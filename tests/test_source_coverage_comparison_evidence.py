"""Damage controls for actual consumed evidence and independent toy stage gates."""
import copy, importlib.util, json
from pathlib import Path
from collections import Counter
import unittest
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'benchmarks/source-coverage-comparison-v1'
spec=importlib.util.spec_from_file_location('source_coverage_comparison_check',HERE/'check.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

class SourceCoverageEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'observed.synthetic.json').read_text(encoding='utf-8'))
 def test_actual_observations_replay_without_service_or_human_claim(self):
  r=bench.check();self.assertEqual((r['full_correct'],r['none_correct']),(80,28))
  self.assertEqual(r['new_model_calls'],0);self.assertLessEqual(r['attempts'],45)
  self.assertFalse(r['human_fidelity_verified']);self.assertFalse(r['fresh_holdout'])
  for v in r['variants'].values():self.assertEqual(v['own']['planned'],80);self.assertLessEqual(v['valid_products'],4)
 def test_fixed_stages_budget_counterbalance_and_donor_cycle(self):
  people=list('abcd');plan=bench.plan(people)
  self.assertEqual(len(plan),45)
  self.assertEqual(Counter(p['group'] for p in plan),{'none':1,'full':4,'inventory':4,'audit':4,'extract':8,'own':8,'tail':8,'wrong':8})
  for v in bench.VARIANTS:
   for g in ('extract','own','tail','wrong'):self.assertEqual(sum(s['variant']==v and s['group']==g for s in plan),4)
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
 def test_source_query_and_exported_artifact_damage_rejected(self):
  for fault in ('source','query','artifact'):
   d=copy.deepcopy(self.data)
   if fault=='source':d['sources']['h17']['sources'][0]['text']+='changed'
   elif fault=='query':d['queries'].pop()
   else:d['artifacts'].append({'group':'inventory','person':'unobserved','variant':'coverage-v1','artifact':{}})
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_scope_claims_runtime_and_reference_cannot_silently_change(self):
  for fault in ('claim','runtime','reference','budget'):
   d=copy.deepcopy(self.data)
   if fault=='claim':d['fresh_holdout']=True
   elif fault=='runtime':d['runtime_sha256']['../outside']='0'*64
   elif fault=='reference':d['reference']['rows'][0]['gold']='not offered'
   else:d['budget_characters']=768
   with self.subTest(fault=fault),self.assertRaises(ValueError):bench.replay(d)
 def test_inventory_and_skipped_dependency_damage_rejected(self):
  d=copy.deepcopy(self.data)
  r=next(r for r in d['records'] if r['group']=='inventory' and 'artifact' in r)
  r['artifact']['ledger']['units'][0]['content']+='changed'
  with self.assertRaises(ValueError):bench.replay(d)
  d=copy.deepcopy(self.data);d['execution_status']['skipped'].append({'slot':1,'group':'none','person':'shared','variant':None,'budget':None,'reason':'invented'})
  with self.assertRaises(ValueError):bench.replay(d)
 def test_audit_gate_flag_and_stage_cost_damage_rejected(self):
  d=copy.deepcopy(self.data)
  r=next(r for r in d['records'] if r['group']=='audit' and 'artifact' in r)
  r['audit_flagged']=not bool(r.get('audit_flagged'))
  with self.assertRaises(ValueError):bench.replay(d)
  d=copy.deepcopy(self.data);next(iter(d['stage_costs'].values()))['local_calls']+=1
  with self.assertRaises(ValueError):bench.replay(d)
 def test_toy_partial_and_flagged_audit_cannot_pass_even_with_perfect_readers(self):
  people=list('abcd');rows=[];own={};artifacts={}
  for i,pid in enumerate(people):
   gold='off' if i%2==0 else 'on'
   rows += [{'person':pid,'case':'lamp','cohort':'toy','gold':gold,'query_ids':['qa','qb'],'personal_known':True},
            {'person':pid,'case':'music','cohort':'toy','gold':'U','query_ids':['qc','qd'],'personal_known':False}]
   own[pid]={'qa':gold,'qb':gold,'qc':'U','qd':'U'}
   artifacts['inventory',pid,'coverage-v1']={}
   artifacts['audit',pid,'coverage-v1']={'audit':{'clear_for_compression':True}}
   for v in bench.VARIANTS:artifacts['extract',pid,v]={'partial':False,'complete_accounting':True if v=='coverage-v1' else None}
  answers={('full',None,pid):copy.deepcopy(a) for pid,a in own.items()}
  answers['none',None,'shared']={q:'U' for q in ('qa','qb','qc','qd')}
  for v in bench.VARIANTS:
   for pid,a in own.items():
    answers['own',v,pid]=copy.deepcopy(a)
    answers['wrong',v,pid]=copy.deepcopy(own[bench.donors(people)[pid]])
  r=bench.summarize(rows,people,answers,artifacts)
  self.assertEqual(r['passing_variants'],list(bench.VARIANTS))
  artifacts['extract','a','coverage-v1'].update(partial=True,complete_accounting=False)
  r=bench.summarize(rows,people,answers,artifacts)
  self.assertEqual(r['variants']['coverage-v1']['groups']['own']['joint']['correct'],8)
  self.assertEqual(r['variants']['coverage-v1']['partial_products'],1)
  self.assertEqual(r['passing_variants'],['grouped-v1'])
  artifacts['extract','a','coverage-v1'].update(partial=False,complete_accounting=True)
  artifacts['audit','b','coverage-v1']['audit']['clear_for_compression']=False
  r=bench.summarize(rows,people,answers,artifacts)
  self.assertEqual(r['pipeline_stages']['audit_flagged'],1)
  self.assertEqual(r['passing_variants'],['grouped-v1'])
  self.assertFalse(r['inventory_semantic_completeness_verified']);self.assertFalse(r['next_stage_authorized'])
 def test_toy_known_unknown_missing_and_donor_are_separate(self):
  rows=[{'person':'a','case':'lamp','cohort':'toy','gold':'off','query_ids':['qa','qb'],'personal_known':True},
        {'person':'a','case':'music','cohort':'toy','gold':'U','query_ids':['qc','qd'],'personal_known':False}]
  r=bench.counts(rows,{'a':{'qa':'U','qb':'U','qc':'U','qd':'U'}})
  self.assertEqual(r['joint'],{'planned':2,'correct':1,'missing':0})
  self.assertEqual(r['known']['correct'],0);self.assertEqual(r['unknown']['correct'],1)
  r=bench.counts(rows,{'a':{'qc':'off','qd':'U'}})
  self.assertEqual(r['joint'],{'planned':2,'correct':0,'missing':1})

if __name__=='__main__':unittest.main()
