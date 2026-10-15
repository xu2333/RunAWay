"""Artificial transport fixtures only; these are not behavioral evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from runaway.demo import demo_bundle
from runaway.evaluation import freeze, validate_dataset
from runaway.trajectory_import import import_pages


def turn(number, text="Fixture user text.", start=None):
    start = 110 + number * 10 if start is None else start
    return {"id": f"turn{number}", "startedAt": start, "completedAt": start + 5,
            "status": "completed", "error": None, "items": [
                {"type": "userMessage", "id": f"u{number}", "content": [{"type": "text", "text": text}]},
                {"type": "agentMessage", "id": f"a{number}", "phase": "final_answer", "text": f"Fixture final {number}.\n"}]}


def source(turns=None):
    return {"schema_version": 1, "pages": [{"schemaVersion": 1,
            "thread": {"id": "new-thread", "kind": "codex"},
            "page": {"order": "newest_first", "hasMore": True, "nextCursor": "opaque"},
            "turns": list(reversed(turns if turns is not None else [turn(0, "Prior fixture."), turn(1)]))}]}


class TrajectoryImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / "fake.gguf"; path.write_bytes(b"not a model")
        bundle, _ = demo_bundle()
        self.snapshot = freeze(bundle["profile.private.json"], bundle["portable.json"], [path], now=100)

    def test_exact_text_and_conservative_timestamp_mapping(self):
        files, audit = import_pages(self.snapshot, source())
        case = files["episodes.private.json"]["cases"][0]
        self.assertEqual(case["target"]["text"], "Fixture user text.")
        self.assertEqual(case["context"][0]["text"], "Fixture final 0.\n")
        self.assertEqual(case["context"][0]["timestamp"], 115)
        self.assertEqual(case["target"]["timestamp"], 120)
        self.assertEqual(case["context_scope"], "excerpt")
        self.assertFalse(audit["independence_verified"])
        self.assertEqual(audit["selected_cases"], 1)
        self.assertEqual(audit["reason_counts"]["preceding_turn_not_supplied"], 1)

    def test_automation_structured_replies_and_old_targets_do_not_become_gold(self):
        cases = [("<heartbeat>automatic prompt</heartbeat>", "automated_target"),
                 ("<send_user_message_question_reply>[]", "structured_target_requires_review")]
        for text, reason in cases:
            files, report = import_pages(self.snapshot, source([turn(0), turn(1, text)]))
            self.assertNotIn("episodes.private.json", files)
            self.assertEqual(report["reason_counts"][reason], 1)
        _, report = import_pages(self.snapshot, source([turn(0, start=10), turn(1, start=20)]))
        self.assertEqual(report["reason_counts"]["target_not_after_freeze"], 2)

    def test_source_episode_alias_cannot_pass_as_new_thread(self):
        files, report = import_pages(self.snapshot, source(), {"new-thread": self.snapshot["source_episodes"][0]})
        self.assertNotIn("episodes.private.json", files)
        self.assertEqual(report["reason_counts"]["source_episode_overlap"], 2)

    def test_refuses_truncated_attachment_and_ambiguous_steered_targets(self):
        for mutation in ("truncated", "image", "blocks", "steered"):
            value = source(); target = value["pages"][0]["turns"][0]
            user = target["items"][0]
            if mutation == "truncated": user["content"][0]["text"] = "Text …123 tokens truncated…"
            elif mutation == "image": user["content"].append({"type": "image", "url": "fixture"})
            elif mutation == "blocks": user["content"].append({"type": "text", "text": "second"})
            else: target["items"].append(copy.deepcopy(user))
            with self.subTest(mutation=mutation):
                files, report = import_pages(self.snapshot, value)
                self.assertEqual(report["selected_cases"], 0)
                self.assertNotIn("episodes.private.json", files)

    def test_refuses_missing_failed_truncated_or_overlapping_preceding_final(self):
        for mutation in ("in_progress", "truncated", "overlap", "missing_time", "failed"):
            value = source(); previous = value["pages"][0]["turns"][1]
            if mutation == "in_progress": previous["status"] = "inProgress"
            elif mutation == "truncated": previous["items"][1]["truncated"] = True
            elif mutation == "overlap": previous["completedAt"] = 120
            elif mutation == "missing_time": previous["completedAt"] = None
            else: previous["error"] = {"message": "fixture failure"}
            with self.subTest(mutation=mutation):
                self.assertEqual(import_pages(self.snapshot, value)[1]["selected_cases"], 0)

    def test_cannot_bridge_a_gap_between_separately_supplied_pages(self):
        value = source([turn(1)]); value["pages"].extend(source([turn(0)])["pages"])
        report = import_pages(self.snapshot, value)[1]
        self.assertEqual(report["selected_cases"], 0)
        self.assertEqual(report["reason_counts"]["preceding_turn_adjacency_unverified"], 1)

    def test_duplicate_pages_are_idempotent_and_disagreement_fails(self):
        value = source(); value["pages"].append(copy.deepcopy(value["pages"][0]))
        self.assertEqual(import_pages(self.snapshot, value)[1]["selected_cases"], 1)
        value["pages"][1]["turns"][0]["items"][0]["content"][0]["text"] = "Changed"
        with self.assertRaisesRegex(ValueError, "disagree"):
            import_pages(self.snapshot, value)

    def test_exact_duplicate_target_text_is_selected_once_before_scoring(self):
        _, report = import_pages(self.snapshot, source([turn(0), turn(1), turn(2)]))
        self.assertEqual(report["selected_cases"], 1)
        self.assertEqual(report["reason_counts"]["duplicate_target_id_or_text"], 1)

    def test_manual_observed_dataset_cannot_bypass_heartbeat_exclusion(self):
        files, _ = import_pages(self.snapshot, source())
        data = files["episodes.private.json"]
        data["cases"][0]["target"]["text"] = "<heartbeat>not a human message</heartbeat>"
        with self.assertRaisesRegex(ValueError, "Automated"):
            validate_dataset(data, self.snapshot)

    def test_malformed_export_fails_with_a_validation_error(self):
        for field in ("thread", "page", "turns"):
            value = source(); value["pages"][0][field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                import_pages(self.snapshot, value)
