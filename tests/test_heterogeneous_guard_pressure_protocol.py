"""Injected fixture protocol tests, not new model execution or fidelity scores."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pressure_protocol_engine', ROOT / 'benchmarks/heterogeneous-guard-pressure-v1/engine.py')
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
p = e.plan


class Fixture:
    def __init__(self, fault=None, at=None): self.fault, self.at, self.calls = fault, at, []

    def __call__(self, request, folder, slot):
        self.calls.append(slot)
        if slot['kind'] == 'extract':
            answer = p.corpus.graph(slot['profile'])
            if slot['slot'] == self.at and self.fault == 'product': answer['nodes'][0]['object_index'] = 11
            if slot['slot'] == self.at and self.fault == 'wire': answer.pop('unknowns')
        elif slot['kind'] == 'none': answer = {q['id']: 'U' for q in p.inputs()['queries'][p.bank(slot['profile'])]}
        else:
            rows = [r for r in p.inputs()['rows'] if r['person'] == slot['profile']]
            answer = {q: r['gold'] for r in rows for q in r['query_ids']}
            if slot['slot'] == self.at and self.fault in ('control', 'order'):
                row = next(r for r in rows if r['gold'] != 'U'); answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), dict(backend='offline_fixture', model_requested=p.MODEL,
            usage=None if slot['slot'] == self.at and self.fault == 'usage' else [dict(input_tokens=0, output_tokens=0)])


class HeterogeneousGuardPressureProtocolTests(unittest.TestCase):
    def execute(self, root, fixture):
        p.prepare(root / 'inputs')
        return e.run(root / 'inputs', root / 'execution', fixture, lambda _: {}, simulated=True)

    def test16slot_source_only_schedule_has_four_extractions_and_own_budgeted_requests(self):
        self.assertEqual(len(p.slots()), 16)
        self.assertEqual([sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')], [2, 2, 4, 8])
        for slot in (s for s in p.slots() if s['kind'] == 'extract'):
            req = p.request(slot); body = json.loads(req['prompt'].split('GRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], p.inputs()['sources'][slot['profile']])
            self.assertEqual(body['budget_characters'], slot['budget'])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            own = dict(req); own.pop('model')
            self.assertEqual(own, {'system':req['system'], **p.candidate.make_request(body['sources'], slot['budget'])})
            self.assertEqual(slot['generation'], 0)
            self.assertNotIn('query_ids', req['prompt']); self.assertNotIn('HAND', req['prompt'])

    def test_author_capacity_fixture_skips_four_reads_and_keeps_low_budget_missing164(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(); result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), len(result['invalid_products']), len(result['skipped'])), (12, 2, 4))
        self.assertEqual((result['unused_slots_expire'], result['status']), (4, 'completed_with_invalid_products'))
        self.assertEqual(result['scores']['methods']['compact768']['strict']['joint'], dict(planned=164, correct=0, missing=164))
        self.assertEqual(result['scores']['methods']['compact1536']['strict']['joint'], dict(planned=164, correct=164, missing=0))
        self.assertEqual(result['scores']['paired_transitions']['only768missing'], 164)
        self.assertEqual(result['scores']['paired_transitions']['only1536retained'], 0)
        self.assertTrue(result['simulated']); self.assertTrue(result['usage_is_fixture_not_billable'])
        self.assertFalse(result['scores']['model_results_established_by_fixture'])

    def test_invalid_high_budget_parent_skips_only_its_two_reads_not_the_person(self):
        slot = next(s for s in p.slots() if s['kind'] == 'extract' and s['budget'] == 1536)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.execute(Path(tmp), Fixture('product', slot['slot']))
        self.assertEqual(result['scores']['methods']['compact1536']['strict']['joint'], dict(planned=164, correct=82, missing=82))
        self.assertEqual(len(result['skipped']), 6)

    def test_first_full_control_wrong_order_stops_before_any_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('control', 3); result = self.execute(Path(tmp), fixture)
        self.assertEqual(len(fixture.calls), 3); self.assertEqual(result['status'], 'stopped')
        self.assertEqual(result['unused_slots_expire'], 13)
        self.assertFalse(any(s['kind'] == 'extract' for s in fixture.calls))

    def test_malformed_extraction_is_fatal_not_a_skippable_budget_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('wire', 5); result = self.execute(Path(tmp), fixture)
        self.assertEqual(len(fixture.calls), 5); self.assertEqual(result['status'], 'stopped')
        self.assertEqual(result['unused_slots_expire'], 11)

    def test_unknown_usage_closes_scope_without_retry_or_redistribution(self):
        slot = next(s for s in p.slots() if s['kind'] == 'extract' and s['budget'] == 1536)
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('usage', slot['slot']); result = self.execute(Path(tmp), fixture)
        self.assertEqual(fixture.calls[-1]['slot'], slot['slot'])
        self.assertEqual(result['status'], 'stopped'); self.assertTrue(result['scope_closed'])
        self.assertEqual(result['unused_slots_expire'], 16 - len(fixture.calls))

    def test_one_wrong_order_does_not_disappear_behind_other_three_correct_answers(self):
        slot = next(s for s in p.slots() if s['kind'] == 'read' and s['budget'] == 1536)
        with tempfile.TemporaryDirectory() as tmp:
            result = self.execute(Path(tmp), Fixture('order', slot['slot']))
        self.assertEqual(result['scores']['methods']['compact1536']['strict']['joint'], dict(planned=164, correct=163, missing=0))
        cells = result['scores']['all_case_transitions']
        self.assertEqual(sum(not c['compact1536']['correct'] for c in cells), 1)

    def test_real_mode_rejects_old_scope_wrong_cap_or_missing_host_before_invocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p.prepare(root / 'inputs'); invoke = Mock()
            with self.assertRaises(PermissionError):
                e.run(root / 'inputs', root / 'out', invoke, lambda _: {}, simulated=False)
            good = dict(approved=True, scope=e.gate.SCOPE, model=p.MODEL, max_new_local_cli_attempts=16,
                manifest_sha256=p.sha(root / 'inputs/manifest.json'), exact_source_ref='a' * 40)
            for changes in ({'scope':'fresh_direct768_54_v1'}, {'max_new_local_cli_attempts':54},
                            {'max_new_local_cli_attempts':True}, {'exact_source_ref':'main'}, {'manifest_sha256':'old'}):
                with self.subTest(changes=changes), self.assertRaises(PermissionError):
                    e.gate.verify(root / 'inputs', dict(good, **changes), lambda _: True)
            with self.assertRaises(PermissionError): e.gate.verify(root / 'inputs', good, lambda _: False)
            invoke.assert_not_called(); self.assertFalse((root / 'out').exists())

    def test_packet_mutation_and_foreign_generation_do_not_enter_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p.prepare(root / 'inputs')
            extract = next(s for s in p.slots() if s['kind'] == 'extract' and s['budget'] == 1536)
            read = next(s for s in p.slots() if s['kind'] == 'read' and p.parent(s) == p.parent(extract))
            foreign = tuple(list(p.parent(extract))[:-1] + [1 - extract['generation']])
            self.assertIsNone(p.request(read, {foreign:p.corpus.graph(extract['profile'])}))
            req = p.request(read, {p.parent(extract):p.corpus.graph(extract['profile'])})
            body = json.loads(req['prompt'].split('READER_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'material', 'queries'})
            self.assertLessEqual(len(body['material']), 1536)
            self.assertNotIn('source_accounting', body['material'])
            (root / 'inputs/reference.private.json').write_text('[]')
            with self.assertRaises(ValueError): p.verify(root / 'inputs')

    def test_existing_output_directory_cannot_consume_an_injected_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p.prepare(root / 'inputs'); (root / 'out').mkdir(); invoke = Mock()
            with self.assertRaises(FileExistsError):
                e.run(root / 'inputs', root / 'out', invoke, lambda _: {}, simulated=True)
            invoke.assert_not_called()


if __name__ == '__main__': unittest.main()
