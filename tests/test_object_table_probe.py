"""Single-source configuration and failure fixtures, never model fidelity."""
import copy
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


e = load('table_probe_tests', ROOT / 'benchmarks/object-table-probe-v1/engine.py')


class Fixture:
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = e.plan.inputs()

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport':
            raise TimeoutError('Offline fixture')
        if slot['kind'] == 'extract':
            source = next(s for s in self.data['sources']['h93']['sources'] if s['role'] == 'user')
            anchor = {'source_id': source['id'], 'quote': source['text'][:80]}
            row = {'object_index': 0, 'question': '夹具选择', 'requires': [], 'action': '夹具做法', 'priority': 0,
                   'decisions': [anchor], 'contexts': [anchor], 'supersedes': []}
            answer = {'version': e.plan.candidate.VERSION, 'objects': ['离线夹具'], 'rows': [row],
                      'name': '控制器夹具', 'tagline': '不是模型提炼。', 'unknowns': ['不评估实际保真度。']}
            if slot['method'] == 'scope-v1':
                ledger = e.plan.candidate.expand(answer)
                answer = e.plan.candidate.base.project(ledger, self.data['sources']['h93'])[0]
                if fault == 'product':
                    answer['groups'][0]['rules'][0]['decisions'][0]['quote'] = 'nonexistent quote'
            elif fault == 'product':
                answer['rows'][0]['object_index'] = 1
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in self.data['queries']['h']}
        else:
            answer = {q: row['gold'] for row in self.data['rows'] for q in row['query_ids']}
            if fault == 'control':
                known = next(r for r in self.data['rows'] if r['gold'] != 'U')
                answer[known['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'offline_fixture', 'model_requested': e.plan.MODEL,
            'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class TableProbeTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'
        e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_fixed14_schedule48messages80forms_and_source_only_requests(self):
        slots, data = e.plan.slots(), e.plan.inputs()
        self.assertEqual([s['kind'] for s in slots], ['none', 'full']+['extract']*4+['read']*8)
        self.assertEqual((len(data['sources']['h93']['sources']), len(data['queries']['h']), len(data['rows'])), (48, 80, 40))
        self.assertEqual(sum(r['gold'] != 'U' for r in data['rows']), 24)
        for s in slots[2:6]:
            req = e.plan.request(s)
            marker = '\nSOURCE_LEDGER_INPUT_JSON:\n' if s['method'] == 'table-v1' else '\nEXTRACTION_INPUT_JSON:\n'
            body = json.loads(req['prompt'].split(marker)[1])
            self.assertEqual(body['sources'], data['sources']['h93'])
            self.assertEqual(set(body), {'sources'} if s['method'] == 'table-v1' else {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})

    def test14simulated_calls_both40denominators_and_identical_repeats(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture()
            root, r = self.execute(t, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (14, 'complete', 0))
            self.assertEqual(set(r['control_gates']), {'h93'})
            self.assertEqual(r['scores']['primary_cases_per_method'], 40)
            for m in e.plan.METHODS:
                self.assertEqual(r['scores']['per_method_strict'][m]['joint'], {'planned': 40, 'correct': 40, 'missing': 0})
            pairs = {}
            for x in r['records']:
                if x['kind'] == 'read':
                    pairs.setdefault(e.plan.parent(x), []).append(x['request_sha256'])
            self.assertTrue(all(len(x) == 2 and x[0] == x[1] for x in pairs.values()))
            self.assertEqual((r['local_cli_child_intents'], r['known_usage']['total_tokens']), (0, 0))
            with self.assertRaises(FileExistsError):
                e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test_full_control_failure_at2_stops_before_extract3(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture('control', 2)
            _, r = self.execute(t, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (2, 'stopped', 12))

    def test_invalid_products_skip_only_own_two_reads_and_keep40missing(self):
        for at in (3, 4):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture('product', at)
                _, r = self.execute(t, f)
                slot = e.plan.slots()[at-1]
                self.assertEqual((f.calls, r['status']), (12, 'completed_with_invalid_products'))
                self.assertEqual(len(r['skipped']), 2)
                self.assertTrue(all(e.plan.parent(x) == e.plan.parent(slot) for x in r['skipped']))
                self.assertEqual(r['scores']['per_method_strict'][slot['method']]['joint']['missing'], 40)

    def test_wire_transport_usage_and_final_failure_are_fatal_without_retry(self):
        for fault, at in (('wire', 4), ('transport', 1), ('usage', 1), ('transport', 14)):
            with self.subTest(fault=fault, at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture(fault, at)
                _, r = self.execute(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 14-at))

    def test_preparation_is_exclusive_unapproved_and_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'proposal'
            p = e.plan.prepare(root)
            self.assertFalse(p['approved'])
            self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 6)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError):
                e.plan.prepare(root)
            (root / 'sources.json').write_text('{}')
            with self.assertRaises(ValueError):
                e.plan.verify(root)

    def test_unbound_wrong_generation_or_foreign_method_is_not_a_parent(self):
        s = e.plan.slots()[6]
        self.assertIsNone(e.plan.request(s, {('h93', s['method'], 1): {}}))
        with self.assertRaises(ValueError):
            e.plan.request(dict(s, method='foreign'))
        original = load('original42_after_table_probe', ROOT / 'benchmarks/owned-conditions-v1/engine.py')
        self.assertEqual((original.plan.CAP, original.plan.PROFILES), (42, ('h93', 'j16', 'dev')))


if __name__ == '__main__':
    unittest.main()
