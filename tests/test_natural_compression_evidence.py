"""Consumed-observation integrity and independent toy retention controls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'benchmarks/natural-compression-v1'
spec = importlib.util.spec_from_file_location('natural_compression_check', HERE/'check.py')
bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)


class NaturalCompressionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((HERE/'observed.synthetic.json').read_text(encoding='utf-8'))
        cls.controls = json.loads((HERE.parent/'natural-controls-v1/observed.synthetic.json').read_text(encoding='utf-8'))

    def test_actual_results_reproduce_without_service_or_human_claim(self):
        report = bench.check()
        self.assertEqual([report[k] for k in ('own_correct','tail_correct','wrong_target_correct','wrong_donor_correct')], [56,38,30,56])
        self.assertEqual(report['known_tokens'], 189065)
        self.assertEqual(report['new_model_calls'], 0)
        self.assertFalse(report['human_fidelity_verified'])
        self.assertFalse(report['fresh_holdout'])

    def test_missing_duplicate_mock_and_order_drift_are_rejected(self):
        for fault in ('missing','duplicate','mock','order'):
            data = copy.deepcopy(self.data)
            if fault == 'missing': data['records'].pop()
            elif fault == 'duplicate': data['records'][1]['execution_id'] = data['records'][0]['execution_id']
            elif fault == 'mock': data['records'][0]['simulated'] = True
            else: data['records'][4],data['records'][5] = data['records'][5],data['records'][4]
            with self.subTest(fault=fault), self.assertRaises(ValueError): bench.replay(data, self.controls)

    def test_public_card_changed_or_overbudget_is_not_relabelled_valid(self):
        for fault in ('text','length'):
            data = copy.deepcopy(self.data)
            if fault == 'text': data['products']['n31']['prompt'] += 'guess'
            else: data['products']['n31']['characters'] = 769
            with self.subTest(fault=fault), self.assertRaises(ValueError): bench.replay(data, self.controls)

    def test_actual_response_usage_and_material_binding_damage_is_rejected(self):
        for fault in ('response','usage','request','donor','total'):
            data = copy.deepcopy(self.data)
            if fault == 'response': data['records'][0]['response']['raw'] = '{}'
            elif fault == 'usage': data['records'][0]['usage']['input_tokens'] += 1
            elif fault == 'total': data['known_usage']['input_tokens'] += 1
            elif fault == 'request': data['records'][4]['request']['prompt'] += 'changed'
            else:
                wrong = next(r for r in data['records'] if r['group']=='wrong')
                wrong['person'] = 'n31'
            with self.subTest(fault=fault), self.assertRaises(ValueError): bench.replay(data, self.controls)

    def test_historical_controls_and_study_claims_cannot_silently_change(self):
        controls = copy.deepcopy(self.controls); controls['sources']['n31']['sources'][0]['text'] += 'changed'
        with self.assertRaises(ValueError): bench.replay(self.data, controls)
        for field in ('fresh_holdout','human_fidelity_verified','prior_controls_rerun'):
            data = copy.deepcopy(self.data); data[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError): bench.replay(data, self.controls)

    def test_runtime_inventory_damage_is_rejected(self):
        for fault in ('missing','hash','path'):
            data = copy.deepcopy(self.data)
            key = next(iter(data['runtime_sha256']))
            if fault == 'missing': del data['runtime_sha256'][key]
            elif fault == 'hash': data['runtime_sha256'][key] = '0'*64
            else: data['runtime_sha256']['../outside'] = data['runtime_sha256'].pop(key)
            with self.subTest(fault=fault), self.assertRaises(ValueError): bench.replay(data, self.controls)

    def test_independent_toy_scoring_missing_unknown_and_wrong_donor(self):
        people = ['a','b','c','d']; rows = []; own = {}
        for i,p in enumerate(people):
            gold = 'on' if i%2 else 'off'
            rows += [{'person':p,'case':'lamp','cohort':'toy','gold':gold,'query_ids':['qa','qb'],'personal_known':True},
                     {'person':p,'case':'outside','cohort':'toy','gold':'U','query_ids':['qc','qd'],'personal_known':False}]
            own[p] = {'qa':gold,'qb':gold,'qc':'U','qd':'U'}
        baseline = {'groups':{'full':bench.prior.counts(rows,own),'none':bench.prior.counts(rows,{p:{q:'U' for q in own[p]} for p in people})},'full_qualified':True}
        wrong = {p:own[donor] for p,donor in bench.donor_map(people).items()}
        answers = {'own':own,'wrong':wrong}
        report = bench.summarize(rows,answers,people,baseline,4)
        self.assertTrue(report['strict_retention']); self.assertTrue(report['identity_specificity'])
        self.assertEqual(report['groups']['wrong']['known']['correct'],0)
        self.assertEqual(report['groups']['wrong_against_donor']['known']['correct'],4)
        self.assertEqual(report['groups']['tail']['joint'],{'planned':8,'correct':0,'missing':8})
        damaged = copy.deepcopy(answers)
        damaged['own']['a']['qb'] = 'on'  # One wrong rotation makes a cell wrong.
        damaged['own']['b']['qc'] = 'off'  # Unknown guessing must fail separately.
        del damaged['own']['c']['qa']
        report = bench.summarize(rows,damaged,people,baseline,3)
        self.assertFalse(report['strict_retention']); self.assertFalse(report['identity_specificity'])
        self.assertEqual(report['groups']['own']['joint'],{'planned':8,'correct':5,'missing':1})
        self.assertEqual({e['type'] for e in report['own_losses']},{'known_choice_lost','unknown_not_preserved'})
        self.assertFalse(report['normalized_accuracy_gain']['is_likelihood_RIG'])
        self.assertFalse(report['next_stage_authorized'])


if __name__ == '__main__': unittest.main()
