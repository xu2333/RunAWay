"""Recorded coverage cannot become a pass, best-of selection or JSON receipt."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('inventory_completion_test', ROOT / 'scripts/replay_regression_inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = inventory.old.read(inventory.HERE / 'observed.synthetic.json')

    def test_all232observations_bound_but_not_accepted_or_passing(self):
        r = inventory.check()
        self.assertEqual(r['structurally_bound_observed_cases'], 232)
        self.assertEqual(r['missing_cases'], [])
        self.assertEqual(r['rejected_observations'], [])
        self.assertEqual(len(r['disputed_cases_retained']), 3)
        self.assertFalse(r['reference_acceptance_or_accuracy_assessed'])
        self.assertFalse(r['regression_pass_claim'])
        self.assertFalse(r['project_endpoint_proved'])
        self.assertFalse(r['hashes_or_json_flags_alone_prove_real_inference'])
        self.assertEqual(r['new_model_calls'], 0)

    def test_missing_duplicate_or_extra_pass_receipt_is_rejected(self):
        for fault in ('missing', 'duplicate', 'receipt'):
            d = copy.deepcopy(self.data)
            if fault == 'missing':
                d['observations'].pop()
            elif fault == 'duplicate':
                d['observations'][-1] = d['observations'][0]
            else:
                d['observations'][0]['verified'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                inventory.replay(d)

    def test_later_better_reading_cannot_replace_first_chronological_observation(self):
        d = copy.deepcopy(self.data)
        c = d['contexts']['j62']
        c['reading_execution_id'] = 'attempt-24'
        with self.assertRaises(ValueError):
            inventory.replay(d)

    def test_source_or_artifact_raw_bytes_are_not_just_json_flags(self):
        for field in ('source_file_utf8', 'artifact_file_utf8'):
            d = copy.deepcopy(self.data)
            d['contexts']['j16'][field] += 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                inventory.replay(d)

    def test_original_requirements_and_dispute_flags_cannot_be_removed(self):
        d = copy.deepcopy(self.data)
        next(r for r in d['requirements'] if r['reference_disputed'])['reference_disputed'] = False
        with self.assertRaises(ValueError):
            inventory.replay(d)

    def test_coverage_completion_cannot_be_upgraded_to_truth_or_goal_completion(self):
        for fault in ('semantic', 'pass'):
            d = copy.deepcopy(self.data)
            if fault == 'semantic':
                d['independent_semantic_acceptance'] = True
            else:
                d['assessment']['regression_pass_claim'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                inventory.replay(d)


if __name__ == '__main__':
    unittest.main()
