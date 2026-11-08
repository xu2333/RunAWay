"""Fresh-person two-bank control and isolation checks; oracle fixtures do not measure fidelity."""
import importlib.util
import json
import re
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fresh_alias_protocol_test', ROOT / 'benchmarks/fresh-alias-generalization-v1/engine.py')
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
            if slot['method'] in p.METHODS:
                answer.update(derived_node_ids=[], source_accounting={
                    s['id']: dict(kind='direct_choice' if s['id'] == source['id'] else 'no_choice',
                                  node_ids=['n0'] if s['id'] == source['id'] else [], reason='仅作协议检查，非真实覆盖分类。')
                    for s in data['sources'][person]['sources'] if s['role'] == 'user'})
            if slot['method'] == p.METHODS[1]:
                answer['object_aliases'] = []
                for entry in answer['source_accounting'].values(): entry['alias_ids'] = []
            if slot['slot'] == self.at and self.fault == 'product':
                answer['nodes'][0]['object_index'] = 1
            if slot['slot'] == self.at and self.fault == 'wire':
                answer.pop('unknowns')
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in data['queries'][p.bank(person)]}
            if self.fault == 'none_probe' and p.bank(person) == 'qualified':
                row = next(r for r in data['rows'] if r['person'] == 'tansy' and r['gold'] != 'U')
                for q in row['query_ids']: answer[q] = row['gold']
        else:
            # Reference-aware oracle is intentionally separate from the toy card.
            answer = {q: row['gold'] for row in data['rows'] if row['person'] == person for q in row['query_ids']}
            if slot['slot'] == self.at and self.fault in ('control', 'order'):
                row = next(r for r in data['rows'] if r['person'] == person and r['gold'] != 'U')
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture', 'model_requested': p.MODEL,
            'usage': None if slot['slot'] == self.at and self.fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class FreshAliasProtocolTests(unittest.TestCase):
    def execute(self, root, fixture, *, simulated=True):
        e.plan.prepare(root / 'inputs')
        return e.run(root / 'inputs', root / 'execution', fixture, lambda _: {}, simulated=simulated)

    def test_schedule_sources_and_budgeted_parent_axes_are_isolated(self):
        p = e.plan
        self.assertEqual(len(p.slots()), 54)
        self.assertEqual([sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')], [2, 4, 16, 32])
        extracts = [s for s in p.slots() if s['kind'] == 'extract']
        self.assertEqual(len({p.parent(s) for s in extracts}), 16)
        self.assertEqual([p.bank(s['profile']) for s in p.slots()[:6]],
                         ['chain', 'qualified', 'chain', 'chain', 'qualified', 'qualified'])
        for slot in p.slots()[:6]:
            req = p.request(slot)
            body = json.loads(req['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
            self.assertEqual(body['queries'], p.inputs()['queries'][p.bank(slot['profile'])])
            self.assertEqual(len(body['queries']), 88)
            expected = '' if slot['kind'] == 'none' else p.transcript(p.inputs()['sources'][slot['profile']])
            self.assertEqual(body['material'], expected)
        for slot in extracts:
            request = p.request(slot)
            body = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], p.inputs()['sources'][slot['profile']])
            self.assertEqual(body['budget_characters'], slot['budget'])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertNotIn('v01_ab', request['prompt'])
            self.assertNotIn('author_evidence', request['prompt'])
            twin = next(s for s in extracts if all(s[k] == slot[k] for k in ('profile', 'method', 'budget')) and s['generation'] != slot['generation'])
            self.assertEqual(p.request(twin), request)
        self.assertFalse(p.values()['proposal.json']['approved'])

    def test_complete54oracle_keeps_families_people_and_full176case_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('none_probe')
            result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), result['status'], result['local_cli_child_intents']), (54, 'complete', 0))
        self.assertTrue(result['simulated'])
        self.assertEqual({person: g['none']['personal_known']['correct'] for person, g in result['control_gates'].items()},
                         dict(otter=0, marten=0, tansy=1, sedge=0))
        for method in e.plan.METHODS:
            for budget in e.plan.BUDGETS:
                cell = result['scores']['methods'][method][str(budget)]
                self.assertEqual(cell['strict']['joint'], dict(planned=176, correct=176, missing=0))
                self.assertEqual([cell['strict'][k]['planned'] for k in ('known', 'unknown')], [112, 64])
                self.assertEqual(cell['positive_names']['joint']['planned'], 48)
                self.assertEqual(cell['other_cases']['joint']['planned'], 128)
                for family in cell['per_family'].values():
                    self.assertEqual([family[k]['planned'] for k in ('joint', 'known', 'unknown')], [88, 56, 32])
                for own in cell['per_person'].values():
                    self.assertEqual([own[k]['planned'] for k in ('joint', 'known', 'unknown')], [44, 28, 16])
                self.assertTrue(all(x['joint']['planned'] == 16 for x in cell['cohorts'].values()))

    def test_invalid_parent_skips_only_two_reads_without_shrinking_its_budget_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('product', 7)
            result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), len(result['skipped']), result['unused_slots_expire']), (52, 2, 2))
        bad = e.plan.slots()[6]
        for method in e.plan.METHODS:
            for budget in e.plan.BUDGETS:
                joint = result['scores']['methods'][method][str(budget)]['strict']['joint']
                expected = 44 if method == bad['method'] and budget == bad['budget'] else 0
                self.assertEqual(joint, dict(planned=176, correct=176 - expected, missing=expected))
        cell = result['scores']['methods'][bad['method']]['1536']
        self.assertEqual(cell['per_person']['otter']['joint'], dict(planned=44, correct=0, missing=44))
        self.assertEqual(cell['positive_names']['joint'], dict(planned=48, correct=36, missing=12))
        self.assertEqual(cell['other_cases']['joint'], dict(planned=128, correct=96, missing=32))

    def test_one_wrong_order_remains_a_loss_among_eight_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('order', 11)
            result = self.execute(Path(tmp), fixture)
        slot = e.plan.slots()[10]
        self.assertEqual(result['scores']['methods'][slot['method']][str(slot['budget'])]['strict']['joint'], dict(planned=176, correct=175, missing=0))

    def test_control_wire_usage_and_missing_guard_stop_without_replenishment(self):
        for fault, at, calls in (('control', 3, 3), ('control', 5, 5), ('wire', 10, 10), ('usage', 8, 8)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at)
                result = self.execute(Path(tmp), fixture)
                self.assertEqual((len(fixture.calls), result['status'], result['unused_slots_expire']), (calls, 'stopped', 54 - calls))
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            result = self.execute(Path(tmp), fixture, simulated=False)
            self.assertEqual((len(fixture.calls), result['attempt_reservations']), (0, 0))

    def test_frozen_inputs_and_no_extra_reader_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = dict(os.environ);env.pop('PYTHONPATH', None)
            cli = subprocess.run([sys.executable, '-B', str(e.plan.HERE / 'plan.py'), '--out', str(root / 'standalone')], cwd=tmp, env=env, capture_output=True, text=True)
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertFalse(json.loads(cli.stdout)['approved'])
            self.assertTrue(e.plan.verify(root / 'standalone'))
            result = self.execute(root, Fixture())
            request = json.loads((root / 'execution/attempt-11/request.json').read_text())
            body = json.loads(request['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'material', 'queries'})
            self.assertNotIn('source_accounting', body['material'])
            self.assertNotIn('source_accounting', request['prompt'])
            for number, family in ((11, 'chain'), (23, 'qualified')):
                request = json.loads((root / ('execution/attempt-%02d/request.json' % number)).read_text())
                body = json.loads(request['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
                self.assertEqual(body['queries'], e.plan.inputs()['queries'][family])
                self.assertEqual(len(body['queries']), 88)
                self.assertNotIn('object_aliases', body['material'])
            foreign = e.plan.slots()[12]
            graph = json.loads((root / 'execution/attempt-13/answer.json').read_text())
            self.assertIsNone(e.plan.request(e.plan.slots()[10], {e.plan.parent(foreign): graph}))
            (root / 'inputs/reference.private.json').write_text('[]')
            with self.assertRaises(ValueError):
                e.plan.verify(root / 'inputs')
            self.assertTrue(result['scope_closed'])


if __name__ == '__main__':
    unittest.main()
