"""Offline source-isolation and66slot lifecycle fixtures; no model fidelity."""
from pathlib import Path
import importlib.util,json,tempfile,unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coverage43_fixture_engine',HERE.parent/'benchmarks/remaining-source-repeat-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
class Fixture:
 def __init__(self,fault=None,at=None):self.calls,self.fault,self.at=0,fault,at
 def __call__(self,req,folder,slot):
  self.calls+=1;data=e.plan.inputs();pid=slot['profile']
  if slot['kind']=='extract':
   source=data['sources'][pid]['sources'][0];anchor={'source_id':source['id'],'quote':source['text']}
   answer={'version':e.plan.factory(slot['method']).VERSION,'name':'协议夹具','tagline':'不是模型提炼。',
    'objects':['夹具对象'],'nodes':[{'id':'base','kind':'base','target_kind':'choice','object_index':0,
    'question':'夹具选择','requires':[],'action':'夹具选择','priority':0,'decisions':[anchor],
    'contexts':[anchor],'order_split':None}],'unknowns':['未覆盖未知。']}
   if slot['slot']==self.at and self.fault=='product':answer['nodes'][0]['object_index']=1
  elif slot['kind']=='none':answer={q['id']:'U'for q in data['queries']['all']}
  else:
   answer={q:row['gold']for row in data['rows']if row['person']==pid for q in row['query_ids']}
   if slot['slot']==self.at and self.fault in('control','order'):
    row=next(r for r in data['rows']if r['person']==pid and r['personal_known']);answer[row['query_ids'][1]]='U'
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,
   'usage':None if slot['slot']==self.at and self.fault=='usage'else[{'input_tokens':0,'output_tokens':0}]}
class Tests(unittest.TestCase):
 def execute(self,tmp,fixture,simulated=True):
  root=Path(tmp)/'inputs';e.plan.prepare(root)
  return e.run(root,Path(tmp)/'fixture',fixture,lambda _: {},simulated=simulated)
 def test66slots_source_only_prefix_and_fixed30case_design(self):
  p=e.plan;data=p.inputs();slots=p.slots()
  self.assertEqual((len(slots),len([s for s in slots if s['kind']=='extract']),len([s for s in slots if s['kind']=='read'])),(66,20,40))
  self.assertEqual((len(data['rows']),sum(r['gold']!='U'for r in data['rows'])),(75,36))
  self.assertEqual(data['design']['personal_known'],29);self.assertEqual(data['design']['derived_known'],20)
  for pid in p.PROFILES:
   baseline=p.factory(p.METHODS[0]).make_request(data['sources'][pid],1536)
   candidate=p.factory(p.METHODS[1]).make_request(data['sources'][pid],1536)
   self.assertEqual(candidate['schema'],baseline['schema'])
   self.assertEqual(candidate['prompt'],p.coverage.GUIDANCE+'\n'+baseline['prompt'])
  for slot in (s for s in slots if s['kind']=='extract'):
   req=p.request(slot);body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
   self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
   self.assertEqual(body['sources'],data['sources'][slot['profile']])
   self.assertNotIn('e01_ab',req['prompt'])
 def test_complete66oracle_fixture_only_not_model_quality(self):
  with tempfile.TemporaryDirectory()as tmp:
   fixture=Fixture();result=self.execute(tmp,fixture)
  self.assertEqual((fixture.calls,result['status'],result['local_cli_child_intents']),(66,'complete',0))
  self.assertTrue(result['simulated'])
  for method in e.plan.METHODS:
   for view in('card',):
    self.assertEqual(result['scores']['methods'][method][view]['strict']['joint'],{'planned':75,'correct':75,'missing':0})
 def test_control_stop_and_invalid_parent_keep_methods_denominators(self):
  for fault,at,calls in(('control',2,2),('product',7,64)):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory()as tmp:
    fixture=Fixture(fault,at);result=self.execute(tmp,fixture)
   self.assertEqual((fixture.calls,result['unused_slots_expire']),(calls,66-calls))
   for method in e.plan.METHODS:
    for view in('card',):
     joint=result['scores']['methods'][method][view]['strict']['joint'];self.assertEqual(joint['planned'],75)
     self.assertEqual(joint['missing'],75 if fault=='control'else 15 if method==e.plan.METHODS[0]else 0)
 def test_bad_order_remains_and_unknown_usage_or_missing_guard_stops(self):
  with tempfile.TemporaryDirectory()as tmp:
   fixture=Fixture('order',8);result=self.execute(tmp,fixture)
  slot=e.plan.slots()[7]
  self.assertEqual(result['scores']['methods'][slot['method']][slot['view']]['strict']['joint']['correct'],74)
  with tempfile.TemporaryDirectory()as tmp:
   fixture=Fixture('usage',8);result=self.execute(tmp,fixture)
  self.assertEqual((fixture.calls,result['status'],result['unused_slots_expire']),(8,'stopped',58))
  with tempfile.TemporaryDirectory()as tmp:
   fixture=Fixture();result=self.execute(tmp,fixture,False)
  self.assertEqual((fixture.calls,result['attempt_reservations']),(0,0))
if __name__=='__main__':unittest.main()
