"""Consumed frontier evidence damage controls and independent toy scoring."""
import copy,importlib.util,json
from pathlib import Path
from collections import Counter
import unittest
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'benchmarks/heterogeneous-frontier-v1'
spec=importlib.util.spec_from_file_location('heterogeneous_frontier_check',HERE/'check.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

class HeterogeneousFrontierEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'observed.synthetic.json').read_text(encoding='utf-8'))
 def test_actual_observations_replay_without_service_or_human_claim(self):
  r=bench.check();self.assertEqual((r['full_correct'],r['none_correct']),(80,28));self.assertEqual(r['new_model_calls'],0)
  self.assertLessEqual(r['attempts'],53);self.assertGreaterEqual(r['attempts'],5);self.assertFalse(r['human_fidelity_verified']);self.assertFalse(r['fresh_holdout'])
  for budget,v in r['budgets'].items():self.assertEqual(v['own']['planned'],80);self.assertLessEqual(v['valid_products'],4)
 def test_fixed_budget_counterbalance_and_donor_cycle(self):
  people=list('abcd');plan=bench.plan(people)
  self.assertEqual(len(plan),53);self.assertEqual(Counter(p['group'] for p in plan),{'none':1,'full':4,'extract':12,'own':12,'tail':12,'wrong':12})
  for b in bench.BUDGETS:
   for g in ('extract','own','tail','wrong'):self.assertEqual(sum(s['budget']==b and s['group']==g for s in plan),4)
  self.assertEqual(bench.donors(people),{'a':'b','b':'c','c':'d','d':'a'})
 def test_mock_duplicate_missing_and_order_changes_cannot_pass(self):
  for fault in ('mock','duplicate','missing','order'):
   d=copy.deepcopy(self.data)
   if fault=='mock':d['records'][0]['simulated']=True
   elif fault=='duplicate':d['records'][1]['execution_id']=d['records'][0]['execution_id']
   elif fault=='missing':d['records'].pop()
   else:d['records'][0],d['records'][1]=d['records'][1],d['records'][0]
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_original_responses_usage_and_request_damage_rejected(self):
  for fault in ('response','usage','request','total','missing_usage'):
   d=copy.deepcopy(self.data)
   if fault=='response':d['records'][0]['response']['raw']='{}'
   elif fault=='usage':d['records'][0]['usage']['input_tokens']+=1
   elif fault=='request':d['records'][0]['request']['prompt']+='changed'
   elif fault=='total':d['known_usage']['input_tokens']+=1
   else:d['execution_status']['missing_usage']+=1
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_source_query_and_exported_product_damage_rejected(self):
  for fault in ('source','query','product'):
   d=copy.deepcopy(self.data)
   if fault=='source':d['sources']['h17']['sources'][0]['text']+='changed'
   elif fault=='query':d['queries'].pop()
   else:d['products']['384']['unobserved-owner']={}
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_scope_claims_runtime_and_reference_cannot_silently_change(self):
  for fault in ('claim','runtime','reference','budget'):
   d=copy.deepcopy(self.data)
   if fault=='claim':d['fresh_holdout']=True
   elif fault=='runtime':d['runtime_sha256']['../outside']='0'*64
   elif fault=='reference':d['reference']['rows'][0]['gold']='not offered'
   else:d['budgets']=[300,512,768]
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_independent_toy_budget_missing_unknown_and_donor_gates(self):
  people=list('abcd');rows=[];own={}
  for i,pid in enumerate(people):
   gold='off' if i%2==0 else 'on'
   rows += [{'person':pid,'case':'lamp','cohort':'toy','gold':gold,'query_ids':['qa','qb'],'personal_known':True},
            {'person':pid,'case':'music','cohort':'toy','gold':'U','query_ids':['qc','qd'],'personal_known':False}]
   own[pid]={'qa':gold,'qb':gold,'qc':'U','qd':'U'}
  answers={('full',None,pid):copy.deepcopy(a) for pid,a in own.items()};answers['none',None,'shared']={q:'U' for q in ('qa','qb','qc','qd')}
  for b in bench.BUDGETS:
   for pid,a in own.items():answers['own',b,pid]=copy.deepcopy(a);answers['wrong',b,pid]=copy.deepcopy(own[bench.donors(people)[pid]])
  valid={(b,pid) for b in bench.BUDGETS for pid in people}
  r=bench.summarize(rows,people,answers,valid);self.assertEqual(r['minimum_tested_passing_budget'],384)
  self.assertTrue(all(v['strict_retention'] and v['identity_specificity'] for v in r['budgets'].values()))
  answers['own',384,'a']['qb']='on';answers['own',384,'b']['qc']='on';del answers['own',384,'c']['qa']
  r=bench.summarize(rows,people,answers,valid-{(384,'c')});v=r['budgets']['384']
  self.assertEqual(v['groups']['own']['joint'],{'planned':8,'correct':5,'missing':1});self.assertFalse(v['strict_retention']);self.assertEqual(r['minimum_tested_passing_budget'],512)
  self.assertEqual({e['type'] for e in v['own_losses']},{'known_choice_lost','unknown_not_preserved'})
  self.assertEqual(v['groups']['tail']['joint'],{'planned':8,'correct':0,'missing':8});self.assertFalse(v['normalized_accuracy_gain']['is_likelihood_RIG']);self.assertFalse(r['next_stage_authorized'])
if __name__=='__main__':unittest.main()
