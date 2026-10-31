"""Offline corruption controls; preflagged observations never become new gold."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('world_evidence_tests', ROOT / 'scripts/replay_remaining_world_frontier.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class WorldEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_closed_scope_replays_with69primary3unscored_and_no_new_calls(self):
        r = archive.check()
        self.assertEqual(r['new_model_calls'], 0)
        self.assertEqual(r['actual_original_attempts'], len(self.data['records']))
        self.assertLessEqual(r['actual_original_attempts'], 40)
        self.assertEqual((r['primary_cases_per_budget'], r['legacy_cases_retained'], r['unscored_disputed_cases']), (69, 72, 3))
        self.assertFalse(r['w14_reference_accepted'])
        for budget in ('1024', '1536'):
            c = r['scores']['per_budget_strict'][budget]
            self.assertEqual((c['joint']['planned'], c['known']['planned'], c['unknown']['planned']), (69, 51, 18))

    def test_changed_reference_mask_or_global_acceptance_is_rejected(self):
        for fault in ('mask', 'legacy', 'w14_reference_accepted', 'independent_semantic_acceptance'):
            data = copy.deepcopy(self.data)
            if fault == 'mask':
                data['disputed_reference_rows'].pop()
            elif fault == 'legacy':
                data['legacy_reference_rows'][0]['gold'] = 'changed'
            else:
                data[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_scored_denominator_and_unscored_observation_cannot_be_rewritten(self):
        for fault in ('denominator', 'acceptance', 'response'):
            data = copy.deepcopy(self.data)
            if fault == 'denominator':
                data['status']['scores']['per_budget_strict']['1024']['joint']['planned'] = 72
            else:
                row = data['status']['scores']['disputed_observations_not_scored'][0]
                if fault == 'acceptance':
                    row['reference_accepted'] = True
                else:
                    row['generations_reads_orders'][0][0][0] = 'forged'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_request_or_raw_drift_cannot_be_hidden_by_new_hash(self):
        for fault in ('request', 'raw'):
            data = copy.deepcopy(self.data)
            rec = data['records'][0]
            if fault == 'request':
                rec['request']['prompt'] += '\nchanged'
                rec['request_sha256'] = archive.engine.plan.digest(rec['request'])
            else:
                rec['raw'] += 'changed'
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_missing_generation_or_duplicate_execution_cannot_select_better_outcome(self):
        for fault in ('remove', 'duplicate'):
            data = copy.deepcopy(self.data)
            if fault == 'duplicate':
                data['records'][1]['execution_id'] = data['records'][0]['execution_id']
            else:
                rec = data['records'].pop()
                data['status']['attempt_reservations'] -= 1
                data['status']['local_cli_child_intents'] -= int(rec['local_cli_child_intent'])
                data['status']['unused_slots_expire'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_artifact_content_or_source_generation_binding_cannot_drift(self):
        data = copy.deepcopy(self.data)
        rec = next(r for r in data['records'] if 'card' in r)
        rec['card']['prompt'] += 'changed'
        with self.assertRaises(ValueError):
            archive.replay(data)

    def test_usage_subset_and_closed_scope_counter_are_recomputed(self):
        for fault in ('subset', 'ledger'):
            data = copy.deepcopy(self.data)
            if fault == 'subset':
                row = data['records'][0]['usage_rows'][0]
                row['reasoning_output_tokens'] = row['output_tokens'] + 1
            else:
                data['status']['known_usage']['total_tokens'] += 1
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)

    def test_holdout_or_runtime_claim_cannot_be_inserted(self):
        for fault in ('independent_holdout', 'runtime'):
            data = copy.deepcopy(self.data)
            if fault == 'runtime':
                data['implementation_sha256'] = {}
            else:
                data[fault] = True
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                archive.replay(data)


if __name__ == '__main__':
    unittest.main()
