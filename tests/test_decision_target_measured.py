"""Damage controls for actual source-bound comparison evidence, no inference."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/decision-targets-v1'
spec = importlib.util.spec_from_file_location('target_measured_test', HERE / 'measured.py')
measured = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measured)


class MeasuredTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE / 'measured.synthetic.json').read_text())

    def test_closed_actual_snapshot_replays_without_service(self):
        result = measured.check()
        self.assertEqual(result['actual_calls'], len(self.data['records']))
        self.assertEqual(result['actual_calls'], 21)
        self.assertEqual(result['known_usage']['total_tokens'], 375216)
        self.assertEqual(result['strict_totals']['v1']['joint']['correct'], 96)
        self.assertEqual(result['strict_totals']['v2']['joint']['correct'], 96)
        self.assertEqual(result['strict_totals']['v1']['joint']['planned'], 96)
        self.assertEqual(result['strict_totals']['v2']['joint']['planned'], 96)
        self.assertEqual(result['profiles']['dev']['v2']['strict']['execution']['planned'], 5)
        self.assertEqual(result['profiles']['dev']['v2']['strict']['preference']['planned'], 11)
        self.assertEqual(result['new_model_calls'], 0)
        self.assertEqual((result['old_inventory_measured'], result['old_inventory_remaining']), (160, 72))
        self.assertFalse(result['production_default_changed'])
        self.assertFalse(result['project_goal_complete'])

    def test_request_cannot_switch_card_owner_or_method(self):
        data = copy.deepcopy(self.data)
        rec = next(r for r in data['records'] if r['kind'] == 'cached_read')
        rec['request']['prompt'] += '\nchanged'
        rec['request_sha256'] = measured.exp.digest(rec['request'])
        with self.assertRaises(ValueError):
            measured.replay(data)

    def test_missing_repeat_cannot_be_deleted_or_best_of_selected(self):
        data = copy.deepcopy(self.data)
        data['records'].pop()
        data['status']['attempt_reservations'] -= 1
        data['status']['local_cli_child_intents'] -= 1
        data['status']['unused_slots_expire'] += 1
        with self.assertRaises(ValueError):
            measured.replay(data)

    def test_duplicate_execution_or_reordered_slot_is_rejected(self):
        for fault in ('duplicate', 'order'):
            data = copy.deepcopy(self.data)
            if fault == 'duplicate':
                data['records'][1]['execution_id'] = data['records'][0]['execution_id']
            else:
                data['records'][1], data['records'][2] = data['records'][2], data['records'][1]
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                measured.replay(data)

    def test_exact_raw_and_source_bound_card_are_verified(self):
        for fault in ('raw', 'card'):
            data = copy.deepcopy(self.data)
            rec = next(r for r in data['records'] if 'card' in r)
            if fault == 'raw':
                rec['raw'] += 'changed'
            else:
                rec['card']['prompt'] += 'changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                measured.replay(data)

    def test_unknown_usage_and_double_counted_subsets_are_rejected(self):
        for fault in ('missing', 'subset', 'ledger'):
            data = copy.deepcopy(self.data)
            rec = data['records'][0]
            if fault == 'missing':
                del rec['usage_rows'][0]['input_tokens']
            elif fault == 'subset':
                rec['usage_rows'][0]['reasoning_output_tokens'] = rec['usage_rows'][0]['output_tokens'] + 1
            else:
                data['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                measured.replay(data)

    def test_reference_rewrite_or_failed_control_cannot_pass(self):
        for fault in ('gold', 'gate'):
            data = copy.deepcopy(self.data)
            if fault == 'gold':
                data['reference_rows'][0]['gold'] = 'U'
            else:
                data['status']['control_gates']['dev']['qualified'] = False
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                measured.replay(data)

    def test_unmeasured_claim_and_runtime_drift_are_rejected(self):
        for fault in ('independent_holdout', 'production_default_changed', 'runtime', 'remove_pins'):
            data = copy.deepcopy(self.data)
            if fault == 'runtime':
                data['implementation_sha256']['../outside'] = '0' * 64
            elif fault == 'remove_pins':
                data['implementation_sha256'] = {}
            else:
                data[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                measured.replay(data)

    def test_missing_is_not_a_correct_unknown_and_one_read_is_not_enough(self):
        rows = [{'query_ids': ['a', 'b'], 'gold': 'U', 'stratum': 'execution', 'personal_known': False}]
        a = {'a': 'U', 'b': 'U'}
        self.assertEqual(measured.counts(rows, a, {})['execution'], {'planned': 1, 'correct': 0, 'missing': 1})
        self.assertEqual(measured.counts(rows, a, {'a': 'U', 'b': 'yes'})['execution'],
                         {'planned': 1, 'correct': 0, 'missing': 0})


if __name__ == '__main__':
    unittest.main()
