"""Observed recovery/regression evidence and immutable-denominator damage checks."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('accounted_evidence_test', ROOT / 'scripts/replay_source_accounted.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class SourceAccountedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.p.read(r.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError, TypeError, AssertionError)):
            r.replay(data)

    def test_actual_archive_reconstructs_closed_counters_and_all_case_endpoints_without_models(self):
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            report = r.check()
        backend.assert_not_called()
        self.assertEqual(report['summary'], self.data['status']['scores'])
        self.assertEqual(report['actual_attempts'], self.data['status']['attempt_reservations'])
        self.assertEqual(report['actual_children'], self.data['status']['local_cli_child_intents'])
        self.assertEqual(report['known_usage'], self.data['status']['known_usage'])
        self.assertEqual((report['status'], report['stop'], report['actual_attempts'], report['actual_children']), ('complete', None, 27, 27))
        self.assertEqual(report['known_usage']['total_tokens'], 338516)
        self.assertEqual(report['missing_usage'], 0)
        self.assertEqual(report['invalid_products'], [])
        self.assertEqual(report['skipped'], [])
        self.assertEqual(report['unused_slots_expire'], 0)
        self.assertTrue(report['controls_qualified'])
        self.assertEqual(len(report['all_case_transitions']), 30)
        self.assertEqual(sum(report['transition_counts'].values()), 30)
        self.assertEqual(len(report['historical_seven_loss_targets']), 7)
        self.assertEqual(report['transition_counts'], dict(kept=30, recovered=0, new_loss=0, both_fail=0))
        self.assertTrue(all(t[method]['correct'] for t in report['historical_seven_loss_targets'] for method in r.p.METHODS))
        for method in r.p.METHODS:
            strict = report['summary']['methods'][method]['card']['strict']
            self.assertEqual([strict[k]['planned'] for k in ('joint', 'known', 'unknown')], [30, 13, 17])
            self.assertEqual([strict[k]['correct'] for k in ('joint', 'known', 'unknown')], [30, 13, 17])
            self.assertEqual(report['reference_strata']['derived_known'][method], dict(planned=6, correct=6, missing=0))
        self.assertFalse(report['source_accounting_is_behavioral_endpoint'])

    def test_sources_reference_schema_and_implementation_cannot_change(self):
        for name in ('sources.json', 'reference.private.json', 'queries.public.json', 'static-requests.json', 'implementation-sha256.json'):
            data = copy.deepcopy(self.data)
            data['prepared_files'][name] = {}
            self.reject(data)
        for field in ('scientific_source_ref', 'input_manifest_sha256'):
            data = copy.deepcopy(self.data)
            data[field] = 'foreign'
            self.reject(data)

    def test_changed_raw_choices_or_accounting_are_not_accepted_as_original(self):
        data = copy.deepcopy(self.data)
        record, row = next((record, row) for record in data['records'] if record['kind'] == 'read' and record['state'] == 'completed'
                           for row in r.p.inputs()['rows'] if row['person'] == record['profile'] and row['gold'] != 'U'
                           and all(r.e.parse_answer(record['raw']).get(q) == row['gold'] for q in row['query_ids']))
        answer = r.e.parse_answer(record['raw'])
        answer[row['query_ids'][0]] = 'U'
        record['raw'] = json.dumps(answer, ensure_ascii=False)
        record['raw_value_sha256'] = r.p.digest(record['raw'])
        self.reject(data)
        data = copy.deepcopy(self.data)
        record = next(x for x in data['records'] if x['kind'] == 'extract' and x['method'] == r.p.METHODS[1] and x['state'] == 'completed')
        answer = r.e.parse_answer(record['raw'])
        answer['source_accounting'].pop(next(iter(answer['source_accounting'])))
        record['raw'] = json.dumps(answer, ensure_ascii=False)
        record['raw_value_sha256'] = r.p.digest(record['raw'])
        self.reject(data)

    def test_same_card_request_parent_method_and_artifact_cannot_be_swapped(self):
        for fault in ('request', 'method', 'artifact'):
            data = copy.deepcopy(self.data)
            if fault == 'artifact':
                record = next(x for x in data['records'] if x['kind'] == 'extract' and x['artifact'] is not None)
            else:
                record = next(x for x in data['records'] if x['kind'] == 'read')
            if fault == 'request':
                record['request']['prompt'] += 'foreign material'
                record['request_sha256'] = r.p.digest(record['request'])
                record['execution_record']['request_sha256'] = record['request_sha256']
            elif fault == 'method':
                record['method'] = 'foreign'
                record['execution_record']['method'] = 'foreign'
            else:
                record['artifact']['prompt'] += 'invented'
            self.reject(data)

    def test_nested_known_unknown_denominators_and_numeric_types_cannot_be_rewritten(self):
        for method in r.p.METHODS:
            for metric in ('joint', 'known', 'unknown'):
                data = copy.deepcopy(self.data)
                data['status']['scores']['methods'][method]['card']['strict'][metric]['planned'] -= 1
                self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['scores']['answers_per_primary_case_method_view'] = True
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['status']['local_cli_child_intents'] = False
        self.reject(data)

    def test_counters_usage_closed_scope_and_private_or_unsupported_fields_reject(self):
        for fault in ('usage', 'attempts', 'child', 'open', 'private_root', 'private_record'):
            data = copy.deepcopy(self.data)
            if fault == 'usage': data['status']['known_usage']['total_tokens'] += 1
            elif fault == 'attempts': data['status']['attempt_reservations'] -= 1
            elif fault == 'child': data['records'][0]['local_cli_child_intent'] = 1
            elif fault == 'open': data['status']['scope_closed'] = False
            elif fault == 'private_root': data['human_authorization'] = 'PRIVATE'
            else: data['records'][0]['runtime_path'] = 'PRIVATE'
            self.reject(data)
        for field in r.FALSE_CLAIMS:
            data = copy.deepcopy(self.data)
            data[field] = True
            self.reject(data)

    def test_historical_targets_come_from_original_failed_answers_with_unchanged_gold(self):
        targets = r.historical_losses()
        self.assertEqual(len({(t['person'], t['case']) for t in targets}), 7)
        rows = {(row['person'], row['case']): row for row in r.p.inputs()['rows']}
        for target in targets:
            self.assertEqual(target['historical_four_answers'], ['U'] * 4)
            self.assertEqual(target['gold'], rows[target['person'], target['case']]['gold'])
            self.assertNotEqual(target['gold'], 'U')

    def test_loss_kind_distinguishes_missing_uncertainty_and_invented_choice(self):
        for gold, values, expected in (('A', [None, 'U'], 'missing'), ('A', ['U'] * 8, 'all_unknown_from_known'),
                                      ('A', ['A', 'U'], 'intermittent_unknown_from_known'),
                                      ('A', ['B', 'U'], 'mixed_unknown_and_different_choice'),
                                      ('A', ['B', 'A'], 'different_choice_from_known'),
                                      ('U', ['A', 'U'], 'choice_when_reference_unknown'), ('U', ['U'] * 8, 'retained')):
            self.assertEqual(r.loss_kind(gold, values), expected)
        with self.assertRaises(ValueError):
            r.loss_kind('A', [])


if __name__ == '__main__':
    unittest.main()
