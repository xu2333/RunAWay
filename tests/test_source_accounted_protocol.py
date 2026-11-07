"""Finite27 source-only lifecycle fixtures; oracle answers are not model results."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('accounted_protocol_test', ROOT / 'benchmarks/source-accounted-encoding-v1/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.fault, self.at, self.calls = fault, at, []

    def __call__(self, request, folder, slot):
        self.calls.append(slot)
        p, pid = e.plan, slot['profile']
        data = p.inputs()
        if slot['kind'] == 'extract':
            source = data['sources'][pid]['sources'][0]
            anchor = dict(source_id=source['id'], quote=source['text'])
            answer = dict(version=p.factory(slot['method']).VERSION, name='协议夹具', tagline='不是实际提炼。',
                          objects=['夹具对象'], unknowns=['夹具不提供行为保真证明。'], nodes=[
                              dict(id='n0', kind='base', target_kind='choice', object_index=0,
                                   question='夹具选择', requires=[], action='这里', priority=0,
                                   decisions=[anchor], contexts=[anchor], order_split=None)])
            if slot['method'] == p.METHODS[1]:
                answer.update(derived_node_ids=[], source_accounting={
                    s['id']: dict(kind='direct_choice' if s['id'] == source['id'] else 'no_choice',
                                  node_ids=['n0'] if s['id'] == source['id'] else [],
                                  reason='仅验证协议，不是真实分类。')
                    for s in data['sources'][pid]['sources'] if s['role'] == 'user'})
                if slot['slot'] == self.at and self.fault == 'product':
                    answer['source_accounting'][source['id']]['kind'] = 'no_choice'
                if slot['slot'] == self.at and self.fault == 'wire':
                    answer.pop('source_accounting')
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in data['queries']['all']}
        else:
            answer = {q: row['gold'] for row in data['rows'] if row['person'] == pid for q in row['query_ids']}
            if slot['slot'] == self.at and self.fault in ('control', 'order'):
                row = next(r for r in data['rows'] if r['person'] == pid and r['personal_known'])
                answer[row['query_ids'][1]] = 'U'
        return json.dumps(answer, ensure_ascii=False), {
            'backend': 'offline_fixture', 'model_requested': p.MODEL,
            'usage': None if slot['slot'] == self.at and self.fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class SourceAccountedProtocolTests(unittest.TestCase):
    def execute(self, root, fixture, *, simulated=True):
        e.plan.prepare(root / 'inputs')
        return e.run(root / 'inputs', root / 'execution', fixture, lambda _: {}, simulated=simulated)

    def test_frozen_population_schedule_and_source_only_inputs(self):
        p = e.plan
        data = p.inputs()
        slots = p.slots()
        self.assertEqual(len(slots), 27)
        self.assertEqual([sum(s['kind'] == kind for s in slots) for kind in ('none', 'full', 'extract', 'read')], [1, 2, 8, 16])
        self.assertEqual((len(data['rows']), sum(r['gold'] != 'U' for r in data['rows'])), (30, 13))
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 44)
        for slot in [s for s in slots if s['kind'] == 'extract']:
            req = p.request(slot)
            body = json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(body['sources'], data['sources'][slot['profile']])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertNotIn('e01_ab', req['prompt'])
            self.assertNotIn('reference.private', req['prompt'])
        self.assertFalse(p.values()['proposal.json']['approved'])

    def test_complete_oracle_fixture_keeps_both_method_denominators_and_public_only_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = Fixture()
            result = self.execute(root, fixture)
            request = json.loads((root / 'execution/attempt-08/request.json').read_text())
            self.assertNotIn('source_accounting', request['prompt'])
        self.assertEqual((len(fixture.calls), result['status'], result['local_cli_child_intents']), (27, 'complete', 0))
        self.assertTrue(result['simulated'])
        for method in e.plan.METHODS:
            counts = result['scores']['methods'][method]['card']['strict']
            self.assertEqual(counts['joint'], dict(planned=30, correct=30, missing=0))
            self.assertEqual(counts['known']['planned'], 13)
            self.assertEqual(counts['unknown']['planned'], 17)

    def test_invalid_new_parent_skips_only_own_reads_and_keeps_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('product', 7)
            result = self.execute(Path(tmp), fixture)
        self.assertEqual((len(fixture.calls), len(result['skipped']), result['unused_slots_expire']), (25, 2, 2))
        self.assertEqual(result['scores']['methods'][e.plan.METHODS[1]]['card']['strict']['joint'], dict(planned=30, correct=15, missing=15))
        self.assertEqual(result['scores']['methods'][e.plan.METHODS[0]]['card']['strict']['joint']['correct'], 30)

    def test_one_wrong_option_order_is_not_hidden_by_other_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('order', 8)
            result = self.execute(Path(tmp), fixture)
        self.assertEqual(result['scores']['methods'][e.plan.METHODS[1]]['card']['strict']['joint'], dict(planned=30, correct=29, missing=0))

    def test_control_schema_usage_or_missing_live_guard_closes_without_retry(self):
        for fault, slot, expected in (('control', 2, 2), ('wire', 7, 7), ('usage', 5, 5)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, slot)
                result = self.execute(Path(tmp), fixture)
                self.assertEqual((len(fixture.calls), result['status'], result['unused_slots_expire']), (expected, 'stopped', 27 - expected))
                self.assertTrue(result['scope_closed'])
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            result = self.execute(Path(tmp), fixture, simulated=False)
            self.assertEqual((len(fixture.calls), result['attempt_reservations']), (0, 0))

    def test_input_drift_extra_files_and_symlinks_are_rejected(self):
        for fault in ('reference', 'extra', 'symlink'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'prepared'
                e.plan.prepare(root)
                if fault == 'reference':
                    (root / 'reference.private.json').write_text('[]')
                elif fault == 'extra':
                    (root / 'unexpected').write_text('extra')
                else:
                    file = root / 'sources.json'
                    target = Path(tmp) / 'source.json'
                    file.rename(target)
                    file.symlink_to(target)
                with self.assertRaises(ValueError):
                    e.plan.verify(root)


if __name__ == '__main__':
    unittest.main()
