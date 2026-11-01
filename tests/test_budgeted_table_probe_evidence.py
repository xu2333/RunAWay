"""Adversarial mutations of actual evidence; all replay is offline."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('budgeted_probe_evidence_tests', ROOT / 'scripts/replay_budgeted_table_probe.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class BudgetedProbeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_closed_actual_scope_replays40fixed_cases_with_no_new_calls(self):
        r = archive.check()
        self.assertEqual(r['actual_original_attempts'], len(self.data['records']))
        self.assertLessEqual(r['actual_original_attempts'], 14)
        self.assertEqual(r['new_model_calls'], 0)
        self.assertEqual(r['primary_cases'], 40)
        for m in archive.engine.plan.METHODS:
            c = r['scores']['per_method_strict'][m]
            self.assertEqual((c['joint']['planned'], c['known']['planned'], c['unknown']['planned'], c['personal_known']['planned']), (40, 24, 16, 14))
        self.assertEqual(r['scores']['paired_strict_development_cases']['planned'], 40)
        self.assertFalse(r['validates_j16_or_development'])
        self.assertFalse(r['can_combine_with_older39_into_new79_result'])

    def test_method_or_generation_swaps_cannot_select_another_parent(self):
        for field, value in (('method', 'foreign'), ('generation', 8)):
            d = copy.deepcopy(self.data)
            rec = next((r for r in d['records'] if r['kind'] == 'extract'), d['records'][0])
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
                rec = next((r for r in d['records'] if 'card' in r), d['records'][0])
                rec.setdefault('card', {})['prompt'] = 'borrowed or changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_reference_mask_and_cross_source_claims_are_not_new_truth(self):
        for fault in ('reference', 'mask', 'independent_reference_acceptance', 'validates_j16_or_development', 'can_combine_with_older39_into_new79_result'):
            d = copy.deepcopy(self.data)
            if fault == 'reference':
                d['legacy_reference_rows'][0]['gold'] = 'changed'
            elif fault == 'mask':
                d['disputed_reference_rows'] = [d['reference_rows'][0]]
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
                d['status']['scores']['per_method_strict']['budgeted-table-v1']['joint']['planned'] = 39
            elif fault == 'missing':
                d['status']['scores']['per_method_strict']['budgeted-table-v1']['joint']['missing'] += 1
            else:
                d['status']['scores']['paired_strict_development_cases']['only_candidate_correct'] += 1
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
