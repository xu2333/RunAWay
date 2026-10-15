import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runaway.demo import demo_bundle
from runaway.profile import export_profile, make_profile, validate_profile
from runaway.revision import changes, checkout, revise


def fixture():
    sources = {"schema_version": 1, "sources": [{"id": "u", "episode_id": "fictional", "role": "user",
               "text": "Fictional story: I test reversible ideas on paper, but check access before sharing contacts."}]}
    answer = {"claims": [{"id": "paper", "statement": "Try paper prototypes for reversible ideas.",
               "basis": "self_report", "scope": "Fictional product work", "conditions": [],
               "exceptions": [], "related_claim_ids": [], "evidence": [{"source_id": "u",
               "quote": "I test reversible ideas on paper", "relation": "supports"}]}], "unknowns": ["Other contexts unknown."]}
    return make_profile(answer, sources, {"backend": "fixture"})


class RevisionTests(unittest.TestCase):
    def test_revision_preserves_original_and_records_changed_conditions(self):
        original = fixture()
        before = copy.deepcopy(original)
        draft = copy.deepcopy(checkout(original)["answer.private.json"])
        draft["claims"][0]["exceptions"] = ["Check access before sharing contacts."]
        result, delta = revise(original, draft, original["sources"], "Restore the privacy condition")
        self.assertEqual(original, before)
        self.assertEqual(result["previous_profile_id"], original["id"])
        self.assertEqual(result["status"], "candidate_unvalidated")
        self.assertEqual(result["provenance"]["backend"], "local_editor_revision")
        self.assertEqual(delta["changed_claims"][0]["fields"]["exceptions"]["after"], draft["claims"][0]["exceptions"])
        self.assertIn("Check access", export_profile(result)[0])

    def test_rewrite_or_remove_original_evidence_rejected(self):
        profile = fixture()
        for kind in ("text", "role", "remove"):
            sources = copy.deepcopy(profile["sources"])
            if kind == "remove":
                sources["sources"] = [{"id": "new", "episode_id": "fictional", "role": "user", "text": "New evidence"}]
            else:
                sources["sources"][0][kind] = "context" if kind == "role" else "Changed history"
            with self.assertRaisesRegex(ValueError, "cannot be changed or removed"):
                revise(profile, checkout(profile)["answer.private.json"], sources, "Change")

    def test_new_user_evidence_can_support_a_new_claim(self):
        profile = fixture()
        sources = copy.deepcopy(profile["sources"])
        sources["sources"].append({"id": "u2", "episode_id": "fictional_new", "role": "user", "text": "I check access before sharing."})
        draft = copy.deepcopy(checkout(profile)["answer.private.json"])
        added = copy.deepcopy(draft["claims"][0])
        added.update({"id": "access", "statement": "Check access before sharing.",
                      "evidence": [{"source_id": "u2", "quote": "I check access before sharing.", "relation": "supports"}]})
        draft["claims"].append(added)
        result, delta = revise(profile, draft, sources, "Append explicitly supplied evidence")
        validate_profile(result)
        self.assertEqual(delta["added_source_ids"], ["u2"])
        self.assertEqual(delta["added_claims"][0]["id"], "access")
        sources["sources"][-1]["role"] = "assistant"
        with self.assertRaisesRegex(ValueError, "cannot support"):
            revise(profile, draft, sources, "Assistant is not endorsement")

    def test_invalid_quote_and_dangling_links_rejected(self):
        profile = fixture()
        draft = copy.deepcopy(checkout(profile)["answer.private.json"])
        draft["claims"][0]["evidence"][0]["quote"] = "Not in the original"
        with self.assertRaises(ValueError):
            revise(profile, draft, profile["sources"], "Bad quote")
        draft = copy.deepcopy(checkout(profile)["answer.private.json"])
        draft["claims"][0]["related_claim_ids"] = ["missing"]
        with self.assertRaises(ValueError):
            revise(profile, draft, profile["sources"], "Missing dependency")

    def test_noop_and_empty_reason_rejected(self):
        profile = fixture()
        draft = checkout(profile)["answer.private.json"]
        with self.assertRaisesRegex(ValueError, "No changes"):
            revise(profile, draft, profile["sources"], "Nothing changed")
        with self.assertRaises(ValueError):
            revise(profile, draft, profile["sources"], "")

    def test_removal_and_unknown_only_profile_are_visible(self):
        profile = fixture()
        result, delta = revise(profile, {"claims": [], "unknowns": ["Evidence does not establish this preference."]},
                               profile["sources"], "Withdraw overinterpretation")
        self.assertEqual(delta["removed_claims"][0]["id"], "paper")
        self.assertEqual(changes(profile, result), delta)
        self.assertEqual(result["claims"], [])

    def test_demo_uses_packaged_fiction_without_starting_a_process(self):
        with patch("subprocess.run", side_effect=AssertionError("Demo must be offline")):
            bundle, summary = demo_bundle()
        self.assertFalse(summary["personalized_to_you"])
        self.assertEqual(summary["model_calls"], 0)
        self.assertIn("虚构", bundle["prompt.md"])
        self.assertIn("offline_fictional_demo", bundle["review.private.html"])

    def test_cli_demo_checkout_revise_diff_export_and_no_overwrite(self):
        def cli(*args, success=True):
            result = subprocess.run([sys.executable, "-m", "runaway", *map(str, args)], capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, success, result.stderr)
            return json.loads(result.stdout) if success else result
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo, edit, revised, exported = [root / name for name in ("demo", "edit", "revised", "exported")]
            cli("demo", "--out", demo)
            base = demo / "profile.private.json"
            cli("profile", "checkout", base, "--out", edit)
            draft = edit / "answer.private.json"
            value = json.loads(draft.read_text())
            value["unknowns"].append("Fictional editorial test; not a real user's correction.")
            draft.write_text(json.dumps(value, ensure_ascii=False))
            response = cli("profile", "revise", edit / "base.private.json", "--answer", draft,
                           "--reason", "Offline fictional correction exercise", "--out", revised)
            self.assertEqual(response["model_calls"], 0)
            delta = cli("profile", "diff", base, revised / "profile.private.json")
            self.assertTrue(delta["direct_revision"])
            cli("profile", "export", revised / "profile.private.json", "--out", exported)
            self.assertTrue((exported / "portable.json").is_file())
            self.assertEqual((revised / "profile.private.json").stat().st_mode & 0o777, 0o600)
            cli("demo", "--out", demo, success=False)
            self.assertEqual(json.loads(base.read_text())["id"], response["previous_profile_id"])
