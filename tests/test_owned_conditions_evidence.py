"""Closed actual evidence replay and adversarial archive mutations; no model."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owned_evidence_tests', ROOT / 'scripts/replay_owned_conditions.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class OwnedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_closed_actual_scope_replays_fixed_denominators_without_new_calls(self):
        r = archive.check()
        self.assertEqual(r['actual_original_attempts'], len(self.data['records']))
        self.assertLessEqual(r['actual_original_attempts'], 42)
        self.assertEqual(r['new_model_calls'], 0)
        self.assertEqual((r['primary_cases'], r['legacy_cases'], r['disputed_cases_unscored']), (79, 80, 1))
        self.assertFalse(r['disputed_reference_accepted'])
        self.assertFalse(r['annotation_semantics_independently_verified'])
        for method in archive.engine.plan.METHODS:
            c = r['scores']['per_method_strict'][method]
            self.assertEqual((c['joint']['planned'], c['known']['planned'], c['unknown']['planned']), (79, 50, 29))
        self.assertEqual(r['scores']['paired_strict_development_cases']['planned'], 79)

    def test_method_or_generation_cannot_be_changed_even_with_new_record_hash(self):
        for field, value in (('method', 'owned-v1'), ('generation', 7)):
            d = copy.deepcopy(self.data)
            rec = next((r for r in d['records'] if r['kind'] == 'extract'), d['records'][0])
            if rec.get(field) == value:
                value = 'foreign'
            rec[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                archive.replay(d)

    def test_request_raw_and_artifact_bytes_are_reconstructed(self):
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
                rec.setdefault('card', {})['prompt'] = 'borrowed or changed card'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_legacy_dispute_mask_and_reference_acceptance_cannot_change(self):
        for fault in ('legacy', 'mask', 'acceptance'):
            d = copy.deepcopy(self.data)
            if fault == 'legacy':
                d['legacy_reference_rows'][0]['gold'] = 'changed'
            elif fault == 'mask':
                d['disputed_reference_rows'].clear()
            else:
                d['disputed_reference_accepted'] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_score_and_paired_wins_cannot_be_rewritten(self):
        for fault in ('denominator', 'paired', 'missing'):
            d = copy.deepcopy(self.data)
            scores = d['status']['scores']
            if fault == 'denominator':
                scores['per_method_strict']['owned-v1']['joint']['planned'] = 80
            elif fault == 'paired':
                scores['paired_strict_development_cases']['only_candidate_correct'] += 1
            else:
                scores['per_method_strict']['owned-v1']['joint']['missing'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_removing_a_failed_or_successful_attempt_cannot_select_better_outcome(self):
        d = copy.deepcopy(self.data)
        removed = d['records'].pop()
        d['status']['attempt_reservations'] -= 1
        d['status']['local_cli_child_intents'] -= int(removed['local_cli_child_intent'])
        d['status']['unused_slots_expire'] += 1
        with self.assertRaises(ValueError):
            archive.replay(d)

    def test_unknown_and_double_counted_usage_do_not_become_zero(self):
        for fault in ('mandatory', 'subset', 'total'):
            d = copy.deepcopy(self.data)
            rec = next(r for r in d['records'] if r.get('usage_rows'))
            row = rec['usage_rows'][0]
            if fault == 'mandatory':
                del row['input_tokens']
            elif fault == 'subset':
                row['cached_input_tokens'] = row['input_tokens'] + 1
            else:
                d['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)

    def test_runtime_default_or_holdout_claim_cannot_be_inserted(self):
        for fault in ('runtime', 'production_default_changed', 'independent_holdout'):
            d = copy.deepcopy(self.data)
            if fault == 'runtime':
                d['implementation_sha256'] = {}
            else:
                d[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(d)


if __name__ == '__main__':
    unittest.main()
