"""Offline new-scope adapter and predeclared disputed-reference mask checks."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('remaining_engine_tests', ROOT / 'benchmarks/remaining-world-frontier-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None, flagged_u=False):
        self.calls, self.fault, self.at, self.flagged_u = 0, fault, at, flagged_u
        self.data = e.plan.inputs()
        old = e.plan.read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']['new_worlds']
        from runaway.constraint_extract import parse_answer
        self.answers = {r['person']: parse_answer(r['raw']) for r in old['records'] if r['group'] == 'extract'}

    def __call__(self, req, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport':
            raise TimeoutError('Offline fixture')
        if slot['kind'] == 'extract':
            answer = copy.deepcopy(self.answers[slot['profile']])
            answer['groups'] = answer['groups'][:1]
            answer['unknowns'] = ['局部离线夹具，不代表模型保真度。']
            answer['tagline'] = '夹具第%d张' % slot['generation']
            if fault == 'product':
                answer['name'] = 'x'*21
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in self.data['queries']['j']}
        else:
            answer = {q: row['gold'] for row in self.data['legacy_rows'] if row['person'] == slot['profile'] for q in row['query_ids']}
            if self.flagged_u:
                row = next(r for r in self.data['disputed_rows'] if r['person'] == slot['profile'])
                answer.update(dict.fromkeys(row['query_ids'], 'U'))
            if fault == 'control':
                row = next(r for r in self.data['rows'] if r['person'] == slot['profile'] and r['gold'] != 'U')
                answer[row['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        prov = {'backend': 'offline_fixture', 'model_requested': e.plan.MODEL,
                'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}
        return json.dumps(answer, ensure_ascii=False), prov


class RemainingWorldTests(unittest.TestCase):
    def execute(self, t, fixture):
        root = Path(t) / 'proposal'
        e.plan.prepare(root)
        with patch.object(e.plan.grouped_support, 'codex_generate', side_effect=AssertionError('No actual service')):
            result = e.run(root, root / 'fixture', fixture, lambda _: {'fixture': True}, simulated=True)
        return root, result

    def test40slots16static24dynamic_and_all12extracts_precede_reading(self):
        slots = e.plan.slots()
        self.assertEqual(len(slots), 40)
        self.assertEqual([s['kind'] for s in slots[:4]], ['none', 'full', 'full', 'full'])
        self.assertTrue(all(s['kind'] == 'extract' for s in slots[4:16]))
        self.assertTrue(all(s['kind'] == 'read' for s in slots[16:]))
        self.assertEqual(len(set(e.plan.cells())), 12)
        self.assertEqual(e.plan.BUDGETS, (1024, 1536))

    def test72legacy_rows_retained69primary3flagged_before_any_new_output(self):
        data = e.plan.inputs()
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 102)
        self.assertEqual(len(data['queries']['j']), 48)
        self.assertEqual((len(data['legacy_rows']), len(data['rows']), len(data['disputed_rows'])), (72, 69, 3))
        self.assertEqual(sum(r['gold'] != 'U' for r in data['rows']), 51)
        self.assertTrue(all(r['case'] == 'w14' for r in data['disputed_rows']))
        self.assertTrue(all(r['case'] != 'w14' for r in data['rows']))
        for pid in e.plan.PROFILES:
            self.assertEqual(sum(r['person'] == pid for r in data['rows']), 23)

    def test_source_only_requests_exclude_masks_refs_cached_outputs_and_when_candidate(self):
        data = e.plan.inputs()
        for slot in e.plan.slots():
            if slot['kind'] != 'extract':
                continue
            req = e.plan.request(slot)
            body = json.loads(req['prompt'].split('\nEXTRACTION_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], data['sources'][slot['profile']])
            self.assertEqual(body['budget_characters'], slot['budget'])
            self.assertFalse({'queries', 'gold', 'reference', 'disputed_rows', 'legacy_rows', 'generation'} & set(body))
            field = req['schema']['properties']['groups']['items']['properties']['rules']['items']['properties']['when']
            self.assertNotIn('minLength', field)
            self.assertNotIn('maxLength', field)
            other = next(s for s in e.plan.slots() if s['kind'] == 'extract' and s['profile'] == slot['profile'] and s['budget'] == slot['budget'] and s['generation'] != slot['generation'])
            self.assertEqual(req, e.plan.request(other))

    def test_preparation_freezes_all_rows_and_is_exclusive_without_authority(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / 'proposal'
            p = e.plan.prepare(root)
            self.assertFalse(p['approved'])
            self.assertFalse(p['new_service_authority'])
            self.assertEqual(len(e.plan.read(root / 'static-requests.json')), 16)
            self.assertTrue(e.plan.verify(root))
            with self.assertRaises(FileExistsError):
                e.plan.prepare(root)
            (root / 'reference.consumed-development.private.json').write_text('{}')
            with self.assertRaises(ValueError):
                e.plan.verify(root)

    def test40simulated_calls_and_unscored_flagged_u_do_not_accept_new_reference(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture(flagged_u=True)
            root, r = self.execute(t, f)
            self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (40, 'complete', 0))
            self.assertEqual(r['known_usage']['total_tokens'], 0)
            self.assertEqual(r['local_cli_child_intents'], 0)
            self.assertTrue(r['simulated'])
            for budget in ('1024', '1536'):
                self.assertEqual(r['scores']['per_budget_strict'][budget]['joint'], {'planned': 69, 'correct': 69, 'missing': 0})
            observed = r['scores']['disputed_observations_not_scored']
            self.assertEqual(len(observed), 6)
            self.assertTrue(all(not v['reference_accepted'] and not v['included_in_primary_or_gate'] for v in observed))
            self.assertTrue(all(v['legacy_author_annotation_unaccepted'] != 'U' for v in observed))
            self.assertTrue(all(v['generations_reads_orders'] == [[['U', 'U'], ['U', 'U']]]*2 for v in observed))
            self.assertFalse(r['new_service_authority'])
            with self.assertRaises(FileExistsError):
                e.run(root, root / 'fixture', f, lambda _: {}, simulated=True)
            self.assertEqual(f.calls, 40)

    def test_failed_primary_full_at2_3_or4_stops_before_extraction5(self):
        for at in (2, 3, 4):
            with self.subTest(at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture('control', at)
                _, r = self.execute(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 40-at))
                self.assertFalse(any(rec['kind'] == 'extract' for rec in r['records']))

    def test_invalid_source_budget_generation_skips_only_own_two_readers(self):
        with tempfile.TemporaryDirectory() as t:
            f = Fixture('product', 5)
            _, r = self.execute(t, f)
            self.assertEqual((f.calls, r['status']), (38, 'completed_with_invalid_products'))
            self.assertEqual(len(r['skipped']), 2)
            self.assertTrue(all(e.plan.parent(s) == ('j16', 1024, 0) for s in r['skipped']))
            self.assertEqual(r['scores']['per_budget_strict']['1024']['joint'], {'planned': 69, 'correct': 46, 'missing': 23})
            self.assertEqual(r['scores']['per_budget_strict']['1536']['joint']['correct'], 69)

    def test_transport_wire_usage_failures_and_final_failure_do_not_retry(self):
        for fault, at in (('transport', 1), ('wire', 1), ('usage', 1), ('transport', 40)):
            with self.subTest(fault=fault, at=at), tempfile.TemporaryDirectory() as t:
                f = Fixture(fault, at)
                _, r = self.execute(t, f)
                self.assertEqual((f.calls, r['status'], r['unused_slots_expire']), (at, 'stopped', 40-at))
                self.assertTrue(r['scope_closed'])

    def test_reader_repeats_are_identical_and_do_not_carry_dispute_flags(self):
        with tempfile.TemporaryDirectory() as t:
            _, r = self.execute(t, Fixture())
            pairs = {}
            for rec in r['records']:
                if rec['kind'] == 'read':
                    pairs.setdefault(e.plan.parent(rec), []).append(rec['request_sha256'])
            self.assertEqual(len(pairs), 12)
            self.assertTrue(all(len(v) == 2 and v[0] == v[1] for v in pairs.values()))

    def test_new_adapter_does_not_mutate_original41scope(self):
        spec = importlib.util.spec_from_file_location('original41_after40_adapter', ROOT / 'benchmarks/compression-stability-v1/engine.py')
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        self.assertEqual(original.plan.CAP, 41)
        self.assertEqual(original.plan.PROFILES, ('h68', 'h93', 'dev'))
        self.assertEqual(original.plan.BUDGETS, (768, 1024))


if __name__ == '__main__':
    unittest.main()
