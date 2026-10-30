"""Finite unapproved job preparation; no service or model effects asserted."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/decision-targets-v1'
spec = importlib.util.spec_from_file_location('target_experiment', HERE / 'experiment.py')
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


class TargetExperimentTests(unittest.TestCase):
    def test21slots13static8dynamic_with_controls_first(self):
        slots = exp.slots()
        self.assertEqual(len(slots), 21)
        self.assertEqual([s['kind'] for s in slots[:5]], ['none', 'full', 'full', 'none', 'full'])
        self.assertEqual(sum(s['kind'] == 'extract' for s in slots), 4)
        self.assertEqual(sum(s['kind'] == 'read' for s in slots), 8)
        self.assertEqual(sum(s['kind'] == 'cached_read' for s in slots), 4)

    def test_sources110_queries112_cases96_are_distinct_units(self):
        data = exp.inputs()
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 110)
        self.assertEqual(len(data['queries']['h']), 80)
        self.assertEqual(len(data['queries']['dev']), 32)
        self.assertEqual(len(data['rows']), 96)
        self.assertEqual(sum(r['person'] == 'dev' for r in data['rows']), 16)

    def test_cached_v1_is_previous_measured_revision_not_old_grouped_baseline(self):
        data = exp.inputs()
        self.assertEqual(data['cached_v1']['h68']['characters'], 1118)
        self.assertEqual(data['cached_v1']['h93']['characters'], 1219)

    def test_extractions_only_see_their_own_source_envelope(self):
        data = exp.inputs()
        for slot in exp.slots():
            if slot['kind'] != 'extract':
                continue
            req = exp.request(slot)
            body = json.loads(req['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], data['sources'][slot['profile']])
            self.assertFalse({'queries', 'facts', 'target', 'gold', 'scores', 'cached_v1'} & set(body))

    def test_new_development_rotation_preserves_scenario_and_swaps_options(self):
        for a, b in zip(exp.inputs()['queries']['dev'][::2], exp.inputs()['queries']['dev'][1::2]):
            self.assertEqual(a['scenario'], b['scenario'])
            self.assertEqual(a['id'][:-1] + 'b', b['id'])
            self.assertEqual(list(a['options'].values()), list(reversed(list(b['options'].values()))))

    def test_dynamic_reads_are_exact_repeats_and_only_public_material(self):
        answer = json.loads((HERE / 'examples/partial-answer.synthetic.json').read_text())
        slots = [s for s in exp.slots() if s['kind'] == 'read' and s['profile'] == 'dev' and s['method'] == 'v2']
        a, b = [exp.request(s, {('dev', 'v2'): answer}) for s in slots]
        self.assertEqual(a, b)
        body = json.loads(a['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'material', 'queries'})
        self.assertEqual(len(body['queries']), 32)

    def test_wrong_parent_source_or_missing_artifact_cannot_build_a_read(self):
        slot = next(s for s in exp.slots() if s['kind'] == 'read' and s['profile'] == 'h93')
        self.assertIsNone(exp.request(slot))
        answer = json.loads((HERE / 'examples/partial-answer.synthetic.json').read_text())
        with self.assertRaises(ValueError):
            exp.request(slot, {('h93', 'v2'): answer})

    def test_prepare_has_no_model_authority_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as t, patch.object(exp.grouped, 'codex_generate', side_effect=AssertionError('No model')):
            out = Path(t) / 'proposal'
            proposed = exp.prepare(out)
            self.assertEqual(sum(proposed['categories'].values()), 21)
            self.assertFalse(proposed['approved'])
            self.assertFalse(proposed['new_service_authority'])
            self.assertIsNone(proposed['aggregate_token_cap'])
            self.assertEqual(len(json.loads((out / 'static-requests.json').read_text())), 13)
            self.assertEqual(len(json.loads((out / 'dynamic-rules.json').read_text())['slots']), 8)
            self.assertEqual(json.loads((out / 'manifest.json').read_text())['new_model_calls'], 0)
            with self.assertRaises(FileExistsError):
                exp.prepare(out)


if __name__ == '__main__':
    unittest.main()
