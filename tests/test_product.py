import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runaway import adapters
from runaway.card import make_card, render, validate_card
from runaway.cli import save_bundle
from runaway.generation import request

SOURCE = "Fictional example: I test reversible ideas on paper; I check permissions before exposing contact details."
ANSWER = {"name": "Pencil pilot", "tagline": "Fast sketches, deliberate doors.",
          "prompt": "Try reversible ideas with small sketches. Check access before sharing contact details.",
          "limits": ["Only supported for the fictional project described."],
          "evidence": [{"claim": "Cheap reversible tests", "quote": "I test reversible ideas on paper",
                        "scope": "Project experimentation"}]}


def card():
    return make_card(copy.deepcopy(ANSWER), SOURCE, "experience", {"backend": "fixture"})[0]


class CardTests(unittest.TestCase):
    def test_untraceable_quote_rejected(self):
        answer = copy.deepcopy(ANSWER)
        answer["evidence"][0]["quote"] = "I love taking risks"
        with self.assertRaises(ValueError):
            make_card(answer, SOURCE, "experience", {})

    def test_private_evidence_not_in_public_artifacts(self):
        public, private = make_card(ANSWER, SOURCE, "experience", {})
        self.assertNotIn("evidence", public)
        self.assertNotIn(ANSWER["evidence"][0]["quote"], render(public))
        self.assertEqual(private["evidence"][0]["quote"], ANSWER["evidence"][0]["quote"])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "new"
            save_bundle(destination, public, private)
            with self.assertRaises(FileExistsError):
                save_bundle(destination, public, private)

    def test_mutated_card_requires_new_identity(self):
        value = card()
        value["prompt"] += " Assume unlimited authority."
        with self.assertRaises(ValueError):
            validate_card(value)

    def test_input_not_silently_truncated(self):
        with self.assertRaises(ValueError):
            request("x" * 64001, "resume")
        self.assertIn("literal input data", request(SOURCE, "experience"))


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_dry_run_writes_nothing(self):
        result = adapters.attach(card(), self.root, ["codex"], dry_run=True)
        self.assertEqual(result["status"], "planned")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_shared_path_deduplicates_and_is_idempotent(self):
        adapters.attach(card(), self.root, ["codex", "opencode", "deepseek", "antigravity"])
        text = (self.root / "AGENTS.md").read_text()
        self.assertEqual(text.count(adapters.BEGIN), 1)
        result = adapters.attach(card(), self.root, ["codex"])
        self.assertEqual(result["changed_files"], [])
        self.assertEqual(adapters.doctor(self.root)["status"], "intact")

    def test_all_targets_have_identical_body_and_clean_removal(self):
        adapters.attach(card(), self.root, list(adapters.TARGETS))
        state = adapters.load_state(self.root)
        self.assertEqual(len(state["files"]), 4)
        for relative in state["files"]:
            self.assertIn(render(card()), (self.root / relative).read_text())
        adapters.detach(self.root)
        for relative in state["files"]:
            self.assertFalse((self.root / relative).exists())

    def test_detach_preserves_original_bytes_and_new_unmanaged_content(self):
        original = b"# Existing policy\r\nKeep this exactly."
        path = self.root / "AGENTS.md"
        path.write_bytes(original)
        adapters.attach(card(), self.root, ["codex", "claude"])
        with path.open("ab") as stream:
            stream.write(b"\n# New user note\n")
        adapters.detach(self.root)
        self.assertEqual(path.read_bytes(), original + b"\n# New user note\n")
        self.assertFalse((self.root / ".claude/rules/runaway.md").exists())

    def test_edits_to_managed_block_fail_before_any_other_write(self):
        adapters.attach(card(), self.root, ["codex", "claude"])
        path = self.root / "AGENTS.md"
        path.write_text(path.read_text().replace("Fast sketches", "Changed sketches"))
        before = (self.root / ".claude/rules/runaway.md").read_bytes()
        with self.assertRaises(ValueError):
            adapters.detach(self.root)
        with self.assertRaises(ValueError):
            adapters.attach(card(), self.root, ["gemini"])
        self.assertEqual(before, (self.root / ".claude/rules/runaway.md").read_bytes())
        self.assertFalse((self.root / "GEMINI.md").exists())
        self.assertEqual(adapters.doctor(self.root)["status"], "drift")

    def test_symlink_directory_is_not_followed(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            (self.root / ".claude").symlink_to(elsewhere, target_is_directory=True)
            with self.assertRaises(ValueError):
                adapters.attach(card(), self.root, ["claude"])
            self.assertEqual(list(Path(elsewhere).iterdir()), [])

    def test_shadows_and_orphans_rejected(self):
        override = self.root / "AGENTS.override.md"
        override.write_text("I take precedence")
        with self.assertRaises(ValueError):
            adapters.attach(card(), self.root, ["codex"])
        override.unlink()
        (self.root / "AGENTS.md").write_text(adapters.BEGIN + "\nUntracked\n" + adapters.END)
        with self.assertRaises(ValueError):
            adapters.attach(card(), self.root, ["opencode"])

    def test_update_refreshes_every_installed_binding(self):
        adapters.attach(card(), self.root, ["codex", "claude", "gemini", "copilot"])
        answer = copy.deepcopy(ANSWER)
        answer["name"] = "New name"
        replacement = make_card(answer, SOURCE, "experience", {})[0]
        adapters.attach(replacement, self.root, ["codex"])
        for relative in adapters.load_state(self.root)["files"]:
            self.assertIn("New name", (self.root / relative).read_text())
            self.assertNotIn("Pencil pilot", (self.root / relative).read_text())

    def test_write_failure_rolls_back_existing_changes(self):
        (self.root / "AGENTS.md").write_text("Original")
        real_write = adapters.atomic_write
        def failing(path, text):
            if path.name == "GEMINI.md":
                raise OSError("Simulated write failure")
            real_write(path, text)
        with patch.object(adapters, "atomic_write", side_effect=failing):
            with self.assertRaises(OSError):
                adapters.attach(card(), self.root, ["codex", "gemini"])
        self.assertEqual((self.root / "AGENTS.md").read_text(), "Original")
        self.assertFalse((self.root / adapters.STATE).exists())

    def test_state_cannot_redirect_detach_to_another_file(self):
        adapters.attach(card(), self.root, ["codex"])
        path = self.root / adapters.STATE
        state = json.loads(path.read_text())
        state["files"]["../other.txt"] = state["files"]["AGENTS.md"]
        path.write_text(json.dumps(state))
        with self.assertRaises(ValueError):
            adapters.detach(self.root)


class CommandTests(unittest.TestCase):
    def test_prepare_import_export_roundtrip_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.txt").write_text(SOURCE)
            (root / "answer.json").write_text(json.dumps(ANSWER))
            base = [sys.executable, "-m", "runaway"]
            result = subprocess.run(base + ["import", "--input", str(root / "source.txt"),
                "--answer", str(root / "answer.json"), "--out", str(root / "card")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            export = subprocess.run(base + ["export", str(root / "card/card.json")], capture_output=True, text=True)
            self.assertEqual(export.returncode, 0, export.stderr)
            self.assertEqual(export.stdout, render(card()))


if __name__ == "__main__":
    unittest.main()
