import unittest
from runaway.decision_audit import readout
from runaway.decision_transfer_world import build_world
from runaway.decision_world import gold
from runaway.decision_world import build_world as previous_world


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.world = build_world()
        self.predictions = {p['id']: {'compact': {c['public']['id']: gold(p['policy'], c) for c in self.world['test']}} for p in self.world['personas']}

    def test_failure_inclusive_and_observed_errors_are_distinct(self):
        del self.predictions['t01']['compact']
        r = readout(self.world, self.predictions, 'compact')
        self.assertEqual(r['primary']['end_to_end_rate'], .5)
        self.assertEqual(r['primary']['available_rate'], 1)
        self.assertEqual(r['current_instructions']['missing'], 4)
        self.assertEqual(r['current_instructions']['observed_violations'], 0)
        self.assertEqual(r['twins']['missing'], 3)
        self.assertIsNone(readout(self.world, self.predictions, 'not_run')['primary']['end_to_end_rate'])

    def test_abstention_is_observed_but_does_not_satisfy_instruction(self):
        c = next(c for c in self.world['test'] if c['kind'] == 'explicit_request')
        self.predictions['t01']['compact'][c['public']['id']] = 'unknown'
        r = readout(self.world, self.predictions, 'compact')
        self.assertEqual(r['current_instructions']['observed_violations'], 1)
        self.assertEqual(r['current_instructions']['missing'], 0)

    def test_flip_and_stable_pairs_both_required(self):
        r = readout(self.world, self.predictions, 'compact')
        self.assertGreater(r['counterfactual_required_flip']['planned'], 0)
        self.assertGreater(r['counterfactual_required_stable']['planned'], 0)
        self.assertEqual(r['counterfactual_required_flip']['available_rate'], 1)
        self.assertEqual(r['twins']['correct'], 3)

    def test_new_cohort_and_cases_disjoint_from_consumed_world(self):
        old = previous_world()
        self.assertTrue(all(p['policy'] not in [p['policy'] for p in old['personas']] for p in self.world['personas']))
        self.assertFalse({c['public']['id'] for c in old['training']+old['test']} & {c['public']['id'] for c in self.world['training']+self.world['test']})


if __name__ == '__main__': unittest.main()
