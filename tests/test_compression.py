import copy
import json
from pathlib import Path
import tempfile
import unittest

from runaway.compression import (AUDIT_SCHEMA, HEADER, TEXT_SCHEMA, audit_prompt, audit_request, compress,
                                 compression_plan, metrics, reference, validate_audit)
from runaway.profile import make_profile
from runaway.demo import demo_bundle


def profile():
    return make_profile({"claims": [{"id": "paper", "statement": "Try paper prototypes for reversible ideas.",
        "scope": "Fictional product work", "basis": "self_report", "conditions": ["Only reversible ideas"],
        "exceptions": ["Check access before sharing contacts"], "related_claim_ids": [],
        "evidence": [{"source_id": "u", "quote": "I test paper ideas", "relation": "supports"}]}],
        "unknowns": ["Other contexts unknown"]}, {"schema_version": 1, "sources": [
            {"id": "u", "episode_id": "fiction", "role": "user", "text": "Fictional: I test paper ideas. Private supporting text is not sent in the compression projection."}]}, {})


class Model:
    def __init__(self, fail_first=False, overclaim=False, missing_always=False, too_long=False):
        self.calls = []
        self.fail_first, self.overclaim, self.missing_always, self.too_long = fail_first, overclaim, missing_always, too_long
        self.audits = 0

    def __call__(self, prompt, model, schema=None, system=None):
        self.calls.append(model)
        data = json.loads(prompt.split("DATA_JSON:\n", 1)[1])
        if schema == TEXT_SCHEMA:
            result = {"text": "x" * 3000 if self.too_long else "In fictional product work, the narrator reports trying paper prototypes only for reversible ideas, while checking access before sharing contacts. Other contexts are unknown."}
        elif schema == AUDIT_SCHEMA:
            self.audits += 1
            result = {"units": [], "unsupported": []}
            for unit in data["reference"]["units"]:
                missing = unit["kind"] == "exception" and (self.missing_always or self.fail_first and self.audits == 1)
                result["units"].append({"unit_id": unit["id"], "verdict": "missing" if missing else "retained",
                                         "quote": "" if missing else "the narrator reports", "reason": "Fixture verdict, not measured semantics"})
            if self.overclaim:
                result["unsupported"] = [{"quote": "paper prototypes", "reason": "Fixture unsupported addition"}]
        else:
            raise AssertionError("Unexpected schema")
        return json.dumps(result), {"backend": "fixture", "model_requested": model}


class CompressionTests(unittest.TestCase):
    def test_saved_comparison_and_demo_match_their_quote_anchored_audits(self):
        # Recheck the published measurements, without treating saved model verdicts
        # as independently verified semantics or making any provider calls.
        record = json.loads((Path(__file__).resolve().parents[1] /
                            "examples/compression-results.synthetic.json").read_text(encoding="utf-8"))
        for name, case in record["cases"].items():
            with self.subTest(case=name):
                audit = validate_audit(case["audit"], record["reference"], case["prompt"])
                measured = metrics(record["reference"], audit, case["prompt"], 1000, 2216)
                for key, value in measured.items():
                    self.assertEqual(value, case["summary"][key])
                self.assertEqual(measured["accepted"], name == "repaired_candidate")
        bundle, _ = demo_bundle()
        self.assertEqual(bundle["prompt.md"], record["cases"]["repaired_candidate"]["prompt"])

    def test_counter_context_retains_speaker_and_is_not_user_endorsement(self):
        value = profile()
        sources = copy.deepcopy(value["sources"])
        sources["sources"].append({"id": "assistant", "episode_id": "fiction", "role": "assistant",
                                   "text": "You always favor speed. This is not a user assertion."})
        claims = copy.deepcopy(value["claims"])
        claims[0]["evidence"].append({"source_id": "assistant", "quote": "You always favor speed.",
                                      "relation": "contradicts"})
        updated = make_profile({"claims": claims, "unknowns": value["unknowns"]}, sources, {})
        context = [u for u in reference(updated)["units"] if u["kind"] == "counter_context"]
        self.assertEqual(len(context), 1)
        self.assertEqual(json.loads(context[0]["text"]), {"role": "assistant", "relation": "contradicts",
                         "quote": "You always favor speed.", "user_endorsement": False})

    def test_projection_has_every_facet_but_not_full_supporting_messages(self):
        ref = reference(profile())
        self.assertEqual([u["kind"] for u in ref["units"]], ["statement", "scope", "basis", "condition", "exception", "unknown"])
        self.assertNotIn("Private supporting text", json.dumps(ref))
        self.assertIn("self-report", ref["units"][2]["text"])
        self.assertEqual(compression_plan(profile())["model_calls_upper_bound"], 4)

    def test_missing_exception_is_repaired_before_export_and_models_are_explicit(self):
        model = Model(fail_first=True)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            result = compress(profile(), out, "generator", "reviewer", generate=model)
            self.assertEqual(model.calls, ["generator", "reviewer", "generator", "reviewer"])
            self.assertFalse(result["attempts"][0]["accepted"])
            self.assertEqual(result["attempts"][0]["model_judged_complete_claims"], 0)
            self.assertTrue(result["attempts"][1]["accepted"])
            self.assertTrue((out / "portable.json").exists())
            self.assertFalse(result["independent_fidelity_verified"])
            self.assertEqual(compress(profile(), out, "generator", "reviewer", resume=True, generate=model), result)
            self.assertEqual(len(model.calls), 4)

    def test_no_export_when_any_unit_or_added_claim_fails(self):
        for model in (Model(missing_always=True), Model(overclaim=True)):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "run"
                result = compress(profile(), out, "g", "r", generate=model)
                self.assertEqual(result["status"], "no_faithful_candidate_within_budget")
                self.assertFalse((out / "portable.json").exists())
                self.assertTrue((out / "detailed.portable.json").exists())
                self.assertEqual(len(model.calls), 4)

    def test_over_budget_candidate_is_not_audited_or_exported(self):
        model = Model(too_long=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = compress(profile(), Path(tmp) / "run", "g", "r", budget=500, generate=model)
            self.assertEqual(model.calls, ["g", "g"])
            self.assertFalse(result["prompt_available"])
            self.assertFalse(result["attempts"][0]["audit_performed"])

    def test_bad_auditor_quotes_and_incomplete_coverage_are_rejected(self):
        ref = reference(profile())
        model = Model()
        value = json.loads(model(audit_request(ref, "the narrator reports"), "r", schema=AUDIT_SCHEMA)[0])
        validate_audit(value, ref, "the narrator reports")
        bad = copy.deepcopy(value); bad["units"][0]["quote"] = "invented support"
        with self.assertRaisesRegex(ValueError, "does not occur"):
            validate_audit(bad, ref, "the narrator reports")
        bad = copy.deepcopy(value); bad["units"].pop()
        with self.assertRaisesRegex(ValueError, "every reference unit"):
            validate_audit(bad, ref, "the narrator reports")
        bad = copy.deepcopy(value); bad["units"].append(bad["units"][0])
        with self.assertRaisesRegex(ValueError, "every reference unit"):
            validate_audit(bad, ref, "the narrator reports")

    def test_exact_header_counts_in_budget_and_bad_limits_fail_before_calls(self):
        for budget in (1, len(HEADER), 128001, True):
            with self.assertRaises(ValueError):
                compression_plan(profile(), budget)
        with self.assertRaises(ValueError):
            compression_plan(profile(), attempts=4)
        ref = reference(profile())
        body = "the narrator reports"
        audit = json.loads(Model()(audit_request(ref, body), "r", schema=AUDIT_SCHEMA)[0])
        result = metrics(ref, audit, HEADER + body, len(body), 1000)
        self.assertFalse(result["within_budget"])
        self.assertFalse(result["accepted"])

    def test_new_reference_cannot_reuse_an_old_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            compress(profile(), out, "g", "r", generate=Model())
            changed = profile()
            changed = make_profile({"claims": changed["claims"], "unknowns": ["New uncertainty"]}, changed["sources"], {})
            with self.assertRaisesRegex(ValueError, "differs"):
                compress(changed, out, "g", "r", resume=True, generate=Model())

    def test_audit_existing_prompt_is_one_call_and_does_not_create_an_installer(self):
        model = Model()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "audit"
            result = audit_prompt(profile(), "the narrator reports", out, "reviewer", generate=model)
            self.assertEqual(model.calls, ["reviewer"])
            self.assertTrue(result["accepted"])
            self.assertFalse((out / "portable.json").exists())
            self.assertTrue((out / "candidate.private.md").exists())
            self.assertEqual(audit_prompt(profile(), "the narrator reports", out, "reviewer", resume=True, generate=model), result)
            self.assertEqual(len(model.calls), 1)
