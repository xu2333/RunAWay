"""Fixed-view archive damage checks; no new inference or independent gold."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fixed_card_archive_tests', ROOT / 'scripts/replay_coverage_fixed_views.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class CoverageFixedViewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = replay.p.read(replay.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError)):
            replay.replay(data)

    def test_actual_archive_replays_offline_with_fixed_denominators_and_no_new_generation(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            result = replay.check()
        backend.assert_not_called()
        self.assertEqual(result['actual_original_attempts'],9)
        self.assertEqual(result['missing_original_usage'],0)
        self.assertEqual(result['known_original_usage']['total_tokens'],110877)
        self.assertEqual(result['new_extractions'],0)
        self.assertFalse(result['old43_scores_replaced'])
        self.assertEqual(result['scores']['guided30']['joint'],{'planned':30,'correct':30,'missing':0})
        self.assertEqual(result['scores']['guided30']['known']['correct'],18)
        self.assertEqual(result['scores']['guided30']['unknown']['correct'],12)
        for view in replay.p.VIEWS:
            self.assertEqual(result['scores']['fixed_views'][view]['joint'],{'planned':15,'correct':15,'missing':0})
        stages = result['reported_usage_by_stage']
        self.assertEqual(sum(s['attempts'] for s in stages.values()), result['actual_original_attempts'])
        self.assertEqual(sum(s.get('total_tokens', 0) for s in stages.values()), result['known_original_usage'].get('total_tokens', 0))

    def test_scope_and_reconstructed_input_manifest_cannot_be_substituted(self):
        for key in ('kind', 'source_input_manifest_sha256'):
            data = copy.deepcopy(self.data)
            data[key] = 'foreign'
            self.reject(data)

    def test_changed_source_question_reference_or_implementation_is_rejected(self):
        for fault in ('source', 'question', 'reference', 'implementation'):
            data = copy.deepcopy(self.data)
            if fault == 'source':
                data['sources']['a8r']['sources'][0]['text'] += 'changed'
            elif fault == 'question':
                data['queries']['all'][0]['scenario'] += 'changed'
            elif fault == 'reference':
                data['reference_rows'][0]['gold'] = 'U'
            else:
                data['implementation_sha256'] = {}
            self.reject(data)

    def test_repaired_card_or_wrong_request_parent_is_rejected(self):
        data = copy.deepcopy(self.data)
        data['materials']['a8r:baseline'] += '报名分组也自动。'
        self.reject(data)
        if not self.data['records']:
            self.skipTest('Original scope stopped before any invocation')
        data = copy.deepcopy(self.data)
        record = next((r for r in data['records'] if r['kind'] == 'read'), data['records'][0])
        record['request']['prompt'] += ' supplemented domain'
        record['request_sha256'] = replay.p.digest(record['request'])
        self.reject(data)

    def test_endpoint_denominators_or_partial_success_selection_cannot_change(self):
        data = copy.deepcopy(self.data)
        data['status']['scores']['fixed_views']['a8r:baseline']['joint']['planned'] -= 1
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['scores']['fixed_views']['a8r:baseline']['joint']['correct'] += 1
        self.reject(data)

    def test_raw_response_tampering_is_not_a_new_observation(self):
        data = copy.deepcopy(self.data)
        record = next((r for r in data['records'] if r['raw_present']), None)
        if record is None:
            self.skipTest('Original scope returned no raw response')
        record['raw'] += 'tampered'
        self.reject(data)

    def test_token_child_unused_slot_and_record_order_ledgers_are_preserved(self):
        data = copy.deepcopy(self.data)
        data['status']['known_usage']['total_tokens'] = data['status']['known_usage'].get('total_tokens', 0) + 1
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['local_cli_child_intents'] += 1
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['unused_slots_expire'] += 1
        self.reject(data)
        if len(self.data['records']) > 1:
            data = copy.deepcopy(self.data)
            data['records'][0], data['records'][1] = data['records'][1], data['records'][0]
            self.reject(data)

    def test_independent_stability_decoder_cost_and_old_scope_claims_cannot_be_promoted(self):
        for key in ('new_service_authority', 'production_default_changed', 'independent_holdout',
                    'independent_semantic_acceptance', 'generation_stability_verified',
                    'real_person_fidelity_verified', 'old_scopes_reopened', 'old43_scores_replaced',
                    'external_reader_decoder', 'token_matched_tail', 'optimal_tail_selection'):
            data = copy.deepcopy(self.data)
            data[key] = True
            self.reject(data)

    def test_historical_baseline_recovery_is_bound_but_not_guidance_causality(self):
        result=replay.check()['historical_baseline_comparison']
        self.assertTrue(result['same_exact_producer_request'])
        self.assertTrue(result['same_public_questions'])
        self.assertEqual((result['old_card_characters'],result['fresh_baseline_characters']),(252,353))
        self.assertEqual(result['old_fixed_card_result']['correct'],9)
        self.assertEqual(result['fresh_fixed_card_result']['correct'],15)
        self.assertFalse(result['causal_guidance_effect_established'])
        self.assertFalse(result['generation_stability_estimated'])


if __name__ == '__main__':
    unittest.main()
