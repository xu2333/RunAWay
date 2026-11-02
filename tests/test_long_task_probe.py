"""Offline protocol damage tests; oracle fixtures are not model observations."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('long_task_tests_engine', ROOT / 'benchmarks/long-task-probe-v1/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class Fixture:
    def __init__(self, fault=None, at=None):
        self.calls, self.fault, self.at = 0, fault, at
        self.data = engine.plan.inputs()

    def __call__(self, request, folder, slot):
        self.calls += 1
        fault = self.fault if slot['slot'] == self.at else None
        if fault == 'transport':
            raise TimeoutError('Offline fixture only')
        pid = slot['profile']
        if slot['kind'] == 'extract':
            source = self.data['sources'][pid]['sources'][0]
            anchor = {'source_id': source['id'], 'quote': source['text']}
            answer = {'version': engine.plan.candidate.VERSION, 'name': '协议夹具', 'tagline': '不是模型提炼。',
                'objects': ['夹具对象'], 'nodes': [{'id': 'base', 'kind': 'base', 'target_kind': 'choice',
                'object_index': 0, 'question': '夹具选择', 'requires': [], 'action': '夹具选择', 'priority': 0,
                'decisions': [anchor], 'contexts': [anchor], 'order_split': None}], 'unknowns': ['未覆盖未知。']}
            if fault == 'product':
                answer['nodes'][0]['object_index'] = 2
        elif slot['kind'] == 'none':
            answer = {q['id']: 'U' for q in self.data['queries'][engine.plan.bank(pid)]}
        else:
            answer = {q: r['gold'] for r in self.data['rows'] if r['person'] == pid for q in r['query_ids']}
            if fault == 'control':
                answer[next(r for r in self.data['rows'] if r['person'] == pid and r['gold'] != 'U')['query_ids'][0]] = 'U'
        if fault == 'wire':
            answer = {}
        provenance = {'backend': 'offline_fixture', 'model_requested': engine.plan.MODEL,
                      'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}
        return json.dumps(answer, ensure_ascii=False), provenance


class LongTaskProbeTests(unittest.TestCase):
    def execute(self, directory, fixture):
        root = Path(directory) / 'review'
        engine.plan.prepare(root)
        result = engine.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)
        return root, result

    def test_long_sources_keep_existing_questions_labels_and_grounded_quotes(self):
        data = engine.plan.inputs()
        short = engine.plan.corpus.short.build()
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 192)
        self.assertEqual((len(data['rows']), sum(r['gold'] == 'U' for r in data['rows'])), (40, 12))
        for pid in engine.plan.PROFILES:
            self.assertEqual(data['queries'][engine.plan.bank(pid)], short['questions'][pid])
            self.assertGreater(len(engine.plan.old.old.canonical(data['sources'][pid])), engine.plan.BUDGET)
            self.assertGreater(sum(len(s['text']) for s in data['sources'][pid]['sources']), engine.plan.BUDGET)
            originals = {r['case']: r for r in short['rows'] if r['profile'] == pid}
            for row in [r for r in data['rows'] if r['person'] == pid]:
                self.assertEqual(row['gold'], originals[row['case']]['contract']['reference'])
                index = {s['id']: s for s in data['sources'][pid]['sources']}
                for a in row['support']:
                    self.assertEqual(index[a['source_id']]['role'], 'user')
                    self.assertIn(a['quote'], index[a['source_id']]['text'])
        for role in ('choice', 'past', 'order', 'commitment'):
            ranks = [p[role] for p in data['design']['active_user_message_positions'].values()]
            self.assertEqual(sorted(ranks), [5, 6, 11, 12, 17, 18, 23, 24])

    def test_schedule_packets_source_only_extraction_and_tail_matching(self):
        slots = engine.plan.slots()
        self.assertEqual((len(slots), [s['kind'] for s in slots[:12]].count('full')), (52, 8))
        self.assertTrue(all(s['kind'] == 'extract' for s in slots[12:20]))
        for slot in slots[12:20]:
            request = engine.plan.request(slot)
            payload = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(set(payload), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertEqual(payload['sources'], engine.plan.inputs()['sources'][slot['profile']])
            self.assertNotIn('repair_choice_ab', request['prompt'])
        for pid in engine.plan.PROFILES:
            text = 'x' * 400
            raw = engine.plan.transcript(engine.plan.inputs()['sources'][pid])
            self.assertEqual(engine.plan.material(pid, text, 'tail'), raw[-400:])
            self.assertEqual(len(engine.plan.material(pid, text, 'tail')), len(text))
        proposal = engine.plan.values()['proposal.json']
        self.assertFalse(proposal['approved'])
        self.assertFalse(proposal['generation_stability_verified'])
        self.assertTrue(proposal['full_and_tail_share_same_role_labelled_transcript_layout'])
        slot = next(s for s in slots if s['kind'] == 'full')
        full_text = engine.plan.transcript(engine.plan.inputs()['sources'][slot['profile']])
        expected = engine.plan.choice_reader.make_request(full_text,
            engine.plan.inputs()['queries'][engine.plan.bank(slot['profile'])], as_of=engine.plan.AS_OF,
            answer_format='text', reader_mode='standard')
        self.assertEqual(engine.plan.request(slot)['prompt'], engine.plan.old.old.COMMON + expected['prompt'])

    def test_complete_fixture_is_52_intents_and_fixed_40_cases_not_a_model_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            _, result = self.execute(tmp, fixture)
            self.assertEqual((fixture.calls, result['status'], result['unused_slots_expire']), (52, 'complete', 0))
            self.assertTrue(result['simulated'])
            self.assertEqual(result['local_cli_child_intents'], 0)
            for view in ('card', 'tail'):
                self.assertEqual(result['scores']['per_view_strict'][view]['joint'], {'planned': 40, 'correct': 40, 'missing': 0})
            self.assertEqual(result['scores']['paired_card_tail']['both_correct'], 40)
            self.assertFalse(result['scores']['generation_stability_verified'])

    def test_unqualified_control_closes_before_any_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('control', 2)
            _, result = self.execute(tmp, fixture)
            self.assertEqual((fixture.calls, result['status'], result['unused_slots_expire']), (2, 'stopped', 50))
            self.assertEqual(result['scores']['per_view_strict']['card']['joint'], {'planned': 40, 'correct': 0, 'missing': 40})

    def test_invalid_parent_skips_only_own_four_reads_and_keeps_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture('product', 13)
            _, result = self.execute(tmp, fixture)
            self.assertEqual((fixture.calls, result['unused_slots_expire'], len(result['skipped'])), (48, 4, 4))
            for view in ('card', 'tail'):
                self.assertEqual(result['scores']['per_view_strict'][view]['joint'], {'planned': 40, 'correct': 35, 'missing': 5})

    def test_one_bad_order_loses_exactly_one_case_without_best_of(self):
        data = engine.plan.inputs()
        cards, answers = {}, {}
        for pid, method, generation in engine.plan.cells():
            key = pid, method, generation
            cards[key] = {'prompt': 'x' * 400, 'characters': 400}
            own = {q: r['gold'] for r in data['rows'] if r['person'] == pid for q in r['query_ids']}
            for view in ('card', 'tail'):
                for repeat in (0, 1):
                    answers[key + (view, repeat)] = copy.deepcopy(own)
        first = data['rows'][0]
        answers[first['person'], engine.plan.METHODS[0], 0, 'card', 1][first['query_ids'][1]] = 'U'
        result = engine.score.summarize(data['rows'], answers, cards)
        self.assertEqual(result['per_view_strict']['card']['joint']['correct'], 39)
        self.assertEqual(result['per_view_strict']['tail']['joint']['correct'], 40)
        self.assertEqual(result['paired_card_tail']['tail_only'], 1)

    def test_wire_transport_unknown_usage_and_frozen_input_drift_stop(self):
        for fault, at in (('wire', 13), ('transport', 52), ('usage', 1)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at)
                _, result = self.execute(tmp, fixture)
                self.assertEqual((fixture.calls, result['status'], result['unused_slots_expire']), (at, 'stopped', 52-at))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'review'
            engine.plan.prepare(root)
            self.assertEqual(len(engine.plan.read(root / 'static-requests.json')), 20)
            self.assertEqual(len(engine.plan.read(root / 'dynamic-rules.json')['slots']), 32)
            self.assertTrue(engine.plan.verify(root))
            (root / 'sources.json').write_text('{}')
            with self.assertRaises(ValueError):
                engine.plan.verify(root)

    def test_actual_mode_requires_owned_guard_and_dynamic_reader_uses_only_own_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'review'
            engine.plan.prepare(root)
            fixture = Fixture()
            result = engine.run(root, root / 'not_authorized', fixture, lambda _: {}, simulated=False)
            self.assertEqual((fixture.calls, result['status'], result['attempt_reservations']), (0, 'stopped', 0))
        slot = next(s for s in engine.plan.slots() if s['kind'] == 'extract')
        fixture = Fixture()
        raw, _ = fixture({}, None, slot)
        parent = json.loads(raw)
        read = next(s for s in engine.plan.slots() if s['kind'] == 'read' and s['profile'] == slot['profile'])
        other = next(s for s in engine.plan.slots() if s['kind'] == 'extract' and s['profile'] != slot['profile'])
        self.assertIsNone(engine.plan.request(read, {engine.plan.parent(other): parent}))
        request = engine.plan.request(read, {engine.plan.parent(slot): parent})
        bank = engine.plan.inputs()['queries'][engine.plan.bank(slot['profile'])]
        prompt = engine.plan.bind(slot, parent)['prompt.md']
        expected = engine.plan.choice_reader.make_request(prompt, bank, as_of=engine.plan.AS_OF,
                     answer_format='text', reader_mode='standard')
        self.assertEqual(request['schema'], expected['schema'])
        self.assertEqual(request['prompt'], engine.plan.old.old.COMMON + expected['prompt'])


if __name__ == '__main__':
    unittest.main()
