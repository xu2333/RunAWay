"""Finite-world oracle and protocol damage checks; no measured model fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('epistemic_transfer_tests', ROOT / 'benchmarks/epistemic-transfer-v1/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
w = engine.plan.corpus


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
            answer = {q['id']: 'U' for q in self.data['queries']['all']}
        else:
            answer = {q: row['gold'] for row in self.data['rows'] if row['person'] == pid for q in row['query_ids']}
            if fault == 'control':
                q = next(r for r in self.data['rows'] if r['person'] == pid and r['personal_known'])['query_ids'][0]
                answer[q] = 'U'
        if fault == 'wire':
            answer = {}
        return json.dumps(answer, ensure_ascii=False), {'backend': 'offline_fixture',
            'model_requested': engine.plan.MODEL,
            'usage': None if fault == 'usage' else [{'input_tokens': 0, 'output_tokens': 0}]}


class EpistemicTransferTests(unittest.TestCase):
    def test_exhaustive_universe_and_separately_written_hand_references(self):
        for rule in range(4):
            self.assertEqual(tuple(w.predict(rule, s) for s in w.STATES), w.RULE_TABLES[rule])
        self.assertEqual((len(w.ALL_TABLES), len(set(w.ALL_TABLES))), (16, 16))
        data = w.build()
        self.assertEqual(json.loads(json.dumps(data, ensure_ascii=False)), data)
        self.assertEqual((len(data['rows']), sum(r['gold'] != 'U' for r in data['rows'])), (120, 58))
        self.assertEqual((sum(r['derived_known'] for r in data['rows']), sum(r['personal_known'] for r in data['rows'])), (31, 48))
        self.assertEqual(sum(r['guarantee_withdrawal_sensitive'] for r in data['rows']), 20)
        self.assertEqual(sum(len(s['sources']) for s in data['sources'].values()), 176)

    def test_partial_question_wording_matches_the_finite_feature_completions(self):
        cases = w.case_specs()
        for di in (0, 1):
            local_unknown, undo_unknown = cases[di*7+4:di*7+6]
            self.assertEqual({w.STATES[s] for s in local_unknown['states']}, {(0, 1), (1, 1)})
            self.assertIn('没有说明内容是否外发', local_unknown['scenario'])
            self.assertIn('所有改动可一步完整恢复', local_unknown['scenario'])
            self.assertEqual({w.STATES[s] for s in undo_unknown['states']}, {(0, 0), (0, 1)})
            self.assertIn('完整内容会传到外部服务', undo_unknown['scenario'])
            self.assertIn('没有说明能否撤销', undo_unknown['scenario'])
        for di in (0, 1):
            for si, state in enumerate(w.STATES):
                text = cases[di*7+si]['scenario']
                self.assertIn('全部内容只留在本机' if state[0] else '完整内容会传到外部服务', text)
                self.assertIn('一步完整恢复' if state[1] else '不能撤销', text)

    def test_constructed_calibration_distinguishes_lost_inference_and_overreach(self):
        spec = importlib.util.spec_from_file_location('epistemic_calibration', ROOT / 'benchmarks/epistemic-transfer-v1/check.py')
        check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check)
        result = check.calibration()
        expected = {'reference_vector': (120, 58, 62), 'always_unknown': (62, 0, 62),
                    'direct_observations_only': (89, 27, 62), 'ignore_guarantee_withdrawal': (100, 58, 42)}
        self.assertEqual(result['new_model_calls'], 0)
        for name, values in expected.items():
            self.assertEqual(tuple(result['vectors'][name][k] for k in ('correct', 'known_correct', 'unknown_correct')), values)

    def test_ambiguous_policy_still_entails_some_unseen_choices(self):
        evidence = {'guarantee': True, 'observations': [[1, 0]]}
        self.assertEqual(w.compatible(evidence), [w.RULE_TABLES[1], w.RULE_TABLES[3]])
        cases = w.case_specs()
        self.assertEqual(w.oracle(evidence, cases[0]), 0)  # unseen00, unanimous manual
        self.assertEqual(w.oracle(evidence, cases[3]), 1)  # unseen11, unanimous auto
        self.assertEqual(w.oracle(evidence, cases[2]), 'U')  # unseen10 differs
        self.assertEqual(w.oracle(evidence, cases[5]), 0)  # missingundo, but both completions manual

    def test_missing_complete_family_guarantee_prevents_false_identification(self):
        observations = [[1, 1], [2, 1]]
        closed = {'guarantee': True, 'observations': observations}
        withdrawn = {'guarantee': False, 'observations': observations}
        self.assertEqual(w.compatible(closed), [w.RULE_TABLES[0]])
        self.assertIn((0, 1, 1, 0), w.compatible(withdrawn))
        self.assertEqual(w.oracle(closed, w.case_specs()[3]), 1)
        self.assertEqual(w.oracle(withdrawn, w.case_specs()[3]), 'U')
        self.assertEqual(w.oracle(withdrawn, w.case_specs()[1]), 1)  # explicit decision survives withdrawal

    def test_hidden_unobserved_truth_cannot_leak_through_sources_suggestions_or_gold(self):
        original = w.build()
        tables = [list(pair) for pair in w.GENERATING_TABLES]
        tables[4][0] = w.RULE_TABLES[0]  # same observed01, different unobserved00/10
        tables[1][0] = (1, 1, 1, 1)  # same two decisions, different unseen truth
        changed = w.build(tables)
        self.assertEqual(original['sources'], changed['sources'])
        self.assertEqual(original['queries'], changed['queries'])
        self.assertEqual(original['rows'], changed['rows'])
        self.assertNotEqual(original['author_parameters'], changed['author_parameters'])
        for dimension in (0, 1):
            for value in range(4):
                self.assertEqual(len({p[1-dimension] for p in w.POLICIES if p[dimension] == value}), 2)

    def test_outside_vocabulary_domain_and_conflicting_evidence_are_not_guessed(self):
        evidence = {'guarantee': True, 'observations': [[1, 1], [2, 1]]}
        for case in w.case_specs():
            if not case['in_scope']:
                self.assertEqual(w.oracle(evidence, case), 'U')
        with self.assertRaises(ValueError):
            w.compatible({'guarantee': True, 'observations': [[1, 0], [1, 1]]})

    def test_request_isolation_no_external_decoder_and_exact_role_text_tail(self):
        slots = engine.plan.slots()
        self.assertEqual(len(slots), 49)
        self.assertEqual([s['kind'] for s in slots[:9]].count('full'), 8)
        self.assertTrue(all(s['kind'] == 'extract' for s in slots[9:17]))
        data = engine.plan.inputs()
        family = w.family_text(w.DOMAINS[0])
        self.assertNotIn(family, engine.plan.request(slots[0])['prompt'])
        for slot in slots[9:17]:
            request = engine.plan.request(slot)
            body = json.loads(request['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
            self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
            self.assertEqual(body['sources'], data['sources'][slot['profile']])
            self.assertNotIn('hidden_generating_tables', request['prompt'])
            self.assertNotIn('e01_ab', request['prompt'])
        slot = slots[1]
        full = engine.plan.transcript(data['sources'][slot['profile']])
        expected = engine.plan.choice_reader.make_request(full, data['queries']['all'],
            as_of=engine.plan.AS_OF, answer_format='text', reader_mode='standard')
        self.assertEqual(engine.plan.request(slot)['prompt'], engine.plan.base.old.old.COMMON + expected['prompt'])
        extract = slots[9]
        fixture = Fixture()
        raw, _ = fixture({}, None, extract)
        parent = json.loads(raw)
        read = next(s for s in slots if s['kind'] == 'read' and s['profile'] == extract['profile'])
        self.assertIsNone(engine.plan.request(read))
        request = engine.plan.request(read, {engine.plan.parent(extract): parent})
        prompt = engine.plan.bind(extract, parent)['prompt.md']
        expected = engine.plan.choice_reader.make_request(prompt, data['queries']['all'],
            as_of=engine.plan.AS_OF, answer_format='text', reader_mode='standard')
        self.assertEqual(request['prompt'], engine.plan.base.old.old.COMMON + expected['prompt'])
        self.assertNotIn(family, request['prompt'])
        self.assertEqual(engine.plan.material(extract['profile'], prompt, 'tail'), full[-len(prompt):])

    def execute(self, directory, fixture):
        root = Path(directory) / 'review'
        engine.plan.prepare(root)
        return root, engine.run(root, root / 'fixture', fixture, lambda _: {}, simulated=True)

    def test_complete_oracle_fixture_49_attempts_and_stratified_120case_denominators(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture()
            _, result = self.execute(tmp, fixture)
            self.assertEqual((fixture.calls, result['status'], result['unused_slots_expire']), (49, 'complete', 0))
            self.assertTrue(result['simulated'])
            self.assertEqual(result['local_cli_child_intents'], 0)
            for view in ('card', 'tail'):
                self.assertEqual(result['scores']['per_view_strict'][view]['joint'], {'planned': 120, 'correct': 120, 'missing': 0})
                for key, count in (('derived_known', 31), ('personal_known', 48), ('guarantee_withdrawal_sensitive', 20), ('observed_decision', 27)):
                    self.assertEqual(result['scores']['slices'][view][key], {'planned': count, 'correct': count, 'missing': 0})

    def test_control_failure_and_invalid_parent_keep_original_denominators(self):
        for fault, at, calls, missing in (('control', 2, 2, 120), ('product', 10, 45, 15)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at)
                _, result = self.execute(tmp, fixture)
                self.assertEqual((fixture.calls, result['unused_slots_expire']), (calls, 49-calls))
                for view in ('card', 'tail'):
                    joint = result['scores']['per_view_strict'][view]['joint']
                    self.assertEqual((joint['planned'], joint['missing']), (120, missing))

    def test_unknown_usage_wire_transport_and_actual_mode_missing_guard_close(self):
        for fault, at in (('usage', 1), ('wire', 10), ('transport', 49)):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                fixture = Fixture(fault, at)
                _, result = self.execute(tmp, fixture)
                self.assertEqual((fixture.calls, result['status'], result['unused_slots_expire']), (at, 'stopped', 49-at))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'review'
            engine.plan.prepare(root)
            fixture = Fixture()
            result = engine.run(root, root / 'denied', fixture, lambda _: {}, simulated=False)
            self.assertEqual((fixture.calls, result['attempt_reservations']), (0, 0))

    def test_one_bad_order_and_frozen_package_mutation_are_not_repaired(self):
        data = engine.plan.inputs()
        cards, answers = {}, {}
        for pid, method, generation in engine.plan.cells():
            key = pid, method, generation
            cards[key] = {'prompt': 'x'*400, 'characters': 400}
            own = {q: r['gold'] for r in data['rows'] if r['person'] == pid for q in r['query_ids']}
            for view in ('card', 'tail'):
                for repeat in (0, 1):
                    answers[key+(view, repeat)] = copy.deepcopy(own)
        first = data['rows'][0]
        answers[first['person'], engine.plan.METHODS[0], 0, 'card', 1][first['query_ids'][1]] = 'U'
        result = engine.score.summarize(data['rows'], answers, cards)
        self.assertEqual(result['per_view_strict']['card']['joint']['correct'], 119)
        self.assertEqual(result['per_view_strict']['tail']['joint']['correct'], 120)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'review'
            engine.plan.prepare(root)
            self.assertTrue(engine.plan.verify(root))
            (root / 'author-parameters.private.json').write_text('{}')
            with self.assertRaises(ValueError):
                engine.plan.verify(root)


if __name__ == '__main__':
    unittest.main()
