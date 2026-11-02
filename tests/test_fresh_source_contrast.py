"""Prospective protocol calibration; oracle fixtures are not measured fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fresh_contrast_tests',ROOT/'benchmarks/fresh-source-contrast-v1/engine.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)


class Fixture:
 def __init__(self,fault=None,at=None):self.calls=0;self.fault=fault;self.at=at;self.data=e.plan.inputs()
 def __call__(self,req,folder,slot):
  self.calls+=1;fault=self.fault if slot['slot']==self.at else None
  if fault=='transport':raise TimeoutError('Offline fixture')
  pid=slot['profile']
  if slot['kind']=='extract':
   source=self.data['sources'][pid]['sources'][0];anchor={'source_id':source['id'],'quote':source['text']}
   value={'version':e.plan.candidate.VERSION,'name':'协议夹具','tagline':'不是模型提炼。','objects':['夹具对象'],
    'nodes':[{'id':'base','kind':'base','target_kind':'choice','object_index':0,'question':'夹具方法','requires':[],
              'action':'夹具选择','priority':0,'decisions':[anchor],'contexts':[anchor],'order_split':None}],
    'unknowns':['未覆盖未知。']}
   if fault=='product':value['nodes'][0]['object_index']=1
  elif slot['kind']=='none':value={q['id']:'U' for q in self.data['queries'][e.plan.bank(pid)]}
  else:
   value={q:r['gold'] for r in self.data['rows'] if r['person']==pid for q in r['query_ids']}
   if fault=='control':value[next(r for r in self.data['rows'] if r['person']==pid and r['gold']!='U')['query_ids'][0]]='U'
   if fault=='tail_guess':value={k:'U' for k in value}
  if fault=='wire':value={}
  return json.dumps(value,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,'usage':None if fault=='usage' else [{'input_tokens':0,'output_tokens':0}]}


class FreshSourceContrastTests(unittest.TestCase):
 def execute(self,tmp,f):
  root=Path(tmp)/'review';e.plan.prepare(root)
  return root,e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_fresh_data_fixed_opposition_roles_support_and_card_source_isolation(self):
  d=e.plan.inputs();self.assertEqual((len(d['rows']),sum(r['gold']!='U' for r in d['rows']),sum(r['personal_known'] for r in d['rows'])),(48,32,20))
  self.assertEqual(sum(len(x['sources']) for x in d['sources'].values()),48)
  self.assertEqual(sum(len(q) for q in d['queries'].values()),48)
  for pid in e.plan.PROFILES:
   own=[r for r in d['rows'] if r['person']==pid];opposite={r['case']:r for r in d['rows'] if r['person']==e.plan.corpus.PAIRS[pid]}
   self.assertEqual(len(own),12)
   for r in own:
    self.assertEqual(r['query_ids'],opposite[r['case']]['query_ids'])
    if r['personal_known']:self.assertNotEqual(r['gold'],opposite[r['case']]['gold'])
    for a in r['support']:self.assertIn(a['quote'],next(s['text'] for s in d['sources'][pid]['sources'] if s['id']==a['source_id']))
  for slot in e.plan.slots()[6:14]:
   req=e.plan.request(slot);body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
   self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
   self.assertEqual(body['sources'],d['sources'][slot['profile']]);self.assertNotIn('tools_01_ab',req['prompt'])

 def test46_fixture_slots_views_repeat_pairs_and_counterfactual_is_not_another_read(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fixture();root,r=self.execute(tmp,f)
   self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(46,'complete',0))
   for v in ('card','tail'):self.assertEqual(r['scores']['per_method_strict'][v]['joint'],{'planned':48,'correct':48,'missing':0})
   self.assertEqual(r['local_cli_child_intents'],0)
   self.assertTrue(all(a['new_reader_calls']==0 and a['opposite_personal_reference']['joint']=={'planned':5,'correct':0,'missing':0} for a in r['scores']['pair_rescoring']))
   pairs={}
   for rec in r['records']:
    if rec['kind']=='read':pairs.setdefault(e.plan.parent(rec)+(rec['view'],),[]).append(rec['request_sha256'])
   self.assertEqual(len(pairs),16);self.assertTrue(all(len(x)==2 and x[0]==x[1] for x in pairs.values()))
   with self.assertRaises(FileExistsError):e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_tail_is_exact_own_length_raw_suffix_and_does_not_borrow_other_profile(self):
  d=e.plan.inputs()
  for pid in e.plan.PROFILES:
   raw=e.plan.old.canonical(d['sources'][pid]);self.assertGreater(len(raw),1536)
   self.assertEqual(e.plan.material(pid,'x'*800,'tail'),raw[-800:])
  self.assertIsNone(e.plan.request(e.plan.slots()[14],{('foreign','source-order-v3',0):{}}))
  with self.assertRaises(ValueError):e.plan.request(dict(e.plan.slots()[14],view='wrong'))

 def test_any_full_control_failure_stops_before_extract7(self):
  for at in (2,3,5,6):
   with self.subTest(at=at),tempfile.TemporaryDirectory() as tmp:
    f=Fixture('control',at);_,r=self.execute(tmp,f)
    self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',46-at));self.assertFalse(any(x['kind']=='extract' for x in r['records']))

 def test_invalid_parent_keeps_both_view_denominators_and_skips_only_own4(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fixture('product',7);_,r=self.execute(tmp,f)
   self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(42,'completed_with_invalid_products',4))
   self.assertEqual(len(r['skipped']),4)
   for v in ('tail','card'):self.assertEqual(r['scores']['per_method_strict'][v]['joint'],{'planned':48,'correct':36,'missing':12})

 def test_one_wrong_order_in_one_card_read_loses_only_that_view_case(self):
  d=e.plan.inputs();cards={};answers={}
  for pid,method,g in e.plan.cells():
   cards[pid,method,g]={'prompt':'x'*200}
   for view in ('card','tail'):
    for r in (0,1):answers[pid,method,g,view,r]={q:row['gold'] for row in d['rows'] if row['person']==pid for q in row['query_ids']}
  row=next(r for r in d['rows'] if r['person']=='t0' and r['personal_known'])
  answers['t0','source-order-v3',1,'card',1][row['query_ids'][1]]='U'
  scored=e.score.summarize(d['rows'],answers,cards)
  self.assertEqual(scored['per_method_strict']['card']['joint'],{'planned':48,'correct':47,'missing':0})
  self.assertEqual(scored['per_method_strict']['tail']['joint'],{'planned':48,'correct':48,'missing':0})
  self.assertEqual(scored['paired_strict_development_cases']['only_baseline_correct'],1)

 def test_wire_usage_final_failure_and_input_or_encoder_drift_close(self):
  for fault,at in (('wire',7),('usage',1),('transport',46)):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    f=Fixture(fault,at);_,r=self.execute(tmp,f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',46-at))
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'review';p=e.plan.prepare(root)
   self.assertFalse(p['approved']);self.assertEqual(len(e.plan.read(root/'static-requests.json')),14);self.assertEqual(len(e.plan.read(root/'dynamic-rules.json')['slots']),32)
   self.assertTrue(e.plan.verify(root));(root/'sources.json').write_text('{}')
   with self.assertRaises(ValueError):e.plan.verify(root)


if __name__=='__main__':unittest.main()
