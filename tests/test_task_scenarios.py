"""Calibrate new task cases and scorer damage; no model fidelity observations."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('task_scenario_tests', ROOT / 'benchmarks/task-scenarios-v1/check.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class TaskScenarioTests(unittest.TestCase):
    def test_published_artifacts_reproduce_and_keep_denominators_and_limits(self):
        artifacts = check.artifacts()
        for name, value in artifacts.items():
            self.assertEqual(json.loads((check.HERE / name).read_text(encoding='utf-8')), value)
        design = artifacts['design.json']
        self.assertEqual((design['profiles'], design['dependent_template_families'], design['source_messages']), (8, 4, 48))
        self.assertEqual((design['primary_cases'], design['known'], design['unknown']), (40, 28, 12))
        self.assertEqual((design['unique_public_forms'], design['person_form_combinations'], design['planned_answers']), (40, 80, 160))
        for flag in ('semantic_reference_independently_accepted', 'independent_holdout', 'new_service_authority',
                     'existing_benchmarks_or_defaults_changed', 'counterfactual_answer_transitions_semantically_verified',
                     'source_interventions_are_compressor_damage'):
            self.assertIs(design[flag], False)
        self.assertEqual(design['model_calls'], 0)

    def test_opposite_people_share_tasks_but_not_choice_order_past_or_commitment(self):
        data = check.corpus.build()
        for pid, pair in data['pairs'].items():
            self.assertEqual(data['questions'][pid], data['questions'][pair])
            own = {r['case']: r['contract'] for r in data['rows'] if r['profile'] == pid}
            other = {r['case']: r['contract'] for r in data['rows'] if r['profile'] == pair}
            for case in own:
                if case == 'uncovered':
                    self.assertEqual((own[case]['reference'], other[case]['reference']), ('U', 'U'))
                else:
                    self.assertNotEqual(own[case]['reference'], other[case]['reference'])
        self.assertEqual({r['contract']['intent'] for r in data['rows']}, set(check.corpus.authoring.KINDS))

    def test_source_interventions_change_one_user_span_and_keep_both_question_orders(self):
        data = check.corpus.build()
        rows = {(r['profile'], r['case']): r for r in data['rows']}
        for mutation in data['mutations']:
            original = rows[mutation['profile'], mutation['case']]['contract']
            changed = mutation['contract']
            self.assertNotEqual(original['reference'], changed['reference'])
            self.assertEqual(check.corpus.authoring.prepare(original, data['sources'][mutation['profile']])['questions.public'],
                             check.corpus.authoring.prepare(changed, mutation['sources'])['questions.public'])
            self.assertEqual(original['contrasts'][0]['predicted_answer'], changed['reference'])
            self.assertEqual(changed['contrasts'][0]['predicted_answer'], original['reference'])
            self.assertIs(mutation['semantic_transition_independently_verified'], False)
        damaged = copy.deepcopy(data)
        damaged['mutations'][0]['sources']['sources'][1]['text'] += '改变第二条消息'
        with patch.object(check.corpus, 'build', return_value=damaged):
            with self.assertRaisesRegex(ValueError, 'exactly one user message'):
                check.artifacts()

    def test_known_past_and_unknown_commitment_do_not_collapse_into_one_unknown(self):
        data = check.corpus.build()
        for row in data['rows']:
            c = row['contract']
            if row['case'] == 'past':
                self.assertNotEqual(c['reference'], 'U')
                self.assertIsNone(c['unknown_reason'])
            if row['case'] == 'commitment':
                # The assistant's advice is identical; only the user's decision differs.
                assistant = [m for m in data['sources'][row['profile']]['sources'] if m['role'] == 'assistant']
                self.assertEqual(len(assistant), 1)
                self.assertIn('建议你接受', assistant[0]['text'])
                self.assertEqual(c['reference'], 'U' if row['profile'].endswith('0') else '接受安排')

    def test_encoder_reader_packets_exclude_references_and_other_person_sources(self):
        data = check.corpus.build()
        for pid in data['sources']:
            packet = check.encoder_packet(pid)
            self.assertEqual(packet, {'sources': data['sources'][pid]})
            self.assertEqual(check.reader_packet(pid, '测试卡'), {'memory': '测试卡', 'questions': data['questions'][pid]})
            packet['sources']['sources'][0]['text'] = 'edited locally'
            self.assertNotEqual(check.encoder_packet(pid), packet)
        for profile in ('unknown-person', None, []):
            with self.assertRaises(ValueError):
                check.encoder_packet(profile)
        with self.assertRaises(ValueError):
            check.reader_packet('repair0', {'reference': 'leak'})
        for mutation in data['mutations']:
            packet = check.intervention_packet(mutation['profile'], mutation['case'])
            self.assertEqual(set(packet), {'sources', 'questions'})
            self.assertEqual(packet['sources'], mutation['sources'])
            self.assertEqual(packet['questions'], check.reader_packet(mutation['profile'], '')['questions'])
            self.assertEqual(len(packet['questions']), 10)
        with self.assertRaises(ValueError):
            check.intervention_packet('repair0', 'other')

    def test_scorer_distinguishes_oracle_all_unknown_fault_and_wrong_person_fixtures(self):
        data = check.corpus.build()
        fixtures = check.fixtures(data)
        self.assertEqual({k: check.score(v)['strict_correct'] for k, v in fixtures.items()},
                         {'author_reference': 40, 'all_unknown': 12, 'declared_fault': 0, 'paired_person': 8})
        result = check.score(fixtures['all_unknown'])
        self.assertEqual(result['known'], {'planned': 28, 'correct': 0})
        self.assertEqual(result['unknown'], {'planned': 12, 'correct': 12})
        self.assertFalse(result['model_authenticity_verified'])
        self.assertFalse(result['independent_semantic_acceptance'])

    def test_one_bad_order_loses_one_case_and_missing_never_shrinks_denominator(self):
        data = check.corpus.build()
        perfect = check.fixtures(data)['author_reference']
        damaged = copy.deepcopy(perfect)
        row = data['rows'][0]
        damaged[0]['answers'][row['query_ids'][1]] = 'U'
        self.assertEqual(check.score(damaged)['strict_correct'], 39)
        del damaged[0]['answers'][row['query_ids'][0]]
        result = check.score(damaged)
        self.assertEqual((result['planned_cases'], result['strict_correct'], result['missing_cases'], result['missing_answers']), (40, 39, 1, 1))
        result = check.score(perfect[1:])
        self.assertEqual((result['strict_correct'], result['missing_cases'], result['missing_answers']), (35, 5, 10))
        result = check.score([])
        self.assertEqual((result['planned_cases'], result['missing_cases'], result['missing_answers']), (40, 40, 160))

    def test_duplicate_read_extra_person_question_positional_and_malformed_values_rejected(self):
        perfect = check.fixtures(check.corpus.build())['author_reference']
        for fault in ('duplicate', 'person', 'question', 'position', 'malformed', 'repeat', 'extra_field'):
            with self.subTest(fault=fault):
                records = copy.deepcopy(perfect)
                qid = next(iter(records[0]['answers']))
                if fault == 'duplicate': records.append(copy.deepcopy(records[0]))
                elif fault == 'person': records[0]['profile'] = 'other'
                elif fault == 'question': records[0]['answers']['other-question'] = 'U'
                elif fault == 'position': records[0]['answers'][qid] = 'A'
                elif fault == 'malformed': records[0]['answers'][qid] = []
                elif fault == 'repeat': records[0]['read_repeat'] = True
                else: records[0]['unplanned_best_of'] = True
                with self.assertRaises(ValueError): check.score(records)

    def test_transition_scorer_rejects_frozen_answers_and_retains_missing_denominators(self):
        data = check.corpus.build()
        before = check.fixtures(data)['author_reference']
        after, unchanged = [], []
        rows = {(r['profile'], r['case']): r for r in data['rows']}
        for mutation in data['mutations']:
            pid, case = mutation['profile'], mutation['case']
            row = rows[pid, case]
            for repeat in (0, 1):
                baseline_answers = {q: other['contract']['reference'] for other in data['rows']
                                    if other['profile'] == pid for q in other['query_ids']}
                changed_answers = {**baseline_answers, **{q: mutation['contract']['reference'] for q in row['query_ids']}}
                record = {'profile': pid, 'case': case, 'read_repeat': repeat,
                          'answers': changed_answers}
                after.append(record)
                unchanged.append({**record, 'answers': baseline_answers})
        result = check.score_transitions(before, after)
        self.assertEqual((result['strict_both_correct'], result['missing_transitions']), (40, 0))
        self.assertEqual(result['non_target_preservation'], {'planned_case_interventions': 160, 'strict_both_correct': 160, 'missing': 0})
        self.assertEqual(check.score_transitions(before, unchanged)['strict_both_correct'], 0)
        self.assertEqual(check.score_transitions([], after)['strict_both_correct'], 0)
        result = check.score_transitions(before, after[1:])
        self.assertEqual((result['planned_transitions'], result['strict_both_correct'], result['missing_transitions'], result['missing_intervention_answers']), (40, 39, 1, 10))
        self.assertEqual(result['missing_target_answers'], 2)
        self.assertEqual(result['non_target_preservation'], {'planned_case_interventions': 160, 'strict_both_correct': 156, 'missing': 4})
        damaged = copy.deepcopy(after)
        other = rows['repair0', 'past']
        damaged[0]['answers'][other['query_ids'][0]] = 'U'
        result = check.score_transitions(before, damaged)
        self.assertEqual(result['strict_both_correct'], 40)
        self.assertEqual(result['non_target_preservation']['strict_both_correct'], 159)
        for flag in ('independent_evidence', 'source_edits_are_compressor_damage', 'model_authenticity_verified',
                     'semantic_transitions_independently_verified'):
            self.assertIs(result[flag], False)
        for fault in ('duplicate', 'extra_question', 'wrong_case', 'bool_repeat'):
            with self.subTest(fault=fault):
                broken = copy.deepcopy(after)
                if fault == 'duplicate': broken.append(copy.deepcopy(broken[0]))
                elif fault == 'extra_question': broken[0]['answers']['foreign'] = 'U'
                elif fault == 'wrong_case': broken[0]['case'] = 'nonexistent'
                else: broken[0]['read_repeat'] = False
                with self.assertRaises(ValueError): check.score_transitions(before, broken)


if __name__ == '__main__':
    unittest.main()
