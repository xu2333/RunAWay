"""Protocol fixture only; labels injected by fixture are not model evidence."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixed9_test_engine',HERE.parent/'benchmarks/coverage-fixed-views-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
class Fixture:
 def __init__(self,fault=None,at=None):self.fault,self.at,self.calls=fault,at,0
 def __call__(self,req,folder,slot):
  self.calls+=1;data=e.plan.inputs()
  if slot['kind']=='none':answer={q['id']:'U'for q in data['queries']['all']}
  else:answer={q:r['gold']for r in data['rows']if r['person']==slot['profile']for q in r['query_ids']}
  if slot['slot']==self.at and self.fault=='answer':
   r=next(r for r in data['rows']if r['person']==slot['profile']and r['personal_known']);answer[r['query_ids'][1]]='U'
  if slot['slot']==self.at and self.fault=='transport':raise ValueError('fixture')
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,
   'usage':None if slot['slot']==self.at and self.fault=='usage'else[{'input_tokens':0,'output_tokens':0}]}
class Tests(unittest.TestCase):
 def execute(self,fixture,simulated=True):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'in';e.plan.prepare(root)
   return e.run(root,Path(tmp)/'out',fixture,lambda _: {},simulated=simulated)
 def test_frozen_requests_only_own_card_or_source_no_reference_or_raw_graph(self):
  p=e.plan;self.assertEqual(len(p.slots()),9)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'in';p.prepare(root);self.assertTrue(p.verify(root))
  self.assertEqual([len(t)for t in p.inputs()['materials'].values()],[353,324,506])
  for s in p.slots():
   req=p.request(s)
   self.assertEqual(req,p.values()['static-requests.json'][str(s['slot'])])
   if s['kind']=='read':
    self.assertEqual(p.inputs()['materials'][s['view']],json.loads(req['prompt'].split('\nREADER_INPUT_JSON:\n')[1])['material'])
    self.assertNotIn('GRAPH_INPUT_JSON',req['prompt'])
 def test_complete_fixture_only_keeps15and30_denominators(self):
  f=Fixture();r=self.execute(f);self.assertEqual((f.calls,r['status'],r['local_cli_child_intents']),(9,'complete',0))
  self.assertEqual(r['scores']['guided30']['joint'],{'planned':30,'correct':30,'missing':0})
  for s in r['scores']['fixed_views'].values():self.assertEqual(s['joint'],{'planned':15,'correct':15,'missing':0})
 def test_control_unknown_usage_and_transport_stop_without_retry(self):
  for fault,at in(('answer',3),('usage',4),('transport',5)):
   with self.subTest(fault=fault):
    f=Fixture(fault,at);r=self.execute(f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',9-at))
  f=Fixture();r=self.execute(f,False);self.assertEqual((f.calls,r['attempt_reservations']),(0,0))
 def test_one_wrong_order_is_retained_and_old_scores_never_replaced(self):
  f=Fixture('answer',4);r=self.execute(f)
  self.assertEqual(r['scores']['fixed_views']['a8r:baseline']['joint']['correct'],14)
  self.assertFalse(r['scores']['old43_scores_replaced'])
if __name__=='__main__':unittest.main()
