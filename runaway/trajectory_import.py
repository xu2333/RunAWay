"""Import explicitly supplied Codex read_thread pages; never scan user history.

Only ordinary text targets with a preceding completed final response are selected.
Every selection/exclusion is recorded before scoring. Supplied metadata remains
unverified, including whether an unmarked userMessage was actually human-authored.
"""
import re

from .card import canonical, digest, string
from .evaluation import target_origin_issue, timestamp, validate_dataset, validate_snapshot
from .profile import exact, identifier

TRUNCATED = re.compile(r"\b\d+\s+(?:tokens|characters)\s+truncated\b|\[(?:output )?truncated\]", re.I)


def text_message(item):
    if item.get("truncated") or item.get("isTruncated"):
        return None, "truncated_text"
    if item.get("type") == "userMessage":
        parts = item.get("content")
        if not isinstance(parts, list) or not parts or any(not isinstance(p, dict) or p.get("type") != "text" for p in parts):
            return None, "nontext_or_missing_content"
        # Multiple blocks have no guaranteed original separator. Do not invent one.
        if len(parts) != 1:
            return None, "multiple_text_blocks_require_review"
        text = parts[0].get("text")
        if parts[0].get("truncated") or parts[0].get("isTruncated"):
            return None, "truncated_text"
    else:
        text = item.get("text")
    if not isinstance(text, str) or not text.strip():
        return None, "empty_text"
    if TRUNCATED.search(text):
        return None, "truncated_text"
    string(text, "recorded text", 1000000)
    return text, None


def import_pages(snapshot, source, episode_map=None):
    validate_snapshot(snapshot)
    exact(source, ("schema_version", "pages"), "thread page export")
    if type(source["schema_version"]) is not int or source["schema_version"] != 1:
        raise ValueError("Unsupported thread export schema")
    if not isinstance(source["pages"], list) or not source["pages"]:
        raise ValueError("Provide explicitly selected read_thread pages")
    episode_map = {} if episode_map is None else episode_map
    if not isinstance(episode_map, dict):
        raise ValueError("Episode map must map original thread IDs to source episode IDs")
    for key, value in episode_map.items():
        identifier(key); identifier(value)
    turns, pages, threads, adjacent = {}, [], set(), set()
    for page in source["pages"]:
        if (not isinstance(page, dict) or page.get("schemaVersion") != 1 or
                not isinstance(page.get("thread"), dict) or page["thread"].get("kind") != "codex"):
            raise ValueError("Expected a Codex read_thread schemaVersion 1 page")
        tid = identifier(page["thread"]["id"])
        threads.add(tid)
        if not isinstance(page.get("turns"), list):
            raise ValueError("Missing turns")
        if not isinstance(page.get("page"), dict):
            raise ValueError("Missing provider pagination metadata")
        for turn in page["turns"]:
            if not isinstance(turn, dict) or "id" not in turn or "startedAt" not in turn:
                raise ValueError("Missing turn identity or timestamp")
            if not isinstance(turn.get("items"), list) or any(not isinstance(i, dict) for i in turn["items"]):
                raise ValueError("Turn items must be objects")
        order = page.get("page", {}).get("order")
        if order not in ("newest_first", "oldest_first"):
            raise ValueError("Page must preserve the provider's declared turn order")
        chronological = list(reversed(page["turns"])) if order == "newest_first" else page["turns"]
        for previous, current in zip(chronological, chronological[1:]):
            adjacent.add((tid, previous["id"], current["id"]))
        pages.append({"thread_id": tid, "sha256": digest(canonical(page)),
                      "has_more": page.get("page", {}).get("hasMore"),
                      "next_cursor_present": bool(page.get("page", {}).get("nextCursor"))})
        for turn in page["turns"]:
            identifier(turn["id"])
            timestamp(turn["startedAt"])
            if not isinstance(turn.get("items"), list):
                raise ValueError("Missing turn items")
            # Ignore executable/tool/reasoning payloads, retaining message metadata.
            reduced = {k: turn.get(k) for k in ("id", "startedAt", "completedAt", "status", "error")}
            reduced["items"] = [i for i in turn["items"] if i.get("type") in ("userMessage", "agentMessage")]
            key = tid, turn["id"]
            if key in turns and canonical(turns[key]) != canonical(reduced):
                raise ValueError("Overlapping pages disagree about a turn; refresh or use a consistent export")
            turns[key] = reduced

    audit, candidates = [], []
    for tid in sorted(threads):
        ordered = sorted((t for (thread, _), t in turns.items() if thread == tid), key=lambda t: (t["startedAt"], t["id"]))
        for index, turn in enumerate(ordered):
            users = [i for i in turn["items"] if i["type"] == "userMessage"]
            record = {"thread_id": tid, "episode_id": episode_map.get(tid, tid), "turn_id": turn["id"],
                      "started_at": turn["startedAt"], "user_message_ids": [i.get("id") for i in users],
                      "decision": "excluded", "reason": None}
            audit.append(record)
            if len(users) != 1:
                record["reason"] = "need_one_user_message_with_unambiguous_turn_timestamp"
                continue
            user = users[0]
            identifier(user["id"])
            target_text, issue = text_message(user)
            issue = issue or target_origin_issue(target_text)
            if issue:
                record["reason"] = issue
                continue
            if snapshot["mode"] == "prospective" and turn["startedAt"] <= snapshot["created_at_unix"]:
                record["reason"] = "target_not_after_freeze"
                continue
            if snapshot["mode"] == "prospective" and record["episode_id"] in snapshot["source_episodes"]:
                record["reason"] = "source_episode_overlap"
                continue
            # Use only the immediately previous supplied turn. Never leap over an
            # incomplete/failed/automated turn to fabricate a clean exchange.
            if index == 0:
                record["reason"] = "preceding_turn_not_supplied"
                continue
            previous = ordered[index - 1]
            if (tid, previous["id"], turn["id"]) not in adjacent:
                record["reason"] = "preceding_turn_adjacency_unverified"
                continue
            finals = [i for i in previous["items"] if i["type"] == "agentMessage" and i.get("phase") == "final_answer"]
            if previous["status"] != "completed" or previous["error"] is not None or len(finals) != 1:
                record["reason"] = "preceding_turn_has_no_single_completed_final"
                continue
            completed = previous["completedAt"]
            if completed is None:
                record["reason"] = "preceding_completion_time_missing"
                continue
            timestamp(completed)
            if completed < previous["startedAt"] or completed >= turn["startedAt"]:
                record["reason"] = "overlapping_or_invalid_turn_times"
                continue
            final = finals[0]
            identifier(final["id"])
            context_text, issue = text_message(final)
            if issue:
                record["reason"] = "preceding_" + issue
                continue
            cid = "case-" + digest(canonical([tid, turn["id"], user["id"]]))[:24]
            case = {"id": cid, "episode_id": record["episode_id"], "context_scope": "excerpt",
                    "context": [{"id": final["id"], "role": "assistant", "text": context_text, "timestamp": completed}],
                    "target": {"id": user["id"], "role": "user", "text": target_text, "timestamp": turn["startedAt"]}}
            try:
                validate_dataset({"schema_version": 1, "origin": "observed", "cases": [case]}, snapshot)
            except ValueError as exc:
                record["reason"] = "evaluation_check_failed"
                record["detail"] = str(exc)
                continue
            record.update(case_id=cid, preceding_turn_id=previous["id"], target_sha256=digest(target_text))
            candidates.append((case, record))
    # Deduplicate repeated target text deterministically, never based on scores.
    seen_ids, seen_text, selected = set(), set(), []
    for case, record in sorted(candidates, key=lambda entry: (entry[0]["target"]["timestamp"], entry[0]["id"])):
        target = case["target"]
        if target["id"] in seen_ids or digest(target["text"]) in seen_text:
            record["reason"] = "duplicate_target_id_or_text"
            continue
        seen_ids.add(target["id"]); seen_text.add(digest(target["text"]))
        record.update(decision="included", reason="ordinary_text_with_preceding_final")
        selected.append(case)
    data = {"schema_version": 1, "origin": "observed", "cases": selected}
    if selected:
        validate_dataset(data, snapshot)
    counts = {}
    for record in audit:
        counts[record["reason"]] = counts.get(record["reason"], 0) + 1
    report = {"status": "episodes_imported" if selected else "no_eligible_observed_targets",
              "snapshot_id": snapshot["id"], "source_sha256": digest(canonical(source)),
              "selection_version": 1, "episode_map": episode_map, "pages": pages,
              "supplied_threads": len(threads), "supplied_turns": len(turns), "selected_cases": len(selected),
              "selected_episodes": len({c["episode_id"] for c in selected}), "reason_counts": counts,
              "decisions": audit, "independence_verified": False,
              "limitations": ["Only explicitly supplied pages; not a complete archive or unbiased sampling guarantee.",
                              "userMessage is not authenticated human authorship; known wrappers are excluded, unmarked automation may remain.",
                              "Context is the previous supplied turn's final text only; omitted turns, tools and images are not reconstructed.",
                              "Turn start is used for the single user message; prior turn completion is an upper bound on final-response time.",
                              "Episode aliases must be mapped to the original profile source episodes; metadata is unverified."]}
    files = {"import-audit.private.json": report}
    if selected:
        files["episodes.private.json"] = data
    return files, report
