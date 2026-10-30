"""Portable actual evidence, corruption controls and decision-target toy checks."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/regression-progress-v1'
spec = importlib.util.spec_from_file_location('regression_progress_check', HERE / 'check.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)
spec = importlib.util.spec_from_file_location('regression_target_contract', HERE / 'prototype/target_contract.py')
targets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(targets)


class RegressionProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE / 'observed.synthetic.json').read_text())
        cls.semantics = json.loads((HERE / 'semantic-dispute.synthetic.json').read_text())

    def test_actual_five_studies_replay_without_service(self):
        result = bench.replay(self.data, self.semantics)
        studies = result['studies']
        self.assertEqual(studies['forward']['groups']['own']['joint'], {'planned': 80, 'correct': 80, 'missing': 0})
        self.assertEqual(studies['new_worlds']['groups']['own']['joint'], {'planned': 96, 'correct': 93, 'missing': 0})
        self.assertEqual(studies['repair']['repeats']['candidate']['correct'], 24)
        self.assertEqual(studies['h17']['repeats']['candidate']['correct'], 40)
        self.assertEqual(studies['remaining_h']['repeats']['baseline']['correct'], 119)
        self.assertEqual(studies['remaining_h']['repeats']['candidate']['correct'], 118)
        self.assertEqual((result['actual_choice_calls'], result['neutral_opinion_calls']), (79, 2))
        self.assertEqual((result['revised_measured_cases'], result['revised_remaining_cases']), (160, 72))
        self.assertEqual(result['known_choice_tokens'] + result['known_neutral_tokens'], 1402492)
        self.assertFalse(result['w14_reference_accepted'])
        self.assertFalse(result['project_goal_complete'])

    def test_export_checksums_cards_and_privacy_boundary(self):
        result = bench.check()
        self.assertEqual(result['new_model_calls'], 0)
        self.assertFalse(result['production_default_changed'])
        self.assertEqual(result['w14_affected_people'], 4)

    def test_reference_change_to_another_offered_choice_is_detected(self):
        data = copy.deepcopy(self.data)
        study = data['studies']['remaining_h']
        row = next(r for r in study['reference_rows'] if r['gold'] != 'U')
        query = next(q for q in study['queries'] if q['id'] == row['query_ids'][0])
        row['gold'] = next(value for value in query['options'].values() if value != row['gold'])
        with self.assertRaises(ValueError):
            bench.replay(data, self.semantics)

    def test_source_and_whole_budget_cannot_drift(self):
        for fault in ('source', 'budget'):
            data = copy.deepcopy(self.data)
            study = data['studies']['new_worlds']
            if fault == 'source':
                study['sources']['j39']['sources'][0]['text'] += 'changed'
            else:
                study['whole_card_cap'] = 512
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.replay(data, self.semantics)

    def test_duplicate_execution_or_reordered_slot_is_rejected(self):
        for fault in ('id', 'slot'):
            data = copy.deepcopy(self.data)
            records = data['studies']['h17']['records']
            if fault == 'id':
                records[1]['execution_id'] = records[0]['execution_id']
            else:
                records[1], records[2] = records[2], records[1]
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.replay(data, self.semantics)

    def test_exact_raw_response_and_binder_artifact_are_checked(self):
        for fault in ('raw', 'card'):
            data = copy.deepcopy(self.data)
            rec = next(r for r in data['studies']['remaining_h']['records'] if r['group'] == 'extract')
            if fault == 'raw':
                rec['raw'] += 'changed'
            else:
                rec['card']['prompt'] += 'changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.replay(data, self.semantics)

    def test_wrong_person_reader_cannot_be_replaced_by_own_card(self):
        data = copy.deepcopy(self.data)
        study = data['studies']['forward']
        rec = next(r for r in study['records'] if r['group'] == 'wrong')
        rec['request'] = bench.request(study, 'own', rec['person'], {})
        rec['request_sha256'] = bench.digest(rec['request'])
        with self.assertRaises(ValueError):
            bench.replay(data, self.semantics)

    def test_unknown_or_inflated_usage_is_not_zero_or_double_counted(self):
        for fault in ('missing', 'subset', 'ledger'):
            data = copy.deepcopy(self.data)
            rec = data['studies']['h17']['records'][0]
            if fault == 'missing':
                del rec['usage_rows'][0]['input_tokens']
            elif fault == 'subset':
                rec['usage_rows'][0]['cached_input_tokens'] = rec['usage_rows'][0]['input_tokens'] + 1
            else:
                data['studies']['h17']['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.replay(data, self.semantics)

    def test_unseen_default_or_runtime_claim_cannot_be_added(self):
        for fault in ('holdout', 'default', 'runtime'):
            data = copy.deepcopy(self.data)
            if fault == 'holdout':
                data['independent_holdout'] = True
            elif fault == 'default':
                data['production_default_changed'] = True
            else:
                data['runtime_sha256']['../outside'] = '0' * 64
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                bench.replay(data, self.semantics)

    def test_original_failed_neutral_scope_cannot_be_reclassified_successful(self):
        semantics = copy.deepcopy(self.semantics)
        semantics['opinions'][0]['original_controller_state'] = 'completed'
        with self.assertRaises(ValueError):
            bench.replay(self.data, semantics)

    def test_question_citations_are_valid_but_do_not_become_user_evidence(self):
        report = self.semantics['opinions'][0]['report']
        with self.assertRaises(ValueError):
            bench.verify_citations(self.semantics, report, False)
        self.assertEqual(bench.verify_citations(self.semantics, report, True), {'user': 12, 'question': 4})
        semantics = copy.deepcopy(self.semantics)
        semantics['opinions'][0]['report']['j39']['source_evidence'][0]['quote'] = 'fabricated quote'
        with self.assertRaises(ValueError):
            bench.replay(self.data, semantics)

    def test_toy_missing_is_not_a_correct_unknown_or_deleted_denominator(self):
        rows = [{'person': 'p', 'query_ids': ['a', 'b'], 'gold': 'yes', 'personal_known': True},
                {'person': 'p', 'query_ids': ['c', 'd'], 'gold': 'U', 'personal_known': False}]
        empty = bench.counts(rows, {})
        self.assertEqual(empty['joint'], {'planned': 2, 'correct': 0, 'missing': 2})
        observed = bench.counts(rows, {'p': dict.fromkeys(['a', 'b', 'c', 'd'], 'U')})
        self.assertEqual(observed['known']['correct'], 0)
        self.assertEqual(observed['unknown']['correct'], 1)

    def test_repeats_never_select_the_better_read_or_add_independent_cases(self):
        rows = [{'person': 'p', 'query_ids': ['a', 'b'], 'gold': 'yes', 'personal_known': True}]
        result = bench.repeated(rows, {'p': {'a': 'U', 'b': 'U'}}, {'p': {'a': 'yes', 'b': 'yes'}})
        self.assertEqual(result, {'planned': 1, 'correct': 0, 'missing': 0, 'disagreeing_cases': 1})

    def test_toy_plan_choice_does_not_grant_publication_or_conflict_with_denial(self):
        rules = targets.annotated_rules('option_A')
        facts = {'public_interface_conditions': True, 'client_list_pending': True}
        self.assertEqual(targets.resolve(rules, 'plan_choice', facts), 'option_A')
        self.assertEqual(targets.resolve(rules, 'publication_permission', facts), 'do_not_publish')
        self.assertEqual(targets.resolve(rules[:1], 'publication_permission', facts), 'U')
        self.assertEqual(targets.resolve(rules, 'plan_choice', {'client_list_pending': True}), 'U')
        extra = copy.deepcopy(rules[0])
        extra['value'] = 'option_B'
        self.assertEqual(targets.resolve(rules + [extra], 'plan_choice', facts), 'U')


if __name__ == '__main__':
    unittest.main()
