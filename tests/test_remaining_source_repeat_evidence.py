"""Actual-archive damage checks: no service calls or independent semantic gold."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('epistemic_actual_archive_tests', ROOT / 'scripts/replay_remaining_source_repeat.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class RemainingSourceRepeatEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = replay.engine.plan.read(replay.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError)):
            replay.replay(data)

    def test_actual_archive_replays_offline_without_transport_and_keeps_fixed_cases(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            result = replay.check()
            backend.assert_not_called()
        self.assertEqual(result['primary_cases_per_method_view'],75)
        self.assertEqual(result['answers_per_primary_case'],8)
        self.assertEqual(result['planned_new_producers'],20)
        self.assertEqual(result['full_control_strict']['joint'],{'planned':75,'correct':75,'missing':0})
        self.assertEqual(result['scores']['answers_per_primary_case_method_view'],8)
        for method in replay.engine.plan.METHODS:
            self.assertEqual(result['scores']['methods'][method]['card']['strict']['joint']['planned'],75)
        for method in replay.engine.plan.METHODS:
            self.assertEqual(result['derived_strata'][method]['withdrawal_sensitive']['joint']['planned'],10)
            self.assertEqual(result['derived_strata'][method]['derived_known']['joint']['planned'],20)
            self.assertEqual(result['scores']['methods'][method]['card']['strict']['known']['planned'],36)
            self.assertEqual(result['scores']['methods'][method]['card']['strict']['unknown']['planned'],39)
        stages=result['reported_usage_by_stage']
        self.assertEqual(sum(s['attempts']for s in stages.values()),result['actual_original_attempts'])
        self.assertEqual(sum(s.get('total_tokens',0)for s in stages.values()),result['known_original_usage'].get('total_tokens',0))

    def test_scope_or_input_manifest_substitution_is_rejected(self):
        for key in ('kind', 'source_input_manifest_sha256'):
            data = copy.deepcopy(self.data)
            data[key] = 'foreign'
            self.reject(data)

    def test_changed_source_question_or_reference_is_rejected(self):
        for fault in ('source', 'question', 'reference'):
            data = copy.deepcopy(self.data)
            if fault == 'source':
                next(iter(data['sources'].values()))['sources'][0]['text'] += 'changed'
            elif fault == 'question':
                next(iter(data['queries'].values()))[0]['scenario'] += 'changed'
            else:
                next(row for row in data['reference_rows'] if row['gold'] != 'U')['gold'] = 'U'
            self.reject(data)

    def test_external_decoder_hidden_truth_stability_and_tail_claims_cannot_be_promoted(self):
        for key in ('independent_reference_acceptance', 'independent_generalization',
                    'generation_stability_verified', 'new_scene_generalization_claim',
                    'external_reader_decoder', 'hidden_generating_truth_resolves_unknown', 'token_matched_tail', 'optimal_tail_selection',
                    'tail_has_json_metadata'):
            data = copy.deepcopy(self.data)
            data[key] = True
            self.reject(data)

    def test_wrong_read_parent_or_request_drift_is_rejected(self):
        data = copy.deepcopy(self.data)
        record = next((r for r in data['records'] if r['kind'] == 'read'), data['records'][0])
        record['request']['prompt'] += ' foreign memory'
        record['request_sha256'] = replay.engine.plan.digest(record['request'])
        self.reject(data)

    def test_reordered_records_or_reclaimed_unused_slots_are_rejected(self):
        if len(self.data['records']) > 1:
            data = copy.deepcopy(self.data)
            data['records'][0], data['records'][1] = data['records'][1], data['records'][0]
            self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['unused_slots_expire'] += 1
        self.reject(data)

    def test_removed_missing_cases_or_changed_token_totals_are_rejected(self):
        data = copy.deepcopy(self.data)
        data['status']['scores']['methods']['source-order-v3']['card']['strict']['joint']['planned'] -= 1
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['known_usage']['total_tokens'] = data['status']['known_usage'].get('total_tokens', 0) + 1
        self.reject(data)

    def test_changed_response_or_artifact_cannot_replace_frozen_observation(self):
        data = copy.deepcopy(self.data)
        record = next((r for r in data['records'] if r['raw_present']), None)
        if record is None:
            self.skipTest('Closed scope has no returned raw response')
        record['raw'] += 'tampered'
        self.reject(data)
        card = next((r for r in self.data['records'] if 'card' in r), None)
        if card is not None:
            data = copy.deepcopy(self.data)
            record = next(r for r in data['records'] if 'card' in r)
            record['card']['prompt'] += 'tampered'
            self.reject(data)


if __name__=='__main__':
    unittest.main()
