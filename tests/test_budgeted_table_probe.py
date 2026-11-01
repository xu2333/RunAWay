"""Budgeted request study configuration, offline fixtures only."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


e = load('budgeted_probe_tests', ROOT / 'benchmarks/budgeted-table-probe-v1/engine.py')
fixtures = load('budgeted_probe_control_fixtures', ROOT / 'tests/test_object_table_probe.py')


class BudgetedProbeTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'
        e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test14slots_unchanged_sources_baseline_and_explicit_budgeted_candidate(self):
        old = load('budgeted_test_original_plan', ROOT / 'benchmarks/object-table-probe-v1/plan.py')
        self.assertEqual(e.plan.inputs(), old.inputs())
        self.assertEqual(len(e.plan.slots()), 14)
        self.assertEqual(e.plan.METHODS, ('scope-v1', 'budgeted-table-v1'))
        for s in e.plan.slots()[2:6]:
            request = e.plan.request(s)
            if s['method'] == 'scope-v1':
                self.assertEqual(request, old.request(s))
            else:
                body = json.loads(request['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n')[1])
                self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
                self.assertEqual(body['budget_characters'], 1536)
                self.assertEqual(body['sources'], e.plan.inputs()['sources']['h93'])
        self.assertEqual(old.METHODS, ('scope-v1', 'table-v1'))

    def test14fixture_calls_reproduce40fixed_cases_and_identical_reads(self):
        with tempfile.TemporaryDirectory() as temp:
            f = fixtures.Fixture()
            root, result = self.execute(temp, f)
            self.assertEqual((f.calls, result['status'], result['unused_slots_expire']), (14, 'complete', 0))
            self.assertEqual(result['known_usage']['total_tokens'], 0)
            for method in e.plan.METHODS:
                self.assertEqual(result['scores']['per_method_strict'][method]['joint'], {'planned': 40, 'correct': 40, 'missing': 0})
            pairs = {}
            for rec in result['records']:
                if rec['kind'] == 'read':
                    pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
            self.assertTrue(all(len(p) == 2 and p[0] == p[1] for p in pairs.values()))
            with self.assertRaises(FileExistsError):
                e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test_control_failure_and_invalid_candidate_preserve_stop_and_missing(self):
        for fault, at, calls, status in [('control', 2, 2, 'stopped'), ('product', 4, 12, 'completed_with_invalid_products')]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = fixtures.Fixture(fault, at)
                _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status']), (calls, status))
                if fault == 'product':
                    self.assertEqual(len(r['skipped']), 2)
                    self.assertEqual(r['scores']['per_method_strict']['budgeted-table-v1']['joint'], {'planned': 40, 'correct': 0, 'missing': 40})

    def test_wire_unknown_usage_and_final_failure_close_without_retry(self):
        for fault, at in [('wire', 4), ('usage', 1), ('transport', 14)]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = fixtures.Fixture(fault, at)
                _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 14-at))

    def test_new_frozen_package_has_correct_builder_and_no_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'proposal'
            p = e.plan.prepare(root)
            self.assertEqual(p['kind'], 'unapproved_budgeted_object_table14_consumed_h93_probe')
            self.assertFalse(p['new_service_authority'])
            self.assertFalse(p['pure_budget_information_effect_isolated'])
            self.assertEqual(e.plan.read(root / 'dynamic-rules.json')['builder'], 'benchmarks/budgeted-table-probe-v1/plan.py:request')
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 6)
            self.assertTrue(e.plan.verify(root))
            (root / 'sources.json').write_text('{}')
            with self.assertRaises(ValueError):
                e.plan.verify(root)


if __name__ == '__main__':
    unittest.main()
