"""Protocol/oracle fixtures only; no service or semantic-review success claim."""
from pathlib import Path
import importlib.util,json,tempfile,unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review7_fixture',HERE.parent/'benchmarks/source-review-diagnostic-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
class Fixture:
 def __init__(self,fault=None,at=None):self.fault,self.at,self.calls=fault,at,0
 def __call__(self,req,folder,slot):
  self.calls+=1;data=e.plan.inputs()
  if slot['kind']=='review':
   answer=json.loads(json.dumps(data['draft']))
   if self.fault=='product':answer['nodes'][0]['object_index']=2
  else:
   answer={q:('U'if slot['kind']=='none'else r['gold'])for r in data['rows']for q in r['query_ids']}
   if slot['slot']==self.at and self.fault=='answer':
    row=next(r for r in data['rows']if r['personal_known']);answer[row['query_ids'][1]]='U'
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,
    'usage':None if self.fault=='usage'and slot['slot']==self.at else[{'input_tokens':0,'output_tokens':0}]}
class Tests(unittest.TestCase):
 def run_fixture(self,fixture,simulated=True):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'inputs';e.plan.prepare(root)
   return e.run(root,Path(tmp)/'fixture',fixture,lambda _: {},simulated=simulated)
 def test_exact_source_and_candidate_only_no_targets_or_reader_feedback(self):
  p=e.plan;self.assertEqual(len(p.slots()),7)
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'input';p.prepare(root);self.assertTrue(p.verify(root))
  data=p.inputs();self.assertEqual((len(data['sources']['f7s']['sources']),len(data['rows'])),(22,15))
  req=p.request(p.slots()[2]);self.assertNotIn('e01_ab',req['prompt'])
  body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1].split('\nREVIEW_DRAFT_JSON:\n')[0])
  self.assertEqual(set(body),{'sources','budget_characters','fixed_header','fixed_guide'})
  self.assertEqual(body['sources'],data['sources']['f7s'])
  self.assertEqual(json.loads(req['prompt'].split('\nREVIEW_DRAFT_JSON:\n')[1]),data['draft'])
  self.assertEqual(p.reviewer.bind(data['draft'],data['sources']['f7s'],1536)['prompt.md'],data['original'])
 def test_seven_slot_oracle_fixture_is_only_accounting_not_review_fidelity(self):
  f=Fixture();r=self.run_fixture(f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(7,'complete',0))
  for view in('original','reviewed'):self.assertEqual(r['scores']['views'][view]['joint'],{'planned':15,'correct':15,'missing':0})
  self.assertEqual(r['local_cli_child_intents'],0);self.assertTrue(r['simulated'])
 def test_invalid_reviewed_product_only_skips_own_two_reads_and_retains_denominator(self):
  f=Fixture('product',3);r=self.run_fixture(f)
  self.assertEqual((f.calls,r['unused_slots_expire'],len(r['skipped'])),(5,2,2))
  self.assertEqual(r['scores']['views']['reviewed']['joint'],{'planned':15,'correct':0,'missing':15})
  self.assertEqual(r['scores']['views']['original']['joint']['correct'],15)
 def test_control_and_unknown_usage_stop_and_single_wrong_order_is_retained(self):
  for fault,at,calls in(('answer',2,2),('usage',3,3)):
   f=Fixture(fault,at);r=self.run_fixture(f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(calls,'stopped',7-calls))
  f=Fixture('answer',4);r=self.run_fixture(f);self.assertEqual(r['scores']['views']['original']['joint']['correct'],14)
  f=Fixture();r=self.run_fixture(f,False);self.assertEqual((f.calls,r['attempt_reservations']),(0,0))
if __name__=='__main__':unittest.main()
