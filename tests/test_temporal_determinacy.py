import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import generation, temporal, temporal_concise as codec, temporal_stress as stress
from runaway import temporal_determinacy as diagnostic

ROOT = Path(__file__).resolve().parents[1]


class DeterminacyDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = stress.build_world()
        cls.report, cls.records = diagnostic.calibrate()

    def case(self, member, day, context, order=0):
        person = self.world['people'][member]
        return person, next(c for c in person['cases'] if c['at'] == day and c['context'] == context and c['order'] == order)

    def test_authored_gold_is_independent_and_separates_three_identical_U_answers(self):
        with patch.object(codec, 'resolve', side_effect=AssertionError('Gold must not use decoder')), patch.object(temporal, 'resolve', side_effect=AssertionError('Gold must not use graph')):
            p, c = self.case(1, 12, {'c1': False}); e = diagnostic.authored_expected(p, c)
            self.assertEqual((e['strict_answer'], e['reported_status'], e['completion_answer']), ('U', 'context_unknown', 'A'))
            self.assertEqual(e['possible_outcomes'], [dict(status='chosen', action=stress.ACTIONS[0])])
            p, c = self.case(0, 12, {'c1': False}); e = diagnostic.authored_expected(p, c)
            self.assertEqual(e['completion_answer'], 'U'); self.assertEqual(len(e['possible_outcomes']), 2)
            for day, status in [(9, 'unobserved'), (11, 'conflict')]:
                p, c = self.case(0, day, {'c0': False, 'c1': False}); e = diagnostic.authored_expected(p, c)
                self.assertEqual((e['strict_answer'], e['completion_answer'], e['reported_status']), ('U', 'U', status))
                self.assertEqual(e['possible_outcomes'], [dict(status=status, action=None)])

    def test_exhaustive_completion_respects_negation_false_and_bound(self):
        policy = codec.decode(stress.snapshots(self.world['people'][1]['artifact'])['12'])
        view = diagnostic.completion_view(policy, stress.DOMAIN, {stress.Q: False})
        self.assertEqual((view['strict']['status'], view['completion_action'], view['enumerated_completions']), ('context_unknown', stress.ACTIONS[0], 2))
        policy['domains'][0]['constraint'][0]['when'] = [[stress.P, False], [stress.Q, True]]
        view = diagnostic.completion_view(policy, stress.DOMAIN, {stress.P: False})
        self.assertIsNone(view['completion_action']); self.assertEqual(len(view['possible_outcomes']), 2)
        self.assertEqual(diagnostic.completion_view(policy, stress.DOMAIN, {stress.P: False, stress.Q: True})['completion_action'], stress.ACTIONS[1])
        policy['domains'][0]['constraint'][0]['when'] = [['p'+str(i), True] for i in range(9)]
        with self.assertRaisesRegex(ValueError, 'no sampling'): diagnostic.completion_view(policy, stress.DOMAIN, {})
        for bad in [True, -1, 9]:
            with self.assertRaises(ValueError): diagnostic.completion_view(policy, stress.DOMAIN, {}, max_missing=bad)
        with self.assertRaises(ValueError): diagnostic.completion_view(policy, stress.DOMAIN, {stress.P: None})

    def test_controls_expose_each_choice_only_or_state_only_false_pass(self):
        r = self.report; self.assertTrue(r['passed']); self.assertEqual(r['paired_statistical_units'], 1)
        def scores(name):
            return tuple(r['controls'][name][k]['joint']['correct'] for k in ('strict_choice', 'reported_rule_status', 'completion_choice', 'possible_outcomes'))
        self.assertEqual(scores('dual_program'), (432, 432, 432, 432))
        self.assertEqual(scores('invariant_action_loses_unknown'), (404, 404, 432, 432))
        self.assertEqual(scores('erase_conflict'), (432, 420, 432, 408))
        self.assertEqual(scores('wrong_person'), (368, 432, 312, 304))
        self.assertEqual(scores('drop_completion_branch'), (432, 432, 356, 356))
        self.assertEqual(scores('assume_missing_false'), (340, 328, 368, 356))
        self.assertEqual(r['authored_slices']['current_choice']['unknown_but_determinate'], 4)
        self.assertEqual(r['authored_slices']['joint']['unknown_but_determinate'], 28)

    def test_new_task_projection_preserves_original_world_and_option_order_semantics(self):
        before = copy.deepcopy(self.world); projected = diagnostic.completion_world(self.world)
        self.assertEqual(self.world, before); self.assertNotEqual(projected, self.world)
        for p in self.world['people']:
            for c in p['cases']:
                expected = diagnostic.authored_expected(p, c)
                self.assertEqual(c['options'][expected['completion_answer']], expected['completion_action'])
                if c['expected_status'] == 'chosen': self.assertEqual(expected['completion_answer'], c['gold'])
        row = self.report['controls']['dual_program']['completion_choice']['current_choice']
        self.assertEqual(row['current_scenarios_option_orders_collapsed']['correct'], 18)
        self.assertEqual(row['matched_domain_contrasts']['correct'], 1)

    def test_missing_and_invalid_answers_never_shrink_denominators_or_become_U(self):
        missing = self.report['controls']['missing_snapshot']
        for k in ('strict_choice', 'reported_rule_status', 'completion_choice', 'possible_outcomes'):
            self.assertEqual((missing[k]['joint']['planned'], missing[k]['joint']['missing']), (432, 36))
        records = copy.deepcopy(self.records['program_records']['dual_program'])
        p, c = self.case(0, 12, {'c0': False, 'c1': False}); key = c['public']['id']
        records[p['id']][key]['completion_answer'] = 'invalid'
        scored = diagnostic.score_records(self.world, records)
        self.assertEqual(scored['completion_choice']['current_choice']['invalid_answers'], 1)
        self.assertEqual(scored['completion_choice']['current_choice']['planned'], 36)
        del records[p['id']][key]['possible_outcomes']
        self.assertEqual(diagnostic.score_records(self.world, records)['possible_outcomes']['current_choice']['missing'], 1)

    def test_saved_fixture_replays_with_no_service_or_token_estimates(self):
        with patch.object(generation, 'codex_generate', side_effect=AssertionError('No services')), patch.object(generation, 'run_bounded', side_effect=AssertionError('No commands')):
            report, records = diagnostic.calibrate()
        self.assertEqual((report['external_model_calls'], report['experimental_service_tokens'], report['actual_tokens']), (0, 0, None))
        base = ROOT/'examples/temporal-determinacy'
        self.assertEqual(json.loads((base/'report.synthetic.json').read_text()), report)
        self.assertEqual(json.loads((base/'records.synthetic.json').read_text()), records)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'new'; self.assertEqual(diagnostic.save(out), report)
            with self.assertRaises(FileExistsError): diagnostic.save(out)

    def test_schema_rejects_unexpected_identity_and_invalid_outcome_without_dropping_rows(self):
        for records in [{'unexpected-person': {}}, {'partial-0': {'unexpected-query': {}}}]:
            with self.assertRaises(ValueError): diagnostic.score_records(self.world, records)
        p, c = self.case(1, 12, {'c1': False}); pid = p['id']; key = c['public']['id']
        for row in [dict(extra='hidden'), dict(strict_answer=['A']),
                    dict(possible_outcomes=[]), dict(possible_outcomes=[dict(status='context_unknown', action=None)]),
                    dict(possible_outcomes=[dict(status='conflict', action='invented')]),
                    dict(possible_outcomes=[dict(status='chosen', action=stress.ACTIONS[0])]*2)]:
            with self.assertRaises(ValueError): diagnostic.score_records(self.world, {pid: {key: row}})
        empty = diagnostic.score_records(self.world, {})
        self.assertEqual(empty['completion_choice']['joint']['missing'], 432)
        self.assertEqual(empty['reported_rule_status']['joint']['missing'], 432)
        self.assertEqual(empty['possible_outcomes']['joint']['missing'], 432)


if __name__ == '__main__': unittest.main()
