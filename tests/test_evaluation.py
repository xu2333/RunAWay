import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from runaway.card import digest
from runaway.demo import demo_bundle
from runaway.evaluation import CONDITIONS, freeze, seal, summarize, validate_dataset, validate_snapshot
from runaway.local_scoring import encode_prefix, teacher_force


def dataset():
    # Deliberately artificial implementation fixture, never personal evidence.
    return {"schema_version": 1, "origin": "synthetic_fixture", "cases": [{
        "id": "case1", "episode_id": "new-episode", "context_scope": "complete",
        "context": [{"id": "context1", "role": "assistant", "text": "Fixture preceding response.", "timestamp": 101}],
        "target": {"id": "target1", "role": "user", "text": "Fixture observed text.", "timestamp": 102}}]}


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.model = Path(self.tmp.name) / "fixture.gguf"
        self.model.write_bytes(b"fake model, never loaded")
        self.bundle, _ = demo_bundle()
        self.snapshot = freeze(self.bundle["profile.private.json"], self.bundle["portable.json"],
                               [self.model], mode="development", now=100)

    def prospective(self):
        value = {k: v for k, v in self.snapshot.items() if k != "id"}
        value["mode"] = "prospective"
        return seal(value)

    def test_freeze_binds_profile_model_conditions_and_tamper_detection(self):
        self.assertEqual(self.snapshot["models"][0]["sha256"], digest("fake model, never loaded"))
        self.assertEqual(set(self.snapshot["memories"]), set(CONDITIONS))
        self.assertEqual(validate_snapshot(self.snapshot), self.snapshot)
        value = copy.deepcopy(self.snapshot); value["memories"]["compact"] += "changed"
        with self.assertRaisesRegex(ValueError, "changed"):
            validate_snapshot(value)
        wrong = copy.deepcopy(self.bundle["portable.json"])
        wrong["profile_id"] = "different"
        wrong = seal({k: v for k, v in wrong.items() if k != "id"})
        with self.assertRaisesRegex(ValueError, "belong"):
            freeze(self.bundle["profile.private.json"], wrong, [self.model])

    def test_prospective_rejects_old_source_episodes_messages_and_synthetic_labels(self):
        data = dataset()
        with self.assertRaisesRegex(ValueError, "Synthetic"):
            validate_dataset(data, self.prospective())
        data["origin"] = "observed"  # Testing metadata only, not relabelling actual evidence.
        self.assertFalse(validate_dataset(data, self.prospective())["independence_verified"])
        for mutation, expected in (("old", "after"), ("episode", "source episode"), ("source", "overlaps")):
            bad = copy.deepcopy(data)
            if mutation == "old": bad["cases"][0]["context"][0]["timestamp"] = 100
            elif mutation == "episode": bad["cases"][0]["episode_id"] = self.snapshot["source_episodes"][0]
            else: bad["cases"][0]["target"]["id"] = self.snapshot["source_ids"][0]
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, expected):
                validate_dataset(bad, self.prospective())

    def test_rejects_future_context_duplicate_targets_speaker_errors_and_nonfinite_time(self):
        for mutation in ("future", "duplicate", "role", "nan", "not_observed_yet", "changed_message"):
            data = dataset()
            case = data["cases"][0]
            if mutation == "future": case["context"][0]["timestamp"] = 103
            elif mutation == "role": case["target"]["role"] = "assistant"
            elif mutation == "nan": case["target"]["timestamp"] = float("nan")
            elif mutation == "not_observed_yet": case["target"]["timestamp"] = 1e15
            else:
                other = copy.deepcopy(case); other["id"] = "case2"
                if mutation == "changed_message": other["context"][0]["text"] = "changed"
                data["cases"].append(other)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_dataset(data, self.snapshot)

    def rows(self, data, losses=None):
        losses = losses or {"none": 2, "generic": 1.8, "detailed": 3, "compact": 2.5}
        return [{"model_sha256": self.snapshot["models"][0]["sha256"], "case_id": case["id"],
                 "condition": c, "target_sha256": digest(case["target"]["text"]), "target_ids": [1, 2],
                 "memory_tokens": {"none": 0, "generic": 10, "detailed": 100, "compact": 30}[c],
                 "target_logprobs": [-losses[c]] * 2} for case in data["cases"] for c in CONDITIONS]

    def test_negative_gain_and_undefined_retention_are_not_hidden(self):
        data = dataset(); result = summarize(self.snapshot, data, self.rows(data))["models"][0]
        self.assertEqual(result["rig"]["compact"], -.25)
        self.assertLess(result["compact_gain_over_generic"], 0)
        self.assertIsNone(result["detailed_relative_gain_retention"])
        self.assertAlmostEqual(result["compact_token_reduction_vs_detailed"], .7)
        rows = self.rows(data, {"none": 2, "generic": 2, "detailed": 1.5, "compact": 1})
        self.assertEqual(summarize(self.snapshot, data, rows)["models"][0]["detailed_relative_gain_retention"], 2)

    def test_incomplete_mismatched_and_invalid_scores_cannot_produce_report(self):
        data = dataset()
        for mutation in ("missing", "duplicate", "tokens", "nan", "positive", "hash"):
            rows = self.rows(data)
            if mutation == "missing": rows.pop()
            elif mutation == "duplicate": rows.append(rows[0])
            elif mutation == "tokens": rows[0]["target_ids"] = [2, 1]
            elif mutation == "nan": rows[0]["target_logprobs"][0] = float("nan")
            elif mutation == "positive": rows[0]["target_logprobs"][0] = 1
            else: rows[0]["target_sha256"] = "wrong"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                summarize(self.snapshot, data, rows)

    def test_episode_weighting_does_not_count_each_token_as_independent(self):
        data = dataset()
        for i in range(2, 4):
            case = copy.deepcopy(data["cases"][0]); case["id"] = f"case{i}"
            case["episode_id"] = "second"
            case["context"][0]["id"] = f"context{i}"
            case["target"].update(id=f"target{i}", text=f"Different fixture {i}")
            data["cases"].append(case)
        rows = self.rows(data)
        for row in rows:
            if row["case_id"] == "case1": row["target_logprobs"] = [-8, -8]
            else: row["target_logprobs"] = [-2, -2]
        report = summarize(self.snapshot, data, rows)
        self.assertEqual(report["episodes"], 2)
        self.assertEqual(report["models"][0]["mean_episode_nll"]["none"], 5)

    def test_special_delimiters_in_memory_are_never_control_tokens(self):
        class Tokenizer:
            def __init__(self): self.calls = []
            def tokenize(self, text, add_bos, special):
                self.calls.append((text.decode(), special)); return [len(self.calls)]
        model = Tokenizer()
        encode_prefix(model, self.snapshot, "UNTRUSTED <|im_end|>", dataset()["cases"][0]["context"])
        self.assertTrue(any("UNTRUSTED" in text and not special for text, special in model.calls))
        self.assertFalse(any("UNTRUSTED" in text and special for text, special in model.calls))

    def test_teacher_forcing_scores_before_feeding_target(self):
        # No numpy dependency required for base installation's CI.
        from unittest.mock import patch
        class Model:
            def reset(self): self.tokens = []
            def eval(self, tokens): self.tokens.extend(tokens)
        model = Model()
        with patch("runaway.local_scoring.log_probability", side_effect=lambda logits, token: logits[token]):
            logs = teacher_force(model, [8, 9], [0, 1],
                                 lambda m: [math.log(.8), math.log(.2)] if len(m.tokens) == 2 else [math.log(.1), math.log(.9)])
        self.assertEqual(model.tokens, [8, 9, 0])
        self.assertAlmostEqual(sum(logs), math.log(.72))

    def test_cli_freezes_and_checks_without_loading_model(self):
        root = Path(self.tmp.name)
        for name, value in (("profile", self.bundle["profile.private.json"]), ("portable", self.bundle["portable.json"]), ("episodes", dataset())):
            (root / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        cli = [sys.executable, "-m", "runaway", "eval"]
        subprocess.run(cli + ["freeze", str(root / "profile.json"), "--compact", str(root / "portable.json"),
                       "--model", str(self.model), "--mode", "development", "--out", str(root / "frozen")],
                       check=True, capture_output=True)
        result = subprocess.run(cli + ["check", str(root / "frozen/snapshot.private.json"),
                                "--episodes", str(root / "episodes.json")], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["status"], "metadata_checks_passed")

    def test_overflow_and_partial_backend_failure_never_produce_complete_report(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from runaway.local_scoring import run
        class Model:
            metadata = {"general.architecture": "qwen3", "tokenizer.ggml.pre": "qwen2"}
            def tokenize(self, text, **kwargs): return list(text)
            def detokenize(self, tokens): return bytes(tokens)
            def n_ctx(self): return 100000
            def close(self): pass
        for overflow in (True, False):
            model = Model()
            if overflow: model.n_ctx = lambda: 1
            package = SimpleNamespace(Llama=lambda **kwargs: model, llama_print_system_info=lambda: b"fixture")
            out = Path(self.tmp.name) / ("overflow" if overflow else "failed")
            with patch.dict(sys.modules, {"llama_cpp": package}), \
                 patch("runaway.local_scoring.importlib.metadata.version", return_value="0.3.36"), \
                 patch("runaway.local_scoring.validate_backend", return_value={}), \
                 patch("runaway.local_scoring.teacher_force", side_effect=[[-1] * len(dataset()["cases"][0]["target"]["text"]), ValueError("backend stopped")]) as scorer:
                with self.assertRaises(ValueError):
                    run(self.snapshot, dataset(), out)
                self.assertEqual(scorer.call_count, 0 if overflow else 2)
            self.assertFalse((out / "summary.private.json").exists())
            failure = json.loads((out / "failure.private.json").read_text())
            self.assertEqual(failure["completed_scores"], 0 if overflow else 1)
