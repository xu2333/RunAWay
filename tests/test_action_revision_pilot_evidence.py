"""Damage controls on the actual one-card pilot; no model invocations."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('graph_pilot_evidence_tests', ROOT / 'scripts/replay_action_revision_pilot.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)


class GraphPilotEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = a.engine.plan.read(a.DEFAULT)

    def test_closed_ledger_replays_one_producer_and_four_answer_endpoint(self):
        r = a.check()
        self.assertLessEqual(r['actual_original_attempts'], 5)
        self.assertEqual((r['new_model_calls'], r['answers_per_case'], r['generated_cards_planned']), (0, 4, 1))
        self.assertFalse(r['fresh_generation_stability_test'])
        scores = r['scores']['strict_both_reads']
        self.assertEqual((scores['joint']['planned'], scores['known']['planned'], scores['unknown']['planned']), (40, 24, 16))
        self.assertTrue(all(len(x['reads_orders']) == 2 for x in r['failed_or_missing_cases']))

    def test_source_reference_requests_raw_and_parent_cannot_drift(self):
        for fault in ('source', 'reference', 'request', 'raw', 'parent'):
            d = copy.deepcopy(self.data)
            if fault == 'source': d['sources']['h93']['sources'][0]['text'] += 'changed'
            elif fault == 'reference': d['reference_rows'][0]['gold'] = 'changed'
            elif fault == 'request':
                d['records'][0]['request']['prompt'] += 'changed'
                d['records'][0]['request_sha256'] = a.engine.plan.digest(d['records'][0]['request'])
            elif fault == 'raw':
                r = next(x for x in d['records'] if x['raw_present']); r['raw'] += 'changed'
                r['raw_value_sha256'] = a.engine.plan.digest(r['raw'])
            else: d['records'][-1]['generation'] = 1
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_gates_scores_missing_and_attempt_removal_cannot_improve_results(self):
        for fault in ('gate', 'score', 'missing', 'remove', 'artifact'):
            d = copy.deepcopy(self.data)
            if fault == 'gate': d['status']['control_gates']['h93']['qualified'] = False
            elif fault == 'score': d['status']['scores']['strict_both_reads']['joint']['planned'] = 39
            elif fault == 'missing': d['status']['scores']['strict_both_reads']['joint']['missing'] += 1
            elif fault == 'artifact':
                r = next((x for x in d['records'] if 'card' in x), d['records'][0])
                r['card'] = {'prompt': 'borrowed', 'characters': 8}
            else:
                d['records'].pop(); d['status']['attempt_reservations'] -= 1
                d['status']['unused_slots_expire'] += 1; d['status']['local_cli_child_intents'] -= 1
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_usage_and_frozen_implementation_cannot_change(self):
        for fault in ('usage', 'subset', 'implementation'):
            d = copy.deepcopy(self.data)
            if fault == 'implementation': d['implementation_sha256'] = {}
            else:
                row = next(r for r in d['records'] if r['usage_rows'])['usage_rows'][0]
                if fault == 'usage': del row['input_tokens']
                else: row['cached_input_tokens'] = row['input_tokens']+1
            with self.subTest(fault=fault), self.assertRaises(ValueError): a.replay(d)

    def test_one_card_is_not_a_stability_holdout_or_new_reference_result(self):
        for key, value in [('answers_per_case', 8), ('generated_cards_planned', 2),
                ('fresh_generation_stability_test', True), ('independent_reference_acceptance', True),
                ('validates_j16_or_development', True), ('independent_holdout', True), ('production_default_changed', True)]:
            d = copy.deepcopy(self.data); d[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): a.replay(d)


if __name__ == '__main__': unittest.main()
