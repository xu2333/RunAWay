"""Finite source-only protocol tests. Oracle fixture success is not model fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


e = load('direct768_test_engine', ROOT / 'benchmarks/fresh-direct-768-v1/engine.py')
f = load('direct768_test_fixtures', e.plan.HERE / 'fixtures.py')
loc = load('direct768_test_trace', e.plan.HERE / 'localize.py')


class Fixture:
    def __init__(self, fault=None, at=None): self.fault, self.at, self.calls = fault, at, []

    def __call__(self, request, folder, slot):
        self.calls.append(slot)
        p, person = e.plan, slot['profile']
        if slot['kind'] == 'extract':
            answer = f.graph(person)
            if slot['slot'] == self.at and self.fault == 'product': answer['nodes'][0]['object_index'] = 11
            if slot['slot'] == self.at and self.fault == 'wire': answer.pop('unknowns')
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in p.inputs()['queries'][p.bank(person)]}
        else:
            answer = f.answer_map(person)
            if slot['slot'] == self.at and self.fault in ('control', 'order'):
                row = next(r for r in p.inputs()['rows'] if r['person'] == person and r['gold'] != 'U')
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), dict(backend='offline_fixture', model_requested=p.MODEL,
            usage=None if slot['slot'] == self.at and self.fault == 'usage' else [dict(input_tokens=0, output_tokens=0)])


class FreshDirect768ProtocolTests(unittest.TestCase):
    def execute(self, root, fixture):
        e.plan.prepare(root / 'inputs')
        return e.run(root / 'inputs', root / 'execution', fixture, lambda _: {}, simulated=True)

    def test_schedule_and_source_only_requests_have_exact_own_axes(self):
        p = e.plan
        self.assertEqual(len(p.slots()), 54)
        self.assertEqual([sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')], [2, 4, 16, 32])
        for slot in (s for s in p.slots() if s['kind'] == 'extract'):
            req = p.request(slot); body = json.loads(req['prompt'].split('GRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['budget_characters'], 768)
            self.assertEqual(body['sources'], p.inputs()['sources'][slot['profile']])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            for forbidden in ('q01_ab', 'HAND_STRICT', 'author-evidence', 'calibration.private'):
                self.assertNotIn(forbidden, req['prompt'])
            twin = next(s for s in p.slots() if s['kind'] == 'extract' and
                all(s[k] == slot[k] for k in ('profile', 'method', 'budget')) and s['generation'] != slot['generation'])
            self.assertEqual(req, p.request(twin))

    def test_complete54_oracle_fixture_keeps_all384_cases_and_unknown_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(); result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), result['status'], result['local_cli_child_intents']), (54, 'complete', 0))
        self.assertTrue(result['simulated'])
        self.assertTrue(result['usage_is_fixture_not_billable'])
        self.assertEqual(result['unused_slots_expire'], 0)
        for method in e.plan.METHODS:
            cell = result['scores']['methods'][method]['768']
            self.assertEqual(cell['strict']['joint'], dict(planned=384, correct=384, missing=0))
            self.assertEqual([cell['strict'][k]['planned'] for k in ('known', 'unknown')], [168, 216])
            self.assertEqual([cell['per_person'][p]['joint']['planned'] for p in e.plan.PROFILES], [96] * 4)
        self.assertEqual(result['scores']['paired_transitions']['kept'], 384)
        self.assertFalse(result['scores']['model_results_established_by_fixture'])

    def test_invalid_graph_skips_own_two_reads_but_preserves96_missing_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('product', 7); result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), len(result['skipped']), result['unused_slots_expire']), (52, 2, 2))
        baseline = result['scores']['methods'][e.plan.METHODS[0]]['768']['strict']['joint']
        self.assertEqual(baseline, dict(planned=384, correct=288, missing=96))
        self.assertEqual(result['scores']['paired_transitions']['baseline_missing'], 96)
        self.assertEqual(result['scores']['paired_transitions']['recovered'], 0)

    def test_one_wrong_order_is_not_hidden_by_other_seven_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.execute(Path(tmp), Fixture('order', 8))
        self.assertEqual(result['scores']['methods'][e.plan.METHODS[0]]['768']['strict']['joint']['correct'], 383)
        self.assertEqual(result['scores']['paired_transitions']['recovered'], 1)
        failed = [r for r in result['scores']['all_case_transitions'] if r['transition'] != 'kept']
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][e.plan.METHODS[0]]['loss_kind'], 'intermittent_unknown_from_known')

    def test_control_wire_and_unknown_usage_close_the_scope_without_replenishment(self):
        for fault, at in (('control', 3), ('control', 6), ('wire', 7), ('usage', 10)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at); result = self.execute(Path(tmp), fixture)
                self.assertEqual((len(fixture.calls), result['status']), (at, 'stopped'))
                self.assertEqual(result['unused_slots_expire'], 54 - at)
                self.assertTrue(result['scope_closed'])

    def test_real_mode_requires_new_exact_manifest_grant_and_trusted_verifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); e.plan.prepare(root / 'inputs'); invoke = Mock()
            for approval, verifier in ((None, None), ({'approved': True}, lambda _: True)):
                with self.assertRaises(PermissionError):
                    e.run(root / 'inputs', root / 'out', invoke, lambda _: {'owned_active': True},
                        simulated=False, approval=approval, verify_human_grant=verifier)
            correct = dict(approved=True, scope=e.gate.SCOPE, model=e.plan.MODEL,
                max_new_local_cli_attempts=54, manifest_sha256=e.plan.sha(root / 'inputs/manifest.json'),
                exact_source_ref='a' * 40)
            for key, value in (('max_new_local_cli_attempts', 55), ('manifest_sha256', 'foreign'), ('exact_source_ref', 'main')):
                bad = dict(correct, **{key: value})
                with self.assertRaises(PermissionError): e.gate.verify(root / 'inputs', bad, lambda _: True)
            with self.assertRaises(PermissionError): e.gate.verify(root / 'inputs', correct, lambda _: False)
            invoke.assert_not_called(); self.assertFalse((root / 'out').exists())

    def test_packet_drift_and_foreign_parent_cannot_enter_reader_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); e.plan.prepare(root / 'inputs')
            extracts = [s for s in e.plan.slots() if s['kind'] == 'extract']
            read = e.plan.slots()[7]
            self.assertIsNone(e.plan.request(read, {e.plan.parent(extracts[1]): f.graph(extracts[1]['profile'])}))
            req = e.plan.request(read, {e.plan.parent(extracts[0]): f.graph(extracts[0]['profile'])})
            body = json.loads(req['prompt'].split('READER_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'material', 'queries'})
            self.assertLessEqual(len(body['material']), 768)
            self.assertNotIn('source_accounting', body['material'])
            (root / 'inputs/reference.private.json').write_text('[]')
            with self.assertRaises(ValueError): e.plan.verify(root / 'inputs')

    def test_case_trace_keeps_roles_source_graph_rows_and_each_read_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.execute(root, Fixture())
            value = loc.trace(root / 'inputs', root / 'execution', 'puffin', '0_ordinary', e.plan.METHODS[0], 0)
            self.assertEqual(len(value['complete_source_episodes']), 9)
            self.assertEqual({s['role'] for s in value['complete_source_episodes']}, {'user', 'assistant', 'tool', 'context'})
            self.assertEqual(len(value['compiled_active_rows']['rows']), 18)
            self.assertIsNone(value['binding_failure'])
            self.assertEqual([x['answers'] for x in value['reads']], [[value['reference']] * 2] * 2)
            self.assertTrue(value['omission_or_scope_cause_requires_review'])
            self.assertEqual(value['new_model_calls'], 0)

    def test_invalid_trace_preserves_original_bad_graph_without_fabricating_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.execute(root, Fixture('product', 7))
            value = loc.trace(root / 'inputs', root / 'execution', 'puffin', '0_ordinary', e.plan.METHODS[0], 0)
            self.assertIsNone(value['public_card'])
            self.assertIsNotNone(value['binding_failure'])
            self.assertEqual(value['raw_source_id_graph']['nodes'][0]['object_index'], 11)
            self.assertTrue(all(x['answers'] == [None, None] for x in value['reads']))

    def test_failed_schema_raw_response_and_changed_artifact_remain_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.execute(root, Fixture('wire', 7))
            value = loc.trace(root / 'inputs', root / 'execution', 'puffin', '0_ordinary', e.plan.METHODS[0], 0)
            self.assertIsNone(value['raw_source_id_graph'])
            self.assertIn('nodes', json.loads(value['original_raw_response']))
            self.assertNotIn('unknowns', json.loads(value['original_raw_response']))
            self.assertTrue(all(r['state'] == 'not_called' for r in value['reads']))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.execute(root, Fixture())
            path = root / 'execution/attempt-07/artifact.json'; artifact = json.loads(path.read_text())
            artifact['prompt'] += 'changed'; path.write_text(json.dumps(artifact))
            with self.assertRaises(ValueError):
                loc.trace(root / 'inputs', root / 'execution', 'puffin', '0_ordinary', e.plan.METHODS[0], 0)


if __name__ == '__main__': unittest.main()
