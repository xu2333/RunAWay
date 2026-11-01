"""Static fixed-view study, inherited parents, controlled diagnostics and faults."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dense_read_tests', ROOT / 'benchmarks/dense-layout-probe-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = e.plan.inputs()

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport':
            raise TimeoutError('Offline fixture')
        answer = {q['id']: 'U' for q in self.data['queries']['h']} if slot['kind'] == 'none' else {
            q: r['gold'] for r in self.data['rows'] for q in r['query_ids']}
        if fault == 'control':
            row = next(r for r in self.data['rows'] if r['gold'] != 'U')
            answer[row['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'offline_fixture', 'model_requested': e.plan.MODEL,
            'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class DenseReadTests(unittest.TestCase):
    def execute(self, temp, f):
        root = Path(temp) / 'proposal'; e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test14static_requests6fixed_views_no_new_extractions_and_expanded_uncapped(self):
        jobs = e.plan.slots()
        self.assertEqual([s['kind'] for s in jobs], ['none', 'full']+['read']*12)
        views = e.plan.views()
        self.assertEqual(len(views), 6)
        for v in views:
            if v['method'] == 'expanded':
                self.assertIsNone(v['memory_ceiling'])
            else:
                self.assertEqual(v['memory_ceiling'], 1536)
                self.assertLessEqual(len(v['prompt']), 1536)
        for g in (0, 1):
            a = e.plan.view({'profile': 'h93', 'method': 'expanded', 'generation': g})
            b = e.plan.view({'profile': 'h93', 'method': 'dense', 'generation': g})
            self.assertEqual(a['semantic_projection_sha256'], b['semantic_projection_sha256'])
        with self.assertRaises(ValueError):
            e.plan.request(jobs[2], {'foreign': 'replacement'})

    def test14fixtures_fixed_hashes_identical_repeats_and40denominators(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(); root, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status']), (14, 'complete'))
            self.assertEqual((r['local_cli_child_intents'], r['known_usage']['total_tokens']), (0, 0))
            self.assertEqual(r['scores']['new_extractions'], 0)
            self.assertFalse(r['scores']['fresh_generation_stability_test'])
            pairs = {}
            for rec in r['records']:
                if rec['kind'] == 'read':
                    self.assertEqual(rec['view_sha256'], e.plan.digest(e.plan.view(rec)))
                    pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in pairs.values()))
            for m in e.plan.METHODS:
                self.assertEqual(r['scores']['methods'][m]['strict_all_parents_and_reads']['joint'], {'planned': 40, 'correct': 40, 'missing': 0})
            with self.assertRaises(FileExistsError):
                e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test_failed_full_before_reads_and_wire_usage_final_failures_do_not_retry(self):
        for fault, at in [('control', 2), ('wire', 3), ('usage', 1), ('transport', 14)]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = Fixture(fault, at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 14-at))
                self.assertFalse(r['skipped'])
                self.assertFalse(r['invalid_products'])

    def test_frozen_views_static_inputs_and_unapproved_authority_detect_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'proposal'; p = e.plan.prepare(root)
            self.assertFalse(p['approved'])
            self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 14)
            self.assertFalse(e.plan.read(root / 'dynamic-rules.json')['slots'])
            self.assertTrue(e.plan.verify(root))
            (root / 'views.public.json').write_text('[]')
            with self.assertRaises(ValueError):
                e.plan.verify(root)

    def test_unread_fixed_views_cannot_credit_missing_or_rewrite_uncapped_control(self):
        rows = e.plan.inputs()['rows']
        r = e.score.summarize(rows, {})
        for m in e.plan.METHODS:
            self.assertEqual(r['methods'][m]['strict_all_parents_and_reads']['joint'], {'planned': 40, 'correct': 0, 'missing': 40})
        self.assertTrue(r['expanded_is_uncapped_diagnostic_not_memory_candidate'])
        self.assertEqual(r['paired_strict']['dense_vs_expanded']['dense_missing'], 40)


if __name__ == '__main__':
    unittest.main()
