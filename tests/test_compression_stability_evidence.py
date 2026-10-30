"""Corrupt portable actual evidence; every replay is offline and unbilled."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('stability_evidence_tests', ROOT / 'scripts/replay_compression_stability.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class StabilityEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_closed_snapshot_replays_all_reserved_attempts_without_model_calls(self):
        result = archive.check()
        self.assertEqual(result['actual_original_attempts'], self.data['status']['attempt_reservations'])
        self.assertLessEqual(result['actual_original_attempts'], 41)
        self.assertEqual(result['new_model_calls'], 0)
        self.assertFalse(result['production_default_changed'])
        self.assertEqual(result['original_inventory_remaining'], 72)
        for b in ('768', '1024'):
            counts = result['scores']['per_budget_strict'][b]
            self.assertEqual(counts['joint']['planned'], 96)
            self.assertEqual(counts['known']['planned'], 54)
            self.assertEqual(counts['unknown']['planned'], 42)
            self.assertEqual(counts['execution']['planned'], 5)
            self.assertEqual(counts['untyped']['planned'], 80)

    def test_changed_request_cannot_be_hidden_by_a_recomputed_checksum(self):
        data = copy.deepcopy(self.data)
        rec = next((r for r in data['records'] if r['kind'] == 'read'), data['records'][0])
        rec['request']['prompt'] += '\nchanged'
        rec['request_sha256'] = archive.engine.plan.digest(rec['request'])
        with self.assertRaises(ValueError):
            archive.replay(data)

    def test_raw_response_drift_and_duplicate_execution_are_rejected(self):
        for fault in ('raw', 'duplicate'):
            data = copy.deepcopy(self.data)
            if fault == 'raw':
                rec = next(r for r in data['records'] if r['raw_present'])
                rec['raw'] += 'changed'
            else:
                data['records'][1]['execution_id'] = data['records'][0]['execution_id']
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_invalid_products_and_missing_generations_cannot_be_deleted(self):
        data = copy.deepcopy(self.data)
        invalid = next(r for r in data['records'] if r.get('product_invalid'))
        data['records'].remove(invalid)
        data['status']['attempt_reservations'] -= 1
        data['status']['unused_slots_expire'] += 1
        data['status']['local_cli_child_intents'] -= int(invalid['local_cli_child_intent'])
        with self.assertRaises(ValueError):
            archive.replay(data)

    def test_a_card_cannot_be_inserted_for_an_invalid_or_wrong_generation(self):
        data = copy.deepcopy(self.data)
        rec = next(r for r in data['records'] if r.get('product_invalid'))
        rec['card'] = {'prompt': 'borrowed sibling', 'characters': 16}
        with self.assertRaises(ValueError):
            archive.replay(data)

    def test_original_card_bytes_are_bound_to_raw_extraction(self):
        data = copy.deepcopy(self.data)
        rec = next(r for r in data['records'] if 'card' in r)
        rec['card']['prompt'] += 'changed'
        with self.assertRaises(ValueError):
            archive.replay(data)

    def test_gates_scores_and_skip_denominators_are_recomputed(self):
        for fault in ('gate', 'score', 'skip'):
            data = copy.deepcopy(self.data)
            if fault == 'gate':
                data['status']['control_gates']['h68']['qualified'] = False
            elif fault == 'score':
                data['status']['scores']['per_budget_strict']['768']['joint']['planned'] -= 1
            else:
                if data['status']['skipped']:
                    data['status']['skipped'].pop()
                else:
                    data['status']['skipped'].append({'invented_skip': True})
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_unknown_or_double_counted_usage_is_not_zero(self):
        for fault in ('missing', 'subset', 'ledger'):
            data = copy.deepcopy(self.data)
            if fault == 'missing':
                del data['records'][0]['usage_rows'][0]['input_tokens']
            elif fault == 'subset':
                row = data['records'][0]['usage_rows'][0]
                row['cached_input_tokens'] = row['input_tokens'] + 1
            else:
                data['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_reference_runtime_holdout_and_default_claims_cannot_drift(self):
        for fault in ('reference', 'runtime', 'independent_holdout', 'production_default_changed'):
            data = copy.deepcopy(self.data)
            if fault == 'reference':
                data['reference_rows'][0]['gold'] = 'U'
            elif fault == 'runtime':
                data['implementation_sha256'] = {}
            else:
                data[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)


if __name__ == '__main__':
    unittest.main()
