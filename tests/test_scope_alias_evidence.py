"""Sealed binding-stress evidence, full denominators and failure-localization guards."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binding_evidence_test', ROOT / 'scripts/replay_scope_alias.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
trace_spec = importlib.util.spec_from_file_location('binding_evidence_trace', ROOT / 'scripts/inspect_scope_alias.py')
t = importlib.util.module_from_spec(trace_spec)
trace_spec.loader.exec_module(t)


class ScopeAliasEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.p.read(r.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError, TypeError, AssertionError)):
            r.replay(data)

    def test_closed_observations_reconstruct_every_budget_cell_without_model_calls(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            report = r.check()
        backend.assert_not_called()
        self.assertEqual(report['actual_attempts'], self.data['status']['attempt_reservations'])
        self.assertEqual(report['actual_children'], self.data['status']['local_cli_child_intents'])
        self.assertEqual(report['known_usage'], self.data['status']['known_usage'])
        self.assertEqual(report['summary'], self.data['status']['scores'])
        self.assertEqual(len(report['all_case_transitions']), 64)
        for budget in r.p.BUDGETS:
            self.assertEqual(sum(report['paired_transitions_by_budget'][str(budget)].values()), 64)
            for generation in (0, 1):
                self.assertEqual(sum(report['paired_transitions_by_budget_generation'][str(budget)][str(generation)].values()), 64)
            for method in r.p.METHODS:
                non_alias = report['non_alias_by_budget'][str(budget)][method]
                self.assertEqual([non_alias[key]['planned'] for key in ('joint', 'known', 'unknown')], [48, 24, 24])
                cell = report['summary']['methods'][method][str(budget)]
                self.assertEqual([cell['strict'][key]['planned'] for key in ('joint', 'known', 'unknown')], [64, 40, 24])
                self.assertEqual(cell['old_alias']['joint']['planned'], 16)
                self.assertEqual(cell['late_revision']['joint']['planned'], 16)
        self.assertFalse(report['literal_presence_is_semantic_coverage'])

    def test_exact_sources_questions_references_and_prepared_implementation_cannot_change(self):
        for name in ('sources.json', 'queries.public.json', 'reference.private.json', 'author-evidence.private.json',
                     'calibration.private.json', 'implementation-sha256.json', 'slots.json'):
            data = copy.deepcopy(self.data)
            data['prepared_files'][name] = {}
            self.reject(data)
        for key in ('scientific_source_ref', 'input_manifest_sha256'):
            data = copy.deepcopy(self.data)
            data[key] = 'foreign'
            self.reject(data)

    def test_changed_raw_values_or_valid_full_control_answers_cannot_replace_original(self):
        data = copy.deepcopy(self.data)
        record = next(x for x in data['records'] if x['raw_present'])
        record['raw'] += 'changed'
        self.reject(data)
        data = copy.deepcopy(self.data)
        pair = next(((record, row) for record in data['records'] if record['kind'] in ('read', 'full') and record['state'] == 'completed'
                     for row in r.p.inputs()['rows'] if row['person'] == record['profile'] and row['gold'] != 'U'
                     and all(r.e.parse_answer(record['raw']).get(q) == row['gold'] for q in row['query_ids'])), None)
        if pair is None:
            self.assertTrue(data['status']['stop'])
            return
        record, row = pair
        answer = r.e.parse_answer(record['raw'])
        answer[row['query_ids'][0]] = 'U'
        record['raw'] = json.dumps(answer, ensure_ascii=False)
        record['raw_value_sha256'] = r.p.digest(record['raw'])
        self.reject(data)

    def test_budget_method_parent_and_request_routing_remain_original(self):
        for fault in ('budget', 'method', 'request'):
            data = copy.deepcopy(self.data)
            record = next((x for x in data['records'] if x['kind'] in ('read', 'extract')), data['records'][0])
            if fault == 'request':
                record['request']['prompt'] += 'foreign material'
                record['request_sha256'] = r.p.digest(record['request'])
                record['execution_record']['request_sha256'] = record['request_sha256']
            else:
                record[fault] = 384 if fault == 'budget' else 'foreign'
                record['execution_record'][fault] = record[fault]
            self.reject(data)

    def test_nested_denominators_numeric_types_and_usage_counters_cannot_shrink(self):
        for method in r.p.METHODS:
            for budget in r.p.BUDGETS:
                data = copy.deepcopy(self.data)
                data['status']['scores']['methods'][method][str(budget)]['strict']['joint']['planned'] -= 1
                self.reject(data)
        for fault in ('boolean', 'usage', 'attempt', 'child', 'open'):
            data = copy.deepcopy(self.data)
            if fault == 'boolean': data['status']['scores']['known_per_cell'] = True
            elif fault == 'usage': data['status']['known_usage']['total_tokens'] = data['status']['known_usage'].get('total_tokens', 0) + 1
            elif fault == 'attempt': data['status']['attempt_reservations'] -= 1
            elif fault == 'child': data['records'][0]['local_cli_child_intent'] = 1
            else: data['status']['scope_closed'] = False
            self.reject(data)

    def test_private_fields_or_unsupported_semantic_claims_are_rejected(self):
        for key in r.FALSE_CLAIMS:
            data = copy.deepcopy(self.data)
            data[key] = True
            self.reject(data)
        data = copy.deepcopy(self.data)
        data['human_authorization'] = 'PRIVATE'
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['records'][0]['runtime_path'] = 'PRIVATE'
        self.reject(data)

    def test_availability_is_not_mislabeled_as_observed_regression_or_recovery(self):
        good = dict(correct=True, missing=False)
        wrong = dict(correct=False, missing=False)
        absent = dict(correct=False, missing=True)
        for before, after, expected in ((good, good, 'kept'), (wrong, good, 'recovered'),
                                        (good, wrong, 'new_observed_loss'), (wrong, wrong, 'both_observed_fail'),
                                        (absent, good, 'baseline_missing'), (good, absent, 'candidate_missing'),
                                        (absent, absent, 'both_missing')):
            self.assertEqual(r.transition(before, after), expected)

    def test_loss_kind_preserves_missing_unknown_and_wrong_choice(self):
        for gold, values, expected in (('A', [None, 'U'], 'missing'), ('A', ['U'] * 8, 'all_unknown_from_known'),
                                      ('A', ['A', 'U'], 'intermittent_unknown_from_known'),
                                      ('A', ['B', 'U'], 'mixed_unknown_and_different_choice'),
                                      ('A', ['B', 'A'], 'different_choice_from_known'),
                                      ('U', ['A', 'U'], 'choice_when_reference_unknown')):
            self.assertEqual(r.loss_kind(gold, values), expected)
        with self.assertRaises(ValueError):
            r.loss_kind('A', [])

    def test_joint_failures_cannot_hide_opposite_generation_recovery_and_new_loss(self):
        cell = {'gold': 'A',
                r.p.METHODS[0]: {'answers_by_generation': [['A'] * 4, ['U'] * 4]},
                r.p.METHODS[1]: {'answers_by_generation': [['U'] * 4, ['A'] * 4]}}
        self.assertEqual(r.generation_transition(cell, 0), 'new_observed_loss')
        self.assertEqual(r.generation_transition(cell, 1), 'recovered')
        self.assertEqual(r.transition(dict(correct=False, missing=False), dict(correct=False, missing=False)), 'both_observed_fail')

    def test_case_trace_keeps_original_episode_roles_graph_card_and_two_read_orders(self):
        report = r.replay(self.data)
        cell = report['all_case_transitions'][0]
        method = r.p.METHODS[0]
        before = r.p.digest(self.data)
        value = t.trace(self.data, report, cell['person'], cell['case'], method, cell['budget'], 0)
        self.assertEqual(len(value['complete_related_source_episodes']), 12)
        self.assertEqual({s['role'] for s in value['complete_related_source_episodes']}, {'user', 'assistant', 'tool', 'context'})
        self.assertEqual(len(value['public_queries']), 2)
        self.assertEqual(value['answers_by_read_and_order'], [cell[method]['answers_by_generation'][0][:2], cell[method]['answers_by_generation'][0][2:]])
        if value['parent_slot'] is not None:
            parent = next(x for x in self.data['records'] if x['slot'] == value['parent_slot'])
            self.assertEqual(value['original_raw_response'], parent['raw'] if parent['raw_present'] else None)
            try:
                graph = r.e.parse_answer(parent['raw']) if parent['raw_present'] else None
            except (ValueError, TypeError):
                graph = None
            self.assertEqual(value['original_raw_graph'], graph)
            self.assertEqual(value['original_public_card'], parent['artifact']['prompt'] if parent['artifact'] else None)
        self.assertEqual(value['new_service_calls'], 0)
        self.assertTrue(value['no_automatic_semantic_cause_claim'])
        self.assertEqual(r.p.digest(self.data), before)

    def test_case_trace_rejects_nonexistent_sources_cases_or_parent_coordinates(self):
        report = r.analyze(self.data, self.data['status'])
        cell = report['all_case_transitions'][0]
        args = [cell['person'], cell['case'], r.p.METHODS[0], cell['budget'], 0]
        for index, foreign in enumerate(('foreign', 'foreign', 'foreign', 384, 2)):
            changed = args[:]
            changed[index] = foreign
            with self.assertRaises(ValueError):
                t.trace(self.data, report, *changed)


if __name__ == '__main__':
    unittest.main()
