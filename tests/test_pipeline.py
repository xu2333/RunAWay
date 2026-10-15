import copy
import json
from pathlib import Path
import tempfile
import unittest

from runaway.adapters import attach, detach, doctor
from runaway.card import canonical
from runaway.pipeline import build
from runaway.portable import make_expression, validate_expression
from runaway.profile import PROFILE_SCHEMA
from runaway.review import (REVIEW_SCHEMA, LINK_SCHEMA, COMPACT_SCHEMA, COMPACT_REVIEW_SCHEMA,
                            validate_review, validate_compact)
from runaway.sources import chunks, plan


def sources():
    return {"schema_version": 1, "sources": [
        {"id": "u1", "episode_id": "one", "role": "user", "text": "I try paper prototypes for reversible ideas."},
        {"id": "u2", "episode_id": "two", "role": "user", "text": "I check permissions before sharing contacts."}]}


class Model:
    def __init__(self, reject=False, compact_bad=False, fail_at=None):
        self.calls = 0
        self.reject, self.compact_bad, self.fail_at = reject, compact_bad, fail_at

    def __call__(self, prompt, model, schema=None, system=None):
        self.calls += 1
        if self.calls == self.fail_at:
            raise ValueError("Simulated interrupted call")
        if schema == PROFILE_SCHEMA:
            # The extraction prompt has a different delimiter than review prompts.
            source = sources()["sources"][0 if '"id":"u1"' in prompt else 1]
            result = {"claims": [{"id": "same_id_in_every_chunk", "statement": source["text"],
                       "basis": "self_report", "scope": "Product work", "conditions": ["Reversible ideas only"] if source["id"] == "u1" else [],
                       "exceptions": [], "related_claim_ids": [],
                       "evidence": [{"source_id": source["id"], "quote": source["text"], "relation": "supports"}]}],
                      "unknowns": ["Other situations unknown."]}
        else:
            data = json.loads(prompt.split("DATA_JSON:\n", 1)[1])
            if schema == REVIEW_SCHEMA:
                result = {"reviews": [{"claim_id": c["id"], "verdict": "overgeneralized" if self.reject and self.calls == 4 else "supported", "reason": "Fixture review"}
                                      for c in data["candidate"]["claims"]], "omissions": []}
            elif schema == LINK_SCHEMA:
                result = {"links": [{"left_id": data["claims"][0]["id"], "right_id": data["claims"][1]["id"], "reason": "Privacy qualifies speed"}]}
            elif schema == COMPACT_SCHEMA:
                result = {"paragraphs": [{"text": "The person reports trying paper prototypes for reversible product ideas, but checks permissions before sharing contacts.",
                                          "claim_ids": [c["id"] for c in data["claims"]]}], "omitted_claim_ids": []}
            elif schema == COMPACT_REVIEW_SCHEMA:
                result = {"reviews": [{"paragraph_index": i, "verdict": "missing_conditions" if self.compact_bad else "faithful", "reason": "Fixture review"}
                                      for i, _ in enumerate(data["compact"]["paragraphs"])]}
            else:
                raise AssertionError("Unexpected schema")
        return json.dumps(result), {"backend": "fixture"}


class PipelineTests(unittest.TestCase):
    def test_utf8_chunk_coverage_roles_offsets_and_boundaries(self):
        value = sources()
        value["sources"][0]["text"] = "中文🦊\n\n" * 1500
        parts = chunks(value, 2000)
        coverage = set()
        for part in parts:
            self.assertLessEqual(len(canonical(part["sources"]).encode()), 2000)
            for source, segment in zip(part["sources"]["sources"], part["segments"]):
                original = next(s for s in value["sources"] if s["id"] == source["id"])
                self.assertEqual(source["text"], original["text"][segment["start"]:segment["end"]])
                self.assertEqual(source["role"], original["role"])
                if source["id"] == "u1":
                    coverage.update(range(segment["start"], segment["end"]))
        self.assertEqual(coverage, set(range(len(value["sources"][0]["text"]))))
        self.assertEqual(plan(sources())["model_calls_upper_bound"], 7)

    def test_end_to_end_resume_and_portable_native_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            model = Model()
            result = build(sources(), out, "fixture", generate=model)
            self.assertEqual(model.calls, 7)
            self.assertEqual(result["review_supported_claims"], 2)
            self.assertFalse(result["independent_fidelity_verified"])
            self.assertEqual(build(sources(), out, "fixture", resume=True, generate=model), result)
            self.assertEqual(model.calls, 7)
            expression = json.loads((out / "portable.json").read_text())
            validate_expression(expression)
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "AGENTS.md").write_text("Existing instructions.\n")
            attach(expression, project, ["codex", "claude", "opencode"])
            self.assertIn(expression["text"], (project / "AGENTS.md").read_text())
            self.assertNotEqual(doctor(project)["status"], "drift")
            detach(project)
            self.assertEqual((project / "AGENTS.md").read_text(), "Existing instructions.\n")
            self.assertEqual((out / "profile.private.json").stat().st_mode & 0o777, 0o600)

    def test_interrupt_resume_reuses_completed_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            first = Model(fail_at=3)
            with self.assertRaisesRegex(ValueError, "interrupted"):
                build(sources(), out, "fixture", generate=first)
            second = Model()
            build(sources(), out, "fixture", resume=True, generate=second)
            self.assertEqual(second.calls, 5)
            with self.assertRaisesRegex(ValueError, "differs"):
                build(sources(), out, "different-model", resume=True, generate=second)

    def test_review_failure_withholds_whole_dependency_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build(sources(), Path(tmp) / "out", "fixture", generate=Model(reject=True))
            self.assertEqual(result["candidate_claims"], 2)
            self.assertEqual(result["review_supported_claims"], 0)
            self.assertEqual(len(result["withheld_claim_ids"]), 2)

    def test_compact_review_transport_failure_resumes_without_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            with self.assertRaisesRegex(ValueError, "interrupted"):
                build(sources(), out, "fixture", generate=Model(fail_at=7))
            self.assertTrue((out / "detailed.portable.json").exists())
            self.assertFalse((out / "portable.json").exists())
            model = Model()
            build(sources(), out, "fixture", resume=True, generate=model)
            self.assertEqual(model.calls, 1)

    def test_lossy_compaction_falls_back_without_cutting_conditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = build(sources(), out, "fixture", generate=Model(compact_bad=True))
            self.assertIn("did not pass", result["compact_failure"])
            self.assertIn("Condition: Reversible ideas only", (out / "prompt.md").read_text())
            self.assertLessEqual(len((out / "prompt.md").read_text()), 2400)

    def test_impossible_budget_preserves_detailed_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = build(sources(), out, "fixture", budget_chars=10, generate=Model())
            self.assertFalse(result["compact_available"])
            self.assertTrue((out / "detailed.portable.json").exists())
            self.assertFalse((out / "portable.json").exists())

    def test_tampered_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            model = Model()
            build(sources(), out, "fixture", generate=model)
            path = out / "chunk-0000-extract.step.private.json"
            value = json.loads(path.read_text())
            value["answer"] = "changed"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "Checkpoint changed"):
                build(sources(), out, "fixture", resume=True, generate=model)
            self.assertEqual(model.calls, 7)

    def test_assistant_omission_cannot_become_user_evidence(self):
        src = sources()
        src["sources"][0]["role"] = "assistant"
        with self.assertRaisesRegex(ValueError, "user source"):
            validate_review({"reviews": [], "omissions": [{"source_id": "u1", "quote": "paper", "reason": "Missing preference"}]},
                            {"claims": []}, src)

    def test_compact_mapping_cannot_hide_half_a_dependency(self):
        claims = [{"id": "a", "related_claim_ids": ["b"]}, {"id": "b", "related_claim_ids": []}]
        with self.assertRaisesRegex(ValueError, "linked"):
            validate_compact({"paragraphs": [{"text": "Always ship fast", "claim_ids": ["a"]}], "omitted_claim_ids": ["b"]}, claims)

    def test_report_escapes_source_markup_and_portable_detects_edits(self):
        from runaway.pipeline import report_html
        text = report_html({"claims": [], "unknowns": ["<script>bad</script>"]}, [], [], {}, "<img src=x>")
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;img", text)
        value = make_expression("A " * 4000, "p", "detailed")
        validate_expression(value)
        value["text"] += "edited"
        with self.assertRaises(ValueError):
            validate_expression(value)
