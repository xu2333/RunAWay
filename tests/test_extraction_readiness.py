"""Preserve a one-call observation and the limits of node-coverage diagnostics."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('readiness_archive_tests', ROOT / 'scripts/replay_extraction_readiness.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class ExtractionReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = replay.p.read(replay.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError)):
            replay.replay(data)

    def test_closed_one_call_replays_without_service_and_keeps_omission_visible(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            result = replay.check()
        backend.assert_not_called()
        self.assertEqual((result['attempt_reservations'], result['reader_calls'], result['card_characters']), (1, 0, 252))
        self.assertEqual(result['known_usage']['total_tokens'], 10552)
        self.assertEqual(result['literal_audit']['unreferenced_object_indices'], [1])
        self.assertFalse(result['fidelity_verified'])
        spec = importlib.util.spec_from_file_location('readiness_inventory_test', ROOT / 'scripts/check_graph_object_inventory.py')
        inventory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inventory)
        report = inventory.check()
        self.assertEqual(report['summary'], {'graphs': 9, 'objects': 91, 'nodes': 190, 'unreferenced_objects': 1})
        self.assertEqual(report['new_model_calls'], 0)
        self.assertFalse(report['old_scores_changed'])

    def test_scope_and_input_manifest_substitutions_are_rejected(self):
        for key in ('kind', 'source_input_manifest_sha256'):
            data = copy.deepcopy(self.data)
            data[key] = 'foreign'
            self.reject(data)

    def test_source_request_and_implementation_drift_are_rejected(self):
        for fault in ('source', 'request', 'implementation'):
            data = copy.deepcopy(self.data)
            if fault == 'source':
                data['sources']['a8r']['sources'][0]['text'] += 'changed'
            elif fault == 'request':
                data['record']['request']['prompt'] += ' question or old result'
                data['record']['request_sha256'] = replay.p.digest(data['record']['request'])
            else:
                data['implementation_sha256'] = {}
            self.reject(data)

    def test_changed_raw_or_filled_in_card_cannot_replace_observation(self):
        for fault in ('raw', 'card'):
            data = copy.deepcopy(self.data)
            if fault == 'raw':
                data['record']['raw'] += 'changed'
            else:
                data['record']['card']['prompt'] += '报名也自动。'
            self.reject(data)

    def test_changed_usage_child_or_scope_ledger_is_rejected(self):
        for fault in ('usage', 'child', 'timeout', 'unused', 'unknown'):
            data = copy.deepcopy(self.data)
            if fault == 'usage':
                data['record']['usage']['total_tokens'] += 1
            elif fault == 'child':
                data['record']['local_cli_child_intent'] = False
            elif fault == 'timeout':
                data['record']['timeout_seconds'] = 600
            elif fault == 'unused':
                data['status']['unused_slots_expire'] = 39
            else:
                data['status']['missing_usage'] = 1
            self.reject(data)

    def test_semantic_stability_timeout_cause_and_default_claims_cannot_be_promoted(self):
        for key in ('new_service_authority', 'production_default_changed', 'fidelity_verified',
                    'stability_verified', 'timeout_cause_verified', 'independent_semantic_acceptance',
                    'old_scope_reopened', 'old49_scores_replaced', 'real_person_fidelity_verified'):
            data = copy.deepcopy(self.data)
            data[key] = True
            self.reject(data)

    def test_reader_calls_or_new_intake_rules_are_not_this_grant(self):
        data = copy.deepcopy(self.data)
        data['status']['reader_calls'] = 1
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['intake_protocol']['retry'] = True
        self.reject(data)

    def test_literal_audit_cannot_be_relabelled_and_incidence_is_not_semantics(self):
        data = copy.deepcopy(self.data)
        data['literal_audit']['unreferenced_object_indices'] = []
        self.reject(data)
        answer = json.loads(self.data['record']['raw'])
        duplicated = copy.deepcopy(answer)
        duplicated['nodes'].append(copy.deepcopy(duplicated['nodes'][0]))
        duplicated['nodes'][-1]['id'] = 'offline_extra'
        self.assertEqual(replay.coverage.graph_incidence(duplicated)['unreferenced_object_indices'], [1])
        duplicated['nodes'][-1]['object_index'] = 1  # arbitrary assignment is not evidence of semantic support
        incidence = replay.coverage.graph_incidence(duplicated)
        self.assertEqual(incidence['unreferenced_object_indices'], [])
        self.assertFalse(incidence['semantic_coverage_verified'])
        self.assertFalse(incidence['source_support_verified'])
        self.assertFalse(incidence['automatic_repair'])
        revision = copy.deepcopy(answer)
        revision['nodes'].append({'id': 'offline_revision', 'kind': 'action_revision',
                                  'parent_id': revision['nodes'][0]['id']})
        inherited = replay.coverage.graph_incidence(revision)
        self.assertEqual(inherited['node_indices_by_object'], [[0, 1], []])
        self.assertEqual(inherited['unreferenced_object_indices'], [1])
        revision['nodes'][-1]['parent_id'] = 'future_node'
        with self.assertRaises(ValueError):
            replay.coverage.graph_incidence(revision)
        duplicated['nodes'][0]['object_index'] = True
        with self.assertRaises(ValueError):
            replay.coverage.graph_incidence(duplicated)


if __name__ == '__main__':
    unittest.main()
