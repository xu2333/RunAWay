"""Source-order collateral controller calibration; never model fidelity."""
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


e = load('order_regression_tests', ROOT / 'benchmarks/source-order-regression-v1/engine.py')
fixtures = load('order_regression_fixture', ROOT / 'tests/test_action_revision_stability.py')
fixtures.e = e


class Fixture(fixtures.Fixture):
    def __call__(self, req, folder, slot):
        raw, provenance = super().__call__(req, folder, slot)
        value = json.loads(raw)
        if slot['kind'] == 'extract' and 'version' in value:
            value['version'] = req['schema']['properties']['version']['enum'][0]
            if slot['method']=='source-order-v3':
                for node in value['nodes']:node['order_split']=None
        return json.dumps(value, ensure_ascii=False), provenance


class SourceOrderRegressionTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'; e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_source_isolation_counts_and_no_j16_or_auxiliary_questions(self):
        slots,data=e.plan.slots(),e.plan.inputs()
        self.assertEqual([s['kind'] for s in slots],['none','full']*2+['extract']*8+['read']*16)
        self.assertEqual(set(data['sources']),{'h93','dev'})
        self.assertEqual(sum(len(x['sources']) for x in data['sources'].values()),62)
        self.assertEqual(sum(len(x) for x in data['queries'].values()),112)
        self.assertEqual((len(data['rows']),data['disputed_rows']),(56,[]))
        for slot in slots[4:12]:
            req=e.plan.request(slot);body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
            self.assertEqual(body['sources'],data['sources'][slot['profile']])
            self.assertNotIn('order_probe_a',req['prompt'])
        self.assertIsNone(e.plan.request(slots[12],{('j16','source-order-v3',0):{}}))
        with self.assertRaises(ValueError):e.plan.request(dict(slots[12],generation=9))

    def test28fixtures_keep56cases_and_never_pool_prior_j16(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(alter_dispute=True); root, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (28, 'complete', 0))
            for m in e.plan.METHODS:
                self.assertEqual(r['scores']['per_method_strict'][m]['joint'], {'planned': 56, 'correct': 56, 'missing': 0})
            self.assertEqual(r['scores']['primary_cases_per_method'], 56)
            self.assertEqual(r['scores']['legacy_cases'], 56)
            self.assertFalse(r['scores']['semantic_annotation_independently_accepted'])
            self.assertTrue(all(not d['reference_accepted'] and not d['included_in_primary_or_gate'] for d in r['scores']['disputed_observations_not_scored']))
            self.assertEqual(r['known_usage']['total_tokens'], 0)
            pairs = {}
            prompts = {}
            for rec in r['records']:
                if rec['kind'] == 'read': pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
                elif rec['kind'] == 'extract':
                    prompts[rec['profile'],rec['method'],rec['generation']] = e.plan.read(root/'fixture'/rec['execution_id']/'artifact.json')['prompt']
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in pairs.values()))
            for p in e.plan.PROFILES:
                for g in (0,1):self.assertEqual(prompts[p,'policy-v2',g],prompts[p,'source-order-v3',g])
            self.assertFalse(r['scores']['validates_j16']);self.assertFalse(r['scores']['pooled79case_claim'])

    def test_each_full_control_failure_stops_before_all_extractions(self):
        for at in (2,4):
            with self.subTest(at=at),tempfile.TemporaryDirectory() as temp:
                f=Fixture('control',at);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',28-at))
                self.assertFalse(any(x['kind']=='extract' for x in r['records']))

    def test_invalid_generation_loses_only_own_world_in_own_method(self):
        for at,method,missing in ((5,'policy-v2',40),(6,'policy-v2',16),(7,'source-order-v3',16),(8,'source-order-v3',40)):
            with self.subTest(at=at),tempfile.TemporaryDirectory() as temp:
                f=Fixture('product',at);_,r=self.execute(temp,f)
                self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(26,'completed_with_invalid_products',2))
                self.assertEqual(r['scores']['per_method_strict'][method]['joint'],{'planned':56,'correct':56-missing,'missing':missing})
                self.assertTrue(all(e.plan.parent(s)==e.plan.parent(e.plan.slots()[at-1]) for s in r['skipped']))

    def test_wire_usage_final_failure_and_exclusive_run_prevent_retry(self):
        for fault, at in (('wire', 5), ('usage', 1), ('transport', 28)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = Fixture(fault, at); root, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 28-at))
                with self.assertRaises(FileExistsError): e.run(root, root/'fixture', f, lambda _: {}, simulated=True)

    def test_unapproved_freeze_drift_and_closed22scope_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'proposal'; p = e.plan.prepare(root)
            self.assertFalse(p['approved']); self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root/'static-requests.json')),12)
            self.assertEqual(len(e.plan.read(root/'dynamic-rules.json')['slots']),16)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError): e.plan.prepare(root)
            (root/'sources.json').write_text('{}')
            with self.assertRaises(ValueError): e.plan.verify(root)
        old = load('order_regression_original22', ROOT/'benchmarks/source-order-probe-v1/plan.py')
        self.assertEqual((old.CAP,old.PROFILES,old.METHODS),(22,('j16',),('policy-v2','source-order-v3')))


if __name__ == '__main__': unittest.main()
