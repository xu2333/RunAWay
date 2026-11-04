"""Finite review-repeat fixtures; all oracle answers are accounting-only."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('enum59_test_engine',ROOT/'benchmarks/source-id-enum-repeat-v1/engine.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
p=e.plan

def refs(value):
 if isinstance(value,list):return [refs(v)for v in value]
 if not isinstance(value,dict):return copy.deepcopy(value)
 if set(value)=={'source_id','quote'}:return {'source_id':value['source_id']}
 return {k:refs(v)for k,v in value.items()}

class Fixture:
 def __init__(self,fault=None):self.fault=fault;self.calls=[];self.requests=[]
 def __call__(self,req,folder,slot):
  self.calls.append(dict(slot));self.requests.append(req);data=p.inputs()
  if self.fault=='transport'and slot['slot']==5:raise ValueError('Offline transport fixture')
  if slot['kind']=='review':
   answer=refs(data['parents'][slot['parent']]['draft']);answer['version']=p.reviewer.VERSION
   answer['name']=slot['parent']+'-'+slot['method']+'-'+str(slot['review_repeat'])
   if self.fault=='enum_reference'and slot['slot']==8:answer['nodes'][0]['decisions'][0]['source_id']='m99'
   if self.fault=='product'and slot['parent']=='p1'and slot['review_repeat']==0 and slot['method']=='existing':answer['nodes'][0]['object_index']=2
  else:
   rows=[r for r in data['rows']if r['person']==(slot['profile']or'c2v')]
   answer={q:('U'if slot['kind']=='none'else r['gold'])for r in rows for q in r['query_ids']}
   if(self.fault=='control'and slot['slot']==2)or(self.fault=='one_order'and slot['parent']=='p0'and slot['view']=='reviewed'and slot['review_repeat']==1 and slot['read_repeat']==0 and slot['method']=='enumerated'):
    row=next(r for r in rows if r['personal_known']);answer[row['query_ids'][1]]='U'
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':p.MODEL,
   'usage':None if self.fault=='usage'and slot['slot']==5 else[{'input_tokens':0,'output_tokens':0}]}

class EnumReviewComparisonProtocolTests(unittest.TestCase):
 def run_fixture(self,f,simulated=True):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'input';p.prepare(root)
   return e.run(root,Path(tmp)/'execution',f,lambda _: {},simulated=simulated)
 def test_fixed_scope_sources_static_requests_and_distinct_denominators(self):
  data=p.inputs();self.assertEqual((len(data['sources']),sum(len(s['sources'])for s in data['sources'].values()),len(data['rows'])),(2,44,30))
  self.assertEqual([data['parents'][key]['characters']for key in('p0','p1','p2','p3')],[585,312,434,240])
  values=p.values();self.assertEqual((len(p.slots()),len(values['static-requests.json']),len(values['dynamic-rules.json']['slots'])),(59,27,32))
  for slot in p.slots():
   if slot['kind']!='review':continue
   req=p.request(slot);body=json.loads(req['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1].split('\nREVIEW_DRAFT_JSON:\n')[0])
   self.assertEqual(body['sources'],data['sources'][slot['profile']])
   self.assertEqual(json.loads(req['prompt'].split('\nREVIEW_DRAFT_JSON:\n')[1]),data['parents'][slot['parent']]['draft'])
   self.assertNotIn('e01_ab',req['prompt']);self.assertNotIn('previously_incomplete',req['prompt'])
  for parent in data['parents']:
   for repeat in(0,1):
    pair={slot['method']:p.request(slot)for slot in p.slots()if slot['kind']=='review'and slot['parent']==parent and slot['review_repeat']==repeat}
    self.assertEqual({k:v for k,v in pair['existing'].items()if k!='schema'},{k:v for k,v in pair['enumerated'].items()if k!='schema'})
    self.assertNotEqual(pair['existing']['schema'],pair['enumerated']['schema'])
 def test_complete_oracle_only_verifies59slot_accounting(self):
  f=Fixture();r=self.run_fixture(f)
  self.assertEqual((len(f.calls),r['status'],r['unused_slots_expire']),(59,'complete',0))
  self.assertEqual(r['local_cli_child_intents'],0);self.assertTrue(r['simulated'])
  self.assertEqual((r['scores']['planned_parent_case_cells_per_method'],r['scores']['unique_person_cases']),(60,30))
  for parent in r['scores']['by_parent'].values():
   self.assertEqual(parent['original']['joint']['correct'],15)
   for method in parent['methods'].values():
    for view in method.values():self.assertEqual(view['joint'],{'planned':15,'correct':15,'missing':0})
 def test_invalid_review_skips_only_own_two_reads_other_repeat_and_original_still_run(self):
  f=Fixture('product');r=self.run_fixture(f)
  self.assertEqual((len(f.calls),len(r['skipped']),r['unused_slots_expire']),(57,2,2))
  self.assertEqual({(s['parent'],s['method'],s['review_repeat'])for s in r['skipped']},{('p1','existing',0)})
  parent=r['scores']['by_parent']['p1'];views=parent['methods']['existing']
  self.assertEqual(views['review0']['joint'],{'planned':15,'correct':0,'missing':15})
  self.assertEqual(views['review1']['joint']['correct'],15);self.assertEqual(parent['original']['joint']['correct'],15)
  self.assertEqual(parent['methods']['enumerated']['both_reviews']['joint']['correct'],15)
  self.assertEqual(views['both_reviews']['joint']['missing'],15)
  f=Fixture('enum_reference');r=self.run_fixture(f)
  self.assertEqual((len(f.calls),r['status'],len(r['skipped'])),(57,'complete',2))
  failed=next(x for x in r['records']if x['slot']==8)
  self.assertFalse(failed['request_schema_conformant']);self.assertTrue(failed['product_invalid'])
  self.assertEqual(r['scores']['by_parent']['p0']['methods']['existing']['both_reviews']['joint']['correct'],15)
  self.assertEqual(r['scores']['by_parent']['p0']['methods']['enumerated']['both_reviews']['joint']['missing'],15)
 def test_control_unknown_usage_and_transport_failures_close_without_retry(self):
  for fault,calls in(('control',2),('usage',5),('transport',5)):
   with self.subTest(fault=fault):
    f=Fixture(fault);r=self.run_fixture(f)
    self.assertEqual((len(f.calls),r['status'],r['unused_slots_expire']),(calls,'stopped',59-calls))
    self.assertTrue(r['scope_closed']);self.assertFalse(r['old_scopes_reopened'])
 def test_one_wrong_answer_is_retained_in_its_review_and_stricter_joint_result(self):
  f=Fixture('one_order');r=self.run_fixture(f);parent=r['scores']['by_parent']['p0'];views=parent['methods']['enumerated']
  self.assertEqual([parent['original']['joint']['correct']]+[views[k]['joint']['correct']for k in('review0','review1','both_reviews')],[15,15,14,14])
  self.assertEqual(parent['methods']['existing']['both_reviews']['joint']['correct'],15)
  bad=[v for v in r['scores']['transitions']if v['parent']=='p0'and not v['methods']['enumerated']['both_reviews']['correct']]
  self.assertEqual(len(bad),1);self.assertFalse(bad[0]['methods']['enumerated']['both_reviews']['missing'])
 def test_each_reader_uses_its_own_parent_and_own_review_repeat(self):
  f=Fixture();self.run_fixture(f);data=p.inputs()
  for slot,req in zip(f.calls,f.requests):
   if slot['kind']=='read'and slot['view']=='reviewed':
    own=slot['parent']+'-'+slot['method']+'-'+str(slot['review_repeat']);self.assertIn(own,req['prompt'])
    for parent in data['parents']:
     if parent!=slot['parent']:self.assertNotIn(parent+'-'+slot['method']+'-'+str(slot['review_repeat']),req['prompt'])
   elif slot['kind']=='read':self.assertEqual(data['parents'][slot['parent']]['prompt'],json.loads(req['prompt'].split('\nREADER_INPUT_JSON:\n')[1])['material'])
  slot=dict(p.slots()[4]);slot['parent']='foreign'
  with self.assertRaises(ValueError):p.request(slot)
 def test_no_live_guard_no_invocation_and_cached_inputs_cannot_be_mutated_or_drift(self):
  f=Fixture();r=self.run_fixture(f,False);self.assertEqual((len(f.calls),r['attempt_reservations']),(0,0))
  data=p.inputs();data['parents']['p0']['draft']['name']='changed'
  self.assertNotEqual(p.inputs()['parents']['p0']['draft']['name'],'changed')
  old_sha=p.sha
  def drift(file):return 'changed'if str(file).endswith('ambiguous-source-repeat-v1/measured.synthetic.json')else old_sha(file)
  with patch.object(p,'sha',side_effect=drift):
   with self.assertRaises(ValueError):p.inputs()
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)/'input';p.prepare(root);(root/'reference.private.json').write_text('[]')
   with self.assertRaises(ValueError):p.verify(root)
if __name__=='__main__':unittest.main()
