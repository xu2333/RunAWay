"""Project-scoped native instruction bindings. No server or model calls."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import tempfile

from .card import digest
from .portable import render_expression as render

BEGIN = "<!-- runaway:begin -->"
END = "<!-- runaway:end -->"
STATE = ".runaway/install.json"
TARGETS = {
    "codex": ("AGENTS.md", "https://learn.chatgpt.com/docs/agent-configuration/agents-md"),
    "opencode": ("AGENTS.md", "https://docs.opencode.ai/docs/rules/"),
    "deepseek": ("AGENTS.md", "https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/context/agent-instructions"),
    "antigravity": ("AGENTS.md", "https://antigravity.google/docs/rules/"),
    "cursor": ("AGENTS.md", "https://cursor.com/docs/rules"),
    "pi": ("AGENTS.md", "https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/configuration.md"),
    "cline": ("AGENTS.md", "https://docs.cline.bot/customization/cline-rules"),
    "windsurf": ("AGENTS.md", "https://docs.devin.ai/desktop/cascade/memories"),
    "claude": (".claude/rules/runaway.md", "https://code.claude.com/docs/en/memory"),
    "gemini": ("GEMINI.md", "https://geminicli.com/docs/cli/gemini-md/"),
    "copilot": (".github/copilot-instructions.md", "https://docs.github.com/en/copilot/reference/customization-cheat-sheet"),
}
FILES = {v[0] for v in TARGETS.values()}


def safe_path(root, relative):
    path = root / relative
    if path != root and root not in path.parents:
        raise ValueError("Path is outside project")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f"Refusing symlink in managed path: {relative}")
        current = current.parent
    return path


def text_or_none(path):
    return path.read_bytes().decode("utf-8") if path.exists() else None


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".runaway-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(text.encode("utf-8"))
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_state(root):
    text = text_or_none(safe_path(root, STATE))
    if text is None:
        return {"version": 1, "targets": [], "files": {}}
    state = json.loads(text)
    if state.get("version") != 1 or not isinstance(state.get("targets"), list) or not isinstance(state.get("files"), dict):
        raise ValueError("Unknown installation state")
    if not set(state["targets"]) <= set(TARGETS) or not set(state["files"]) <= FILES:
        raise ValueError("Unexpected paths or targets in installation state")
    for record in state["files"].values():
        if not isinstance(record, dict):
            raise ValueError("Invalid installation record")
        segment = record.get("segment", "")
        if not isinstance(segment, str) or not segment or segment.count(BEGIN) != 1 or segment.count(END) != 1:
            raise ValueError("Invalid owned block in installation state")
        if segment.split(BEGIN)[0] not in ("", "\n\n") or not segment.endswith(END + "\n"):
            raise ValueError("Invalid owned block boundaries")
        if digest(segment) != record.get("sha256") or not isinstance(record.get("created"), bool):
            raise ValueError("Installation state checksum mismatch")
    return state


def check_owned(text, record, relative):
    if text is None or text.count(BEGIN) != 1 or text.count(END) != 1 or text.count(record["segment"]) != 1:
        raise ValueError(f"Managed block was edited or removed: {relative}; preserve edits before reattaching")


@contextmanager
def lock(root):
    path = safe_path(root, ".runaway/install.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("Another install is active, or an interrupted install left .runaway/install.lock") from exc
    try:
        os.close(fd)
        yield
    finally:
        path.unlink()


def commit(root, changes):
    """Preflight all paths and contents; roll back ordinary write failures."""
    for relative, (before, after) in changes.items():
        if text_or_none(safe_path(root, relative)) != before:
            raise ValueError(f"File changed during planning: {relative}")
    done = []
    try:
        for relative, (before, after) in changes.items():
            path = safe_path(root, relative)
            if after is None:
                path.unlink()
            else:
                atomic_write(path, after)
            done.append(relative)
    except Exception:
        for relative in reversed(done):
            path = safe_path(root, relative)
            before = changes[relative][0]
            if before is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, before)
        raise


def attach(card, project, targets, dry_run=False):
    root = Path(project).resolve(strict=True)
    if not root.is_dir() or not targets or not set(targets) <= set(TARGETS):
        raise ValueError("Choose an existing project directory and known targets")
    body = render(card)

    def plan():
        state = load_state(root)
        selected = sorted(set(targets) | set(state["targets"]))
        if set(selected) & {"codex", "pi"}:
            override = safe_path(root, "AGENTS.override.md")
            if override.exists() and override.read_text().strip():
                raise ValueError("AGENTS.override.md shadows AGENTS.md in Codex/Pi; resolve that choice explicitly")
        changes, records = {}, {}
        for relative in sorted({TARGETS[t][0] for t in selected}):
            path = safe_path(root, relative)
            before = text_or_none(path)
            old = state["files"].get(relative)
            if old:
                check_owned(before, old, relative)
                separator = old["segment"].split(BEGIN)[0]
                created = old["created"]
            else:
                if before is not None and (BEGIN in before or END in before):
                    raise ValueError(f"Untracked RunAWay block in {relative}; refusing to take ownership")
                separator = "\n\n" if before else ""
                created = before is None
            segment = separator + BEGIN + "\n" + body + END + "\n"
            after = before.replace(old["segment"], segment, 1) if old else (before or "") + segment
            if before != after:
                changes[relative] = (before, after)
            records[relative] = {"segment": segment, "sha256": digest(segment), "created": created}
        next_state = {"version": 1, "card_id": card["id"], "prompt_sha256": digest(body),
                      "targets": selected, "files": records}
        state_text = json.dumps(next_state, ensure_ascii=False, indent=2) + "\n"
        old_state = text_or_none(safe_path(root, STATE))
        if old_state != state_text:
            changes[STATE] = (old_state, state_text)
        result = {"status": "planned" if dry_run else "attached", "project": str(root),
                  "targets": selected, "changed_files": list(changes),
                  "prompt_bytes": len(body.encode()), "runtime_load_verified": False,
                  "note": "Open a new harness session. Shared AGENTS.md applies to any tool that reads it; target names are not isolation boundaries."}
        if not dry_run:
            commit(root, changes)
        return result

    if dry_run:
        return plan()
    with lock(root):
        return plan()


def detach(project, dry_run=False):
    root = Path(project).resolve(strict=True)

    def plan():
        state = load_state(root)
        changes = {}
        for relative, record in state["files"].items():
            before = text_or_none(safe_path(root, relative))
            check_owned(before, record, relative)
            after = before.replace(record["segment"], "", 1)
            if not after and record["created"]:
                after = None
            changes[relative] = (before, after)
        original = text_or_none(safe_path(root, STATE))
        if original is not None:
            changes[STATE] = (original, None)
        if not dry_run:
            commit(root, changes)
        return {"status": "planned" if dry_run else "detached", "changed_files": list(changes),
                "note": "Start fresh sessions to discard old in-context preferences."}

    if dry_run:
        return plan()
    with lock(root):
        return plan()


def doctor(project):
    root = Path(project).resolve(strict=True)
    state = load_state(root)
    files = {}
    for relative, record in state["files"].items():
        try:
            check_owned(text_or_none(safe_path(root, relative)), record, relative)
            files[relative] = "intact"
        except ValueError as exc:
            files[relative] = str(exc)
    notes = ["Static integrity check only; runtime loading and behavioral fidelity are not verified.",
             "Restart sessions after attach/update/detach; existing context may retain old content."]
    if "AGENTS.md" in files and ".claude/rules/runaway.md" in files:
        notes.append("Claude versions/settings that also load AGENTS.md may receive duplicate text. Use one binding for that configuration.")
    if "AGENTS.md" in files and "GEMINI.md" in files:
        notes.append("Tools configured to read both AGENTS.md and GEMINI.md may receive duplicate text.")
    override = safe_path(root, "AGENTS.override.md")
    if "codex" in state["targets"] and override.exists() and override.read_text().strip():
        notes.append("Codex: AGENTS.override.md shadows the installed AGENTS.md block.")
    return {"status": "not_attached" if not files else "intact" if all(v == "intact" for v in files.values()) else "drift",
            "card_id": state.get("card_id"), "files": files, "notes": notes,
            "runtime_load_verified": False,
            "available_cli": {name: bool(shutil.which(command)) for name, command in
                              [("codex", "codex"), ("claude", "claude"), ("opencode", "opencode"),
                               ("deepseek", "dsh"), ("antigravity", "antigravity"), ("gemini", "gemini"), ("pi", "pi")]}}
