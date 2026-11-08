"""Sealed source-only768 observations and loss traces; no fresh model evaluation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


r = load('direct768_observed_tests', ROOT / 'scripts/replay_fresh_direct768.py')
t = load('direct768_trace_tests', ROOT / 'scripts/inspect_fresh_direct768.py')


class FreshDirect768EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.p.read(r.DEFAULT)
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No new model call')) as backend:
            cls.report = r.check()
        backend.assert_not_called()

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError, TypeError, AssertionError)): r.replay(data)

    def test_closed_archive_reconstructs_full384_case_endpoints_usage_and_counters(self):
        report = self.report
        self.assertEqual(report['summary'], self.data['status']['scores'])
        self.assertEqual(report['actual_attempts'], self.data['status']['attempt_reservations'])
        self.assertEqual(report['known_usage'], self.data['status']['known_usage'])
        self.assertEqual(report['actual_children'], self.data['status']['local_cli_child_intents'])
        self.assertEqual(len(report['all_case_transitions']), 384)
        self.assertEqual(sum(report['paired_transitions_by_budget']['768'].values()), 384)
        for g in ('0', '1'): self.assertEqual(sum(report['paired_transitions_by_budget_generation']['768'][g].values()), 384)
        for method in r.p.METHODS:
            cell = report['summary']['methods'][method]['768']
            self.assertEqual([cell['strict'][k]['planned'] for k in ('joint', 'known', 'unknown')], [384, 168, 216])
            self.assertEqual([cell['per_family'][f]['joint']['planned'] for f in ('strict', 'released')], [192, 192])
            self.assertEqual([v['joint']['planned'] for v in cell['cohorts'].values()], [24] * 16)
            subset = report['condition_boundary_cases_by_budget']['768'][method]
            self.assertEqual([subset[k]['planned'] for k in ('joint', 'known', 'unknown')], [288, 144, 144])

    def test_sources_queries_author_navigation_references_and_implementation_are_exact(self):
        for name in r.p.FILES:
            data = copy.deepcopy(self.data); data['prepared_files'][name] = {}; self.reject(data)
        for key in ('scientific_source_ref', 'input_manifest_sha256'):
            data = copy.deepcopy(self.data); data[key] = 'foreign'; self.reject(data)

    def test_original_raw_cannot_be_changed_even_with_updated_value_hash(self):
        rec = next((x for x in self.data['records'] if x['raw_present']), None)
        if rec is None:
            self.assertTrue(self.data['status']['stop']); return
        data = copy.deepcopy(self.data); data['records'][0]['raw'] += 'changed'; self.reject(data)
        pair = next(((x, row) for x in self.data['records'] if x['kind'] in ('full', 'read') and x['state'] == 'completed'
            for row in r.p.inputs()['rows'] if row['person'] == x['profile'] and row['gold'] != 'U'
            and all(r.e.parse_answer(x['raw']).get(q) == row['gold'] for q in row['query_ids'])), None)
        if pair is None: self.assertTrue(self.data['status']['stop']); return
        rec, row = pair; data = copy.deepcopy(self.data); rec = next(x for x in data['records'] if x['slot'] == rec['slot'])
        value = r.e.parse_answer(rec['raw']); value[row['query_ids'][0]] = 'U'
        rec['raw'] = json.dumps(value, ensure_ascii=False); rec['raw_value_sha256'] = r.p.digest(rec['raw']); self.reject(data)

    def test_person_method_budget_generation_and_request_routing_cannot_change(self):
        for fault in ('profile', 'method', 'budget', 'generation', 'request'):
            data = copy.deepcopy(self.data)
            rec = next((x for x in data['records'] if x['kind'] in ('extract', 'read')), data['records'][0])
            if fault == 'request':
                rec['request']['prompt'] += 'extra source'; rec['request_sha256'] = r.p.digest(rec['request'])
                rec['execution_record']['request_sha256'] = rec['request_sha256']
            else: rec[fault] = 'foreign'; rec['execution_record'][fault] = 'foreign'
            self.reject(data)

    def test_fixed_denominators_boolean_child_and_usage_are_not_silently_accepted(self):
        for method in r.p.METHODS:
            data = copy.deepcopy(self.data); data['status']['scores']['methods'][method]['768']['strict']['joint']['planned'] -= 1
            self.reject(data)
        for fault in ('attempt', 'child', 'boolean', 'usage', 'open'):
            data = copy.deepcopy(self.data)
            if fault == 'attempt': data['status']['attempt_reservations'] -= 1
            elif fault == 'child': data['records'][0]['local_cli_child_intent'] = 1
            elif fault == 'boolean': data['status']['local_cli_child_intents'] = True
            elif fault == 'usage': data['status']['known_usage']['total_tokens'] = data['status']['known_usage'].get('total_tokens', 0) + 1
            else: data['status']['scope_closed'] = False
            self.reject(data)

    def test_private_fields_and_unsupported_semantic_or_population_claims_are_rejected(self):
        for key in r.FALSE_CLAIMS:
            data = copy.deepcopy(self.data); data[key] = True; self.reject(data)
        data = copy.deepcopy(self.data); data['human_authorization'] = 'private'; self.reject(data)
        data = copy.deepcopy(self.data); data['records'][0]['machine_path'] = 'private'; self.reject(data)

    def test_reconstructed_model_card_cannot_be_swapped_or_repaired(self):
        rec = next((x for x in self.data['records'] if x['artifact']), None)
        if rec is None:
            self.assertTrue(self.data['status']['stop'] or self.data['status']['invalid_products']); return
        data = copy.deepcopy(self.data)
        next(x for x in data['records'] if x['slot'] == rec['slot'])['artifact']['prompt'] += 'repaired'
        self.reject(data)

    def test_missing_is_separate_from_observed_loss_and_recovery(self):
        good = dict(correct=True, missing=False); wrong = dict(correct=False, missing=False); absent = dict(correct=False, missing=True)
        for a, b, label in ((good, good, 'kept'), (wrong, good, 'recovered'), (good, wrong, 'new_observed_loss'),
            (wrong, wrong, 'both_observed_fail'), (absent, good, 'baseline_missing'),
            (good, absent, 'candidate_missing'), (absent, absent, 'both_missing')):
            self.assertEqual(r.transition(a, b), label)

    def test_missing_unknown_false_certainty_and_wrong_choice_have_distinct_loss_kinds(self):
        for gold, answers, label in (('a', [None, 'U'], 'missing'), ('a', ['U'] * 8, 'all_unknown_from_known'),
            ('a', ['a', 'U'], 'intermittent_unknown_from_known'), ('a', ['b', 'U'], 'mixed_unknown_and_different_choice'),
            ('a', ['a', 'b'], 'different_choice_from_known'), ('U', ['a', 'U'], 'choice_when_reference_unknown')):
            self.assertEqual(r.loss_kind(gold, answers), label)

    def test_opposite_generation_regressions_and_recoveries_remain_visible(self):
        cell = dict(gold='a')
        cell[r.p.METHODS[0]] = dict(answers_by_generation=[['a'] * 4, ['U'] * 4])
        cell[r.p.METHODS[1]] = dict(answers_by_generation=[['U'] * 4, ['a'] * 4])
        self.assertEqual(r.generation_transition(cell, 0), 'new_observed_loss')
        self.assertEqual(r.generation_transition(cell, 1), 'recovered')
        value = dict(name='语法', tagline='夹具', unknowns=['其它未知'], groups=[dict(scope='范围'+str(i), rules=[dict(question='方法', requires=['明确允许本项目离线演练并已确认范围','材料齐备'], choose='方法甲',priority=0)]) for i in range(3)])
        plain = r.p.candidate.dense._render(value)
        common = r.p.candidate.factor.factor(plain, 4096)['prompt']
        self.assertEqual(r.layout_scheme(plain), 'dense')
        self.assertEqual(r.layout_scheme(common), 'common_then_dense')

    def test_source_trace_keeps_all_roles_original_graph_and_each_answer_order(self):
        cell = self.report['all_case_transitions'][0]; method = r.p.METHODS[0]
        before = r.p.digest(self.data)
        value = t.trace(self.data, self.report, cell['person'], cell['case'], method, 768, 0)
        self.assertEqual(len(value['complete_related_source_episodes']), 9)
        self.assertEqual({s['role'] for s in value['complete_related_source_episodes']}, {'user', 'assistant', 'tool', 'context'})
        self.assertEqual(len(value['public_queries']), 2)
        self.assertEqual(value['answers_by_read_and_order'], [cell[method]['answers_by_generation'][0][:2], cell[method]['answers_by_generation'][0][2:]])
        self.assertEqual(value['new_service_calls'], 0)
        self.assertEqual(r.p.digest(self.data), before)

    def test_valid_trace_preserves_all_compiled_fields_and_invalid_coordinates_fail(self):
        rec = next((x for x in self.data['records'] if x['artifact']), None)
        if rec is not None:
            cell = next(c for c in self.report['all_case_transitions'] if c['person'] == rec['profile'])
            value = t.trace(self.data, self.report, rec['profile'], cell['case'], rec['method'], 768, rec['generation'])
            self.assertEqual(value['original_public_card'], rec['artifact']['prompt'])
            self.assertIsNotNone(value['deterministically_resolved_graph'])
            self.assertIsNotNone(value['compiled_active_rows'])
            self.assertLessEqual(len(value['original_public_card']), 768)
        for args in (('foreign', '0_boundary', r.p.METHODS[0], 768, 0),
            (r.p.PROFILES[0], 'foreign', r.p.METHODS[0], 768, 0),
            (r.p.PROFILES[0], '0_boundary', r.p.METHODS[0], 768, True)):
            with self.assertRaises(ValueError): t.trace(self.data, self.report, *args)


if __name__ == '__main__': unittest.main()
