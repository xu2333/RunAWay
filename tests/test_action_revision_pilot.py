"""Five-slot controller fixtures; oracle outputs are not model-fidelity evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('graph_pilot_tests', ROOT / 'benchmarks/action-revision-pilot-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = e.plan.inputs()

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if self.at == slot['slot'] else None
        if fault == 'transport': raise TimeoutError('Offline fixture')
        if slot['kind'] == 'extract':
            source = next(s for s in self.data['sources']['h93']['sources'] if s['role'] == 'user')
            anchor = {'source_id': source['id'], 'quote': source['text'][:80]}
            answer = {'version': e.plan.candidate.VERSION, 'name': '离线夹具', 'tagline': '不是实际提炼。',
                'objects': ['夹具范围'], 'unknowns': ['未覆盖时未知。'], 'nodes': [
                    {'id': 'base', 'kind': 'base', 'target_kind': 'choice', 'object_index': 0,
                     'question': '夹具选择', 'requires': [], 'action': '夹具做法', 'priority': 0,
                     'decisions': [anchor], 'contexts': [anchor]}]}
            if fault == 'product': answer['nodes'][0]['object_index'] = 1
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in self.data['queries']['h']}
        else:
            answer = {q: r['gold'] for r in self.data['rows'] for q in r['query_ids']}
            if fault == 'control':
                row = next(r for r in self.data['rows'] if r['gold'] != 'U')
                answer[row['query_ids'][0]] = 'U'
        if fault == 'wire': answer = {}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'offline_fixture',
            'model_requested': e.plan.MODEL, 'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class GraphPilotTests(unittest.TestCase):
    def execute(self, temp, fixture):
        root = Path(temp) / 'proposal'; e.plan.prepare(root)
        return root, e.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_five_slots_source_only_and_original_scope_unmutated(self):
        slots, data = e.plan.slots(), e.plan.inputs()
        self.assertEqual([s['kind'] for s in slots], ['none', 'full', 'extract', 'read', 'read'])
        self.assertEqual((len(data['sources']['h93']['sources']), len(data['queries']['h']), len(data['rows'])), (48, 80, 40))
        body = json.loads(e.plan.request(slots[2])['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(body['sources'], data['sources']['h93'])
        self.assertEqual(body['budget_characters'], 1536)
        oldspec = importlib.util.spec_from_file_location('graph_test_old_plan', ROOT / 'benchmarks/object-table-probe-v1/plan.py')
        old = importlib.util.module_from_spec(oldspec); oldspec.loader.exec_module(old)
        self.assertEqual((old.CAP, old.METHODS), (14, ('scope-v1', 'table-v1')))
        self.assertIsNone(e.plan.request(slots[3], {('h93', 'graph-v1', 1): {}}))

    def test_complete_five_fixture_calls_four_answers_per_case_not_stability(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture(); root, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (5, 'complete', 0))
            self.assertEqual(r['scores']['strict_both_reads']['joint'], {'planned': 40, 'correct': 40, 'missing': 0})
            self.assertEqual(r['scores']['answers_per_case'], 4)
            self.assertFalse(r['scores']['fresh_generation_stability_test'])
            self.assertEqual((r['local_cli_child_intents'], r['known_usage']['total_tokens']), (0, 0))
            reads = [x['request_sha256'] for x in r['records'] if x['kind'] == 'read']
            self.assertEqual(reads[0], reads[1])
            with self.assertRaises(FileExistsError): e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)

    def test_invalid_product_skips_only_its_two_reads_and_keeps40missing(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Fixture('product', 3); _, r = self.execute(temp, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (3, 'completed_with_invalid_products', 2))
            self.assertEqual(len(r['skipped']), 2)
            self.assertEqual(r['scores']['strict_both_reads']['joint'], {'planned': 40, 'correct': 0, 'missing': 40})

    def test_control_wire_usage_and_last_transport_failure_close_without_retry(self):
        for fault, at in [('control', 2), ('wire', 3), ('usage', 1), ('transport', 5)]:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                f = Fixture(fault, at); _, r = self.execute(temp, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 5-at))

    def test_exclusive_unapproved_freeze_and_input_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'proposal'; p = e.plan.prepare(root)
            self.assertFalse(p['new_service_authority'])
            self.assertFalse(p['approved'])
            self.assertEqual(p['max_new_local_cli_attempts'], 5)
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 3)
            self.assertEqual(len(e.plan.read(root / 'dynamic-rules.json')['slots']), 2)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError): e.plan.prepare(root)
            (root / 'sources.json').write_text('{}')
            with self.assertRaises(ValueError): e.plan.verify(root)


if __name__ == '__main__': unittest.main()
