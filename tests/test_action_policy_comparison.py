"""New guidance wiring/source isolation and finite comparison fixtures only."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


e = load('action_policy_comparison_tests', ROOT / 'benchmarks/action-policy-comparison-v1/engine.py')
fixtures = load('action_policy_isolated_fixtures', ROOT / 'tests/test_action_revision_stability.py')
fixtures.e = e


class Fixture(fixtures.Fixture):
    def __call__(self, req, folder, slot):
        raw, provenance = super().__call__(req, folder, slot)
        value = json.loads(raw)
        if slot['kind'] == 'extract' and 'version' in value:
            value['version'] = req['schema']['properties']['version']['enum'][0]
        return json.dumps(value, ensure_ascii=False), provenance


class ActionPolicyComparisonTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'; e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_source_only_guidance_changes_neither_body_nor_graph_shape(self):
        slots, data = e.plan.slots(), e.plan.inputs()
        self.assertEqual([s['kind'] for s in slots], ['none', 'full']+['extract']*4+['read']*8)
        self.assertEqual((len(data['sources']['j16']['sources']), len(data['queries']['j']), len(data['rows'])), (34, 48, 23))
        requests = {s['method']: e.plan.request(s) for s in slots[2:4]}
        bodies = {m: json.loads(r['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1]) for m, r in requests.items()}
        self.assertEqual(bodies['graph-v1'], bodies['policy-v2'])
        self.assertEqual(set(bodies['policy-v2']), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(bodies['policy-v2']['sources'], data['sources']['j16'])
        schema = requests['policy-v2']['schema']; schema['properties']['version']['enum'] = [e.plan.baseline.VERSION]
        self.assertEqual(schema, requests['graph-v1']['schema'])
        self.assertTrue(requests['policy-v2']['prompt'].endswith(requests['graph-v1']['prompt']))

    def test14fixtures_bind_same_compiler_and_keep23cases_w14unscored(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(alter_dispute=True); root, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (14, 'complete', 0))
            for m in e.plan.METHODS:
                self.assertEqual(r['scores']['per_method_strict'][m]['joint'], {'planned': 23, 'correct': 23, 'missing': 0})
            self.assertEqual(r['scores']['primary_cases_per_method'], 23)
            self.assertEqual(r['scores']['legacy_cases'], 24)
            self.assertFalse(r['scores']['new_semantic_guidance_verified'])
            self.assertTrue(all(not d['reference_accepted'] and not d['included_in_primary_or_gate'] for d in r['scores']['disputed_observations_not_scored']))
            self.assertEqual(r['known_usage']['total_tokens'], 0)
            pairs = {}
            prompts = {}
            for rec in r['records']:
                if rec['kind'] == 'read': pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
                elif rec['kind'] == 'extract':
                    prompts[rec['method'],rec['generation']] = e.plan.read(root/'fixture'/rec['execution_id']/'artifact.json')['prompt']
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in pairs.values()))
            for g in (0, 1): self.assertEqual(prompts['graph-v1',g], prompts['policy-v2',g])

    def test_full_control_failure_stops_before_extraction(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture('control', 2); _, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (2, 'stopped', 12))

    def test_invalid_generation_retains23missing_in_own_method_only(self):
        for at, method in ((3, 'graph-v1'), (4, 'policy-v2')):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as temp:
                f = Fixture('product', at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (12, 'completed_with_invalid_products', 2))
                self.assertEqual(r['scores']['per_method_strict'][method]['joint'], {'planned': 23, 'correct': 0, 'missing': 23})
                self.assertTrue(all(e.plan.parent(s)==e.plan.parent(e.plan.slots()[at-1]) for s in r['skipped']))

    def test_wire_usage_final_failure_and_exclusive_run_prevent_retry(self):
        for fault, at in (('wire', 4), ('usage', 1), ('transport', 14)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = Fixture(fault, at); root, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 14-at))
                with self.assertRaises(FileExistsError): e.run(root, root/'fixture', f, lambda _: {}, simulated=True)

    def test_unapproved_freeze_drift_and_old24scope_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'proposal'; p = e.plan.prepare(root)
            self.assertFalse(p['approved']); self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root/'static-requests.json')),6)
            self.assertEqual(len(e.plan.read(root/'dynamic-rules.json')['slots']),8)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError): e.plan.prepare(root)
            (root/'sources.json').write_text('{}')
            with self.assertRaises(ValueError): e.plan.verify(root)
        old = load('action_policy_original24', ROOT/'benchmarks/action-revision-stability-v1/plan.py')
        self.assertEqual((old.CAP,old.PROFILES,old.METHODS),(24,('h93','j16','dev'),('graph-v1',)))


if __name__ == '__main__': unittest.main()
