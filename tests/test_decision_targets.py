"""Candidate input isolation and discriminating finite development controls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/decision-targets-v1'
spec = importlib.util.spec_from_file_location('decision_target_checks', HERE / 'check.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class DecisionTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads((HERE / 'development.synthetic.json').read_text())

    def test_portable_calibration_preserves_claim_boundary(self):
        result = bench.check()
        self.assertEqual(result['new_model_calls'], 0)
        self.assertFalse(result['candidate_model_effect_measured'])
        self.assertFalse(result['production_default_changed'])
        self.assertEqual(result['logical_calibration']['intact_typed_view']['joint'], {'planned': 16, 'correct': 16})

    def test_only_source_body_and_instruction_delta_reach_extractor(self):
        candidate = bench.candidate
        request = candidate.make_request(self.packet['sources'], 1536)
        previous = candidate.base.make_request(self.packet['sources'], 1536)
        marker = '\nEXTRACTION_INPUT_JSON:\n'
        prefix, body = previous['prompt'].split(marker, 1)
        self.assertEqual(request['prompt'], prefix + candidate.RULES + marker + body)
        self.assertEqual(request['schema'], previous['schema'])
        payload = json.loads(body)
        self.assertEqual(payload['sources'], self.packet['sources'])
        self.assertNotIn('queries', payload)
        self.assertNotIn('rules', payload)
        self.assertNotIn('facts', payload)

    def test_candidate_does_not_bake_in_consumed_failure_ids_or_choices(self):
        for text in ['h93', 'h68', 't01', 't02', 'm29', 'm45', '切换新接口', '保留旧接口', '118/120', '119/120']:
            self.assertNotIn(text, bench.candidate.RULES)

    def test_candidate_uses_same_binder_without_backend_calls(self):
        answer = json.loads((HERE / 'examples/partial-answer.synthetic.json').read_text())
        with patch.object(bench.grouped, 'codex_generate', side_effect=AssertionError('No model allowed')):
            a = bench.candidate.bind(answer, self.packet['sources'], 1536)
            b = bench.grouped.bind(answer, self.packet['sources'], 1536)
            self.assertEqual(a, b)
            self.assertLess(len(a['prompt.md']), 1536)
            self.assertIn('先存草稿，暂不下单', a['prompt.md'])

    def test_compact_shared_group_keeps_both_question_targets(self):
        answer = json.loads((HERE / 'examples/partial-answer-compact.synthetic.json').read_text())
        files = bench.candidate.bind(answer, self.packet['sources'], 1536)
        public = bench.grouped.parse_public(files['prompt.md'])
        self.assertEqual(len(public['groups']), 1)
        self.assertEqual([r['when'] for r in public['groups'][0]['rules']], ['所问为选款', '所问为执行安排，尺寸尚未核对'])
        self.assertEqual([r['choose'] for r in public['groups'][0]['rules']], ['蓝色帆布包', '先存草稿，暂不下单'])

    def test_source_role_and_nonliteral_anchor_damage_still_rejected(self):
        answer = json.loads((HERE / 'examples/partial-answer.synthetic.json').read_text())
        for fault in ['role', 'quote']:
            changed = copy.deepcopy(answer)
            if fault == 'role':
                source = next(s for s in self.packet['sources']['sources'] if s['id'] == 's4')
                changed['groups'][0]['rules'][0]['decisions'] = [{'source_id': 's4', 'quote': source['text']}]
            else:
                changed['groups'][0]['rules'][0]['decisions'][0]['quote'] = 'not in the source'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.candidate.bind(changed, self.packet['sources'], 1536)

    def test_private_target_truth_is_not_in_reader_queries(self):
        body = json.loads(bench.reader_request('toy public card', self.packet)['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'material', 'queries'})
        for query in body['queries']:
            self.assertEqual(set(query), {'id', 'scenario', 'options'})
            self.assertFalse({'target', 'facts', 'expected', 'stratum'} & set(query))

    def test_preference_only_score_would_miss_erased_execution_constraints(self):
        results = bench.calibrate(self.packet)
        erased = results['erase_execution_boundaries']['groups']
        self.assertEqual(erased['preference'], {'planned': 11, 'correct': 11})
        self.assertEqual(erased['execution'], {'planned': 5, 'correct': 2})
        self.assertEqual(erased['joint'], {'planned': 16, 'correct': 13})

    def test_missing_choice_condition_and_actual_conflict_remain_unknown(self):
        byid = {q['public']['id']: q for q in self.packet['queries']}
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q04']), 'U')
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q06']), 'U')
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q05']), '海蓝色')

    def test_all_covered_branches_agree_but_uncovered_worlds_cannot_be_ignored(self):
        query = next(q for q in self.packet['queries'] if q['public']['id'] == 'q07')
        self.assertEqual(bench.oracle.resolve(self.packet, query), '先发书面意见')
        changed = copy.deepcopy(self.packet)
        changed['rules'] = [r for r in changed['rules'] if r['id'] != 'discussion_no_room']
        self.assertEqual(bench.oracle.resolve(changed, query), 'U')

    def test_unknown_not_false_and_unknown_permission_not_granted(self):
        byid = {q['public']['id']: q for q in self.packet['queries']}
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q09']), 'U')
        changed = copy.deepcopy(byid['q09'])
        changed['facts']['raining'] = False
        self.assertEqual(bench.oracle.resolve(self.packet, changed), '走园径')
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q03']), 'U')
        self.assertEqual(bench.oracle.resolve(self.packet, byid['q13']), 'U')

    def test_every_damaged_view_is_detected_without_dropping_denominators(self):
        results = bench.calibrate(self.packet)
        self.assertEqual(len(results), 8)
        for name, result in results.items():
            self.assertEqual(result['groups']['joint']['planned'], 16)
            self.assertEqual(result['groups']['unknown']['planned'], 7)
            if name != 'intact_typed_view':
                self.assertLess(result['groups']['joint']['correct'], 16)

    def test_ontology_renaming_does_not_encode_expected_decisions(self):
        changed = copy.deepcopy(self.packet)
        targets = {r['target'] for r in changed['rules']} | {q['target'] for q in changed['queries']}
        names = {target: 'opaque_' + str(i) for i, target in enumerate(sorted(targets))}
        for rule in changed['rules']:
            rule['target'] = names[rule['target']]
        for query in changed['queries']:
            query['target'] = names[query['target']]
        self.assertEqual(bench.oracle.score(changed), bench.oracle.score(self.packet))

    def test_known_action_not_offered_does_not_fall_back_to_other_choice(self):
        query = copy.deepcopy(self.packet['queries'][0])
        query['public']['options'] = {'A': '红色帆布包', 'B': '灰色帆布包'}
        self.assertEqual(bench.oracle.resolve(self.packet, query), 'U')

    def test_supersession_cannot_cross_target_or_delete_a_different_scope(self):
        for fault in ['target', 'scope']:
            changed = copy.deepcopy(self.packet)
            old = next(r for r in changed['rules'] if r['id'] == 'bag_old')
            if fault == 'target':
                old['target'] = 'bag_execution'
            else:
                old['requires']['other_requirement'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.oracle.resolve(changed, changed['queries'][0])

    def test_development_claims_cannot_be_rewritten_as_model_evidence(self):
        changed = copy.deepcopy(self.packet)
        changed['real_model_performance_measured'] = True
        with self.assertRaises(ValueError):
            bench.validate(changed)


if __name__ == '__main__':
    unittest.main()
