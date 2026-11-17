"""Portable accounting checks; no new observations or independent semantic grade."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('task_result_check', ROOT/'scripts/check_real_task_history.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TaskResultTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads(checker.DEFAULT.read_text(encoding='utf-8'))

    def test_published_accounting_and_limits(self):
        result = checker.check(self.report)
        self.assertEqual(result['primary']['available_text_history'], {'cases': 1, 'retained': 1})
        self.assertEqual(result['primary']['no_history'], {'cases': 1, 'retained': 0})
        self.assertEqual(result['reported_tokens']['total'], 129759)
        self.assertFalse(result['semantic_reassessment'])

    def test_drop_or_duplicate_observation_cannot_pass(self):
        for mutate in (lambda r: r['rows'].pop(), lambda r: r['rows'].__setitem__(7, copy.deepcopy(r['rows'][0]))):
            value = copy.deepcopy(self.report); mutate(value)
            with self.assertRaises(ValueError): checker.check(value)

    def test_unclear_cannot_silently_become_retained(self):
        value = copy.deepcopy(self.report)
        value['rows'][0]['quality_pass'] = True
        with self.assertRaisesRegex(ValueError, 'quality uncertainty'): checker.check(value)
        value = copy.deepcopy(self.report)
        value['rows'][3]['retained'] = True
        with self.assertRaisesRegex(ValueError, 'joint endpoint'): checker.check(value)

    def test_repetitions_and_exploratory_case_not_primary_people(self):
        for field in ('independent_people', 'primary_cases'):
            value = copy.deepcopy(self.report); value[field] = 2
            with self.assertRaises(ValueError): checker.check(value)
        value = copy.deepcopy(self.report)
        value['totals']['available_text_history']['by_role']['primary']['cases'] = 2
        with self.assertRaisesRegex(ValueError, 'separate strata'): checker.check(value)

    def test_tokens_and_constraint_only_totals_must_recount(self):
        value = copy.deepcopy(self.report); value['reported_tokens']['total'] += 1
        with self.assertRaisesRegex(ValueError, 'token totals'): checker.check(value)
        value = copy.deepcopy(self.report)
        value['target_constraint_only']['T1']['no_history']['met'] = 0
        with self.assertRaisesRegex(ValueError, 'constraint-only'): checker.check(value)

    def test_results_do_not_establish_compression_or_device_execution(self):
        for field in ('compression_comparison', 'device_execution'):
            value = copy.deepcopy(self.report); value[field] = True
            with self.assertRaisesRegex(ValueError, 'claim boundary'): checker.check(value)


if __name__ == '__main__': unittest.main()
