"""Finite two-budget control and isolation checks; oracle fixtures do not measure fidelity."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binding_protocol_test', ROOT / 'benchmarks/scope-binding-stress-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.fault, self.at, self.calls = fault, at, []

    def __call__(self, request, folder, slot):
        self.calls.append(slot)
        p, person = e.plan, slot['profile']
        data = p.inputs()
        if slot['kind'] == 'extract':
            source = next(s for s in data['sources'][person]['sources'] if s['role'] == 'user' and '我选“' in s['text'])
            action = re.search('我选“([^”]+)”', source['text']).group(1)
            anchor = dict(source_id=source['id'], quote=source['text'])
            answer = dict(version=p.factory(slot['method']).VERSION, name='协议夹具', tagline='不是模型保真结果。',
                          objects=['夹具对象'], unknowns=['仅验证协议，不是完整提炼。'], nodes=[
                              dict(id='n0', kind='base', target_kind='choice', object_index=0, question='夹具选择',
                                   requires=[], action=action, priority=0, decisions=[anchor], contexts=[anchor], order_split=None)])
            if slot['method'] == p.METHODS[1]:
                answer.update(derived_node_ids=[], source_accounting={
                    s['id']: dict(kind='direct_choice' if s['id'] == source['id'] else 'no_choice',
                                  node_ids=['n0'] if s['id'] == source['id'] else [], reason='仅作协议检查，非真实覆盖分类。')
                    for s in data['sources'][person]['sources'] if s['role'] == 'user'})
            if slot['slot'] == self.at and self.fault == 'product':
                answer['nodes'][0]['object_index'] = 1
            if slot['slot'] == self.at and self.fault == 'wire':
                answer.pop('unknowns')
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in data['queries']['all']}
        else:
            # Reference-aware oracle is intentionally separate from the toy card.
            answer = {q: row['gold'] for row in data['rows'] if row['person'] == person for q in row['query_ids']}
            if slot['slot'] == self.at and self.fault in ('control', 'order'):
                row = next(r for r in data['rows'] if r['person'] == person and r['gold'] != 'U')
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture', 'model_requested': p.MODEL,
            'usage': None if slot['slot'] == self.at and self.fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class ScopeBindingProtocolTests(unittest.TestCase):
    def execute(self, root, fixture, *, simulated=True):
        e.plan.prepare(root / 'inputs')
        return e.run(root / 'inputs', root / 'execution', fixture, lambda _: {}, simulated=simulated)

    def test_schedule_sources_and_budgeted_parent_axes_are_isolated(self):
        p = e.plan
        self.assertEqual(len(p.slots()), 51)
        self.assertEqual([sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')], [1, 2, 16, 32])
        extracts = [s for s in p.slots() if s['kind'] == 'extract']
        self.assertEqual(len({p.parent(s) for s in extracts}), 16)
        for slot in extracts:
            request = p.request(slot)
            body = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], p.inputs()['sources'][slot['profile']])
            self.assertEqual(body['budget_characters'], slot['budget'])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertNotIn('q01_ab', request['prompt'])
            self.assertNotIn('author_evidence', request['prompt'])
            twin = next(s for s in extracts if all(s[k] == slot[k] for k in ('profile', 'method', 'budget')) and s['generation'] != slot['generation'])
            self.assertEqual(p.request(twin), request)
        self.assertFalse(p.values()['proposal.json']['approved'])

    def test_complete51oracle_keeps_four_separate64case_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), result['status'], result['local_cli_child_intents']), (51, 'complete', 0))
        self.assertTrue(result['simulated'])
        for method in e.plan.METHODS:
            for budget in e.plan.BUDGETS:
                cell = result['scores']['methods'][method][str(budget)]
                self.assertEqual(cell['strict']['joint'], dict(planned=64, correct=64, missing=0))
                self.assertEqual([cell['strict'][k]['planned'] for k in ('known', 'unknown')], [40, 24])
                self.assertEqual(cell['old_alias']['joint']['planned'], 16)
                self.assertEqual(cell['late_revision']['joint']['planned'], 16)

    def test_invalid_parent_skips_only_two_reads_without_shrinking_its_budget_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('product', 4)
            result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), len(result['skipped']), result['unused_slots_expire']), (49, 2, 2))
        bad = e.plan.slots()[3]
        for method in e.plan.METHODS:
            for budget in e.plan.BUDGETS:
                joint = result['scores']['methods'][method][str(budget)]['strict']['joint']
                expected = 32 if method == bad['method'] and budget == bad['budget'] else 0
                self.assertEqual(joint, dict(planned=64, correct=64 - expected, missing=expected))

    def test_one_wrong_order_remains_a_loss_among_eight_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('order', 8)
            result = self.execute(Path(tmp), fixture)
        slot = e.plan.slots()[7]
        self.assertEqual(result['scores']['methods'][slot['method']][str(slot['budget'])]['strict']['joint'], dict(planned=64, correct=63, missing=0))

    def test_control_wire_usage_and_missing_guard_stop_without_replenishment(self):
        for fault, at, calls in (('control', 2, 2), ('wire', 7, 7), ('usage', 5, 5)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at)
                result = self.execute(Path(tmp), fixture)
                self.assertEqual((len(fixture.calls), result['status'], result['unused_slots_expire']), (calls, 'stopped', 51 - calls))
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            result = self.execute(Path(tmp), fixture, simulated=False)
            self.assertEqual((len(fixture.calls), result['attempt_reservations']), (0, 0))

    def test_frozen_inputs_and_no_extra_reader_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.execute(root, Fixture())
            request = json.loads((root / 'execution/attempt-08/request.json').read_text())
            body = json.loads(request['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'material', 'queries'})
            self.assertNotIn('source_accounting', body['material'])
            self.assertNotIn('source_accounting', request['prompt'])
            (root / 'inputs/reference.private.json').write_text('[]')
            with self.assertRaises(ValueError):
                e.plan.verify(root / 'inputs')
            self.assertTrue(result['scope_closed'])


if __name__ == '__main__':
    unittest.main()
