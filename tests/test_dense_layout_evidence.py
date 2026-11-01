"""Adversarial mutations of actual evidence; all replay is offline."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dense_read_evidence_tests', ROOT / 'scripts/replay_dense_layout_probe.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class DenseReadEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_closed14fixed_reads_replay_without_new_generation_or_service(self):
        r = archive.check()
        self.assertEqual(r['actual_original_attempts'], 14)
        self.assertEqual(r['new_model_calls'], 0)
        self.assertEqual(r['new_extractions'], 0)
        self.assertEqual(r['primary_dense_cases'], 40)
        self.assertFalse(r['fresh_generation_stability_test'])
        self.assertTrue(r['expanded_is_uncapped_diagnostic_not_memory_candidate'])
        self.assertEqual(r['expanded_dense_observed_response_agreement'],
            {'planned_paired_question_responses': 320, 'matching': 320, 'differing': 0, 'missing': 0})
        for m in archive.engine.plan.METHODS:
            c = r['scores']['methods'][m]['strict_all_parents_and_reads']
            self.assertEqual((c['joint']['planned'], c['known']['planned'], c['unknown']['planned']), (40, 24, 16))

    def test_method_or_generation_swaps_cannot_select_another_parent(self):
        for field, value in (('method', 'foreign'), ('generation', 8)):
            d = copy.deepcopy(self.data)
            rec = next((r for r in d['records'] if r['kind'] == 'read'), d['records'][0])
            rec[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                archive.replay(d)

    def test_request_raw_and_artifact_drift_is_not_hidden_by_new_hashes(self):
        for fault in ('request', 'raw', 'card'):
            d = copy.deepcopy(self.data)
            if fault == 'request':
                rec = d['records'][0]
                rec['request']['prompt'] += '\nchanged'
                rec['request_sha256'] = archive.engine.plan.digest(rec['request'])
            elif fault == 'raw':
                rec = next(r for r in d['records'] if r['raw_present'])
                rec['raw'] += 'changed'
                rec['raw_value_sha256'] = archive.engine.plan.digest(rec['raw'])
            else:
                d['fixed_views'][0]['prompt'] += 'borrowed or changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_reference_mask_and_cross_source_claims_are_not_new_truth(self):
        for fault in ('reference', 'mask', 'independent_reference_acceptance', 'validates_j16_or_development', 'fresh_generation_stability_test'):
            d = copy.deepcopy(self.data)
            if fault == 'reference':
                d['reference_rows'][0]['gold'] = 'changed'
            elif fault == 'mask':
                d['fixed_views'][0]['generation'] = 9
            else:
                d[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_gates_denominators_missing_and_paired_wins_are_recomputed(self):
        for fault in ('gate', 'denominator', 'missing', 'paired'):
            d = copy.deepcopy(self.data)
            if fault == 'gate':
                d['status']['control_gates']['h93']['qualified'] = False
            elif fault == 'denominator':
                d['status']['scores']['methods']['dense']['strict_all_parents_and_reads']['joint']['planned'] = 39
            elif fault == 'missing':
                d['status']['scores']['methods']['dense']['strict_all_parents_and_reads']['joint']['missing'] += 1
            else:
                d['status']['scores']['paired_strict']['dense_vs_expanded']['only_dense_correct'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_removing_or_duplicating_an_attempt_cannot_improve_the_record(self):
        for fault in ('remove', 'duplicate'):
            d = copy.deepcopy(self.data)
            if fault == 'remove':
                removed = d['records'].pop()
                d['status']['attempt_reservations'] -= 1
                d['status']['unused_slots_expire'] += 1
                d['status']['local_cli_child_intents'] -= int(removed['local_cli_child_intent'])
            else:
                d['records'][1]['execution_id'] = d['records'][0]['execution_id']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_usage_subsets_and_unknown_counters_cannot_become_zero(self):
        for fault in ('mandatory', 'subset', 'total'):
            d = copy.deepcopy(self.data)
            row = next(r for r in d['records'] if r.get('usage_rows'))['usage_rows'][0]
            if fault == 'mandatory':
                del row['input_tokens']
            elif fault == 'subset':
                row['cached_input_tokens'] = row['input_tokens'] + 1
            else:
                d['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_runtime_holdout_or_default_change_cannot_be_forged(self):
        for fault in ('runtime', 'independent_holdout', 'production_default_changed'):
            d = copy.deepcopy(self.data)
            if fault == 'runtime':
                d['implementation_sha256'] = {}
            else:
                d[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)


if __name__ == '__main__':
    unittest.main()
