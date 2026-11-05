"""New-source reference and finite-controller checks; oracle is not model evidence."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fresh_pipeline_test_engine',ROOT/'benchmarks/fresh-enum-pipeline-v1/engine.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
p=e.plan

def graph(pid,reviewed=False):
 src=p.inputs()['sources'][pid]['sources'][0];a={'source_id':src['id']}
 if not reviewed:a['quote']=src['text']
 return {'version':p.reviewer.VERSION if reviewed else p.producer.VERSION,'name':pid+('-review'if reviewed else'-draft'),'tagline':'仅记账的离线假响应',
  'objects':[p.corpus.DOMAINS[0][1]],'nodes':[{'id':'x','kind':'base','target_kind':'choice','object_index':0,'question':'剪辑选择','requires':[],
  'action':'保留原声','priority':0,'decisions':[copy.deepcopy(a)],'contexts':[copy.deepcopy(a)],'order_split':None}],'unknowns':['离线记账假响应，不承诺行为。']}
class Fixture:
 def __init__(self,fault=None):self.fault=fault;self.calls=[];self.requests=[]
 def __call__(self,req,folder,slot):
  self.calls.append(slot);self.requests.append(req);kind=slot['kind'];pid=slot['profile']
  if self.fault=='transport'and slot['slot']==6:raise ValueError('Offline fixture')
  if kind in('extract','review'):
   answer=graph(pid,kind=='review')
   if self.fault=='extract_product'and slot['slot']==6:answer['nodes'][0]['object_index']=9
   if self.fault=='review_id'and slot['slot']==7:answer['nodes'][0]['decisions'][0]['source_id']='foreign_id'
   if self.fault=='wire'and slot['slot']==6:answer.pop('nodes')
  else:
   rows=[r for r in p.inputs()['rows']if r['person']==(pid or p.PROFILES[0])]
   answer={q:'U'if kind=='none'else r['gold']for r in rows for q in r['query_ids']}
   if(self.fault=='control'and slot['slot']==2)or(self.fault=='one_order'and pid=='pavo'and slot['view']=='reviewed'and slot['read_repeat']==1):
    row=next(r for r in rows if r['personal_known']);answer[row['query_ids'][1]]='U'
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':p.MODEL,'usage':None if self.fault=='usage'and slot['slot']==6 else[{'input_tokens':0,'output_tokens':0}]}
class FreshEnumPipelineTests(unittest.TestCase):
 def run_fixture(self,f,simulated=True):
  with tempfile.TemporaryDirectory()as t:
   root=Path(t)/'i';p.prepare(root)
   return e.run(root,Path(t)/'e',f,lambda _: {},simulated=simulated)
 def test_reviewable_public_material_and_protocol_match_frozen_reconstruction(self):
  d=p.inputs();folder=ROOT/'benchmarks/fresh-enum-pipeline-v1'
  for name,value in(('sources.synthetic.json',d['sources']),('questions.public.json',d['queries']),('author-reference.synthetic.json',d['rows']),('author-evidence.synthetic.json',d['author_evidence']),('protocol.json',p.values()['proposal.json'])):
   self.assertEqual(p.read(folder/name),value)
 def test_new_cohort_has64_cells_nonmonotone_rules_and_no_old_source_reuse(self):
  d=p.inputs();self.assertEqual((len(d['sources']),len(d['rows']),len(d['queries']['all'])),(4,64,32))
  self.assertEqual(sum(r['gold']!='U'for r in d['rows']),24);self.assertEqual(sum(r['derived_known']for r in d['rows']),8)
  self.assertEqual(sum(r['cohort']=='withdrawal_unseen'for r in d['rows']),8)
  old=p.seed.inputs()['sources'];oldtext={s['text']for x in old.values()for s in x['sources']}
  for pid,src in d['sources'].items():
   self.assertEqual(len(src['sources']),22);self.assertTrue(all(s['id'].startswith(pid+'_')for s in src['sources']))
   self.assertTrue(all(len(s['text'])<=2000 for s in src['sources']));self.assertGreater(sum(len(s['text'])for s in src['sources']),1536)
   self.assertFalse(oldtext&{s['text']for s in src['sources']})
  # Same questions,opposite known choices;none cannot infer both profiles.
  for first,second in(('pavo','rill'),('tavi','wren')):
   a=[r for r in d['rows']if r['person']==first];b=[r for r in d['rows']if r['person']==second]
   for x,y in zip(a,b):
    self.assertEqual(x['query_ids'],y['query_ids']);self.assertNotEqual(x['gold'],y['gold'])if x['gold']!='U'else self.assertEqual(y['gold'],'U')
 def test_reference_uses_current_source_not_retracted_rule_or_hidden_truth(self):
  c=p.corpus;self.assertEqual(c.licensed(False,[[1,1],[2,1]],[0]),0)
  self.assertEqual(c.licensed(True,[[1,0],[2,0]],[0]),1)
  for observed in([[1,0],[2,1]],[[1,1],[2,0]]):
   self.assertEqual(len(c.compatible(None,observed)),4)
   for state in(0,3):self.assertEqual(c.licensed(None,observed,[state]),'U')
  self.assertEqual(c.licensed(False,[[1,1],[2,1]],[1,3]),'U')
  self.assertEqual(c.licensed(False,[[1,1],[2,1]],[0],False),'U')
  with self.assertRaises(ValueError):c.compatible(False,[[0,1]])
 def test_static_and_dynamic_scope_have_no_gold_or_question_leakage_to_producers(self):
  values=p.values();self.assertEqual((len(p.slots()),len(values['static-requests.json']),len(values['dynamic-rules.json']['slots'])),(45,9,36))
  for slot in p.slots():
   if slot['kind']not in('extract','review'):continue
   req=p.request(slot,{(slot['profile'],'draft'):graph(slot['profile'])})
   self.assertNotIn('n01_ab',req['prompt']);self.assertNotIn('derived_known',req['prompt']);self.assertNotIn('author_evidence',req['prompt'])
   for pid in p.PROFILES:
    if pid!=slot['profile']:self.assertNotIn(pid+'_r',req['prompt'])
 def test_complete45_oracle_checks_accounting_only_and_person_slices_do_not_overwrite(self):
  f=Fixture();x=self.run_fixture(f);self.assertEqual((len(f.calls),x['status'],x['unused_slots_expire']),(45,'complete',0))
  self.assertEqual(x['local_cli_child_intents'],0);self.assertTrue(x['simulated'])
  for view in p.VIEWS:
   self.assertEqual(x['scores']['views'][view]['joint'],{'planned':64,'correct':64,'missing':0})
   self.assertEqual(x['scores']['slices']['derived_known'][view]['joint']['correct'],8)
   self.assertEqual(x['scores']['slices']['withdrawal_unseen'][view]['joint']['correct'],8)
   self.assertEqual(x['scores']['slices']['execution'][view]['joint']['correct'],4)
 def test_invalid_initial_skips_only_own_review_and_eight_reads(self):
  f=Fixture('extract_product');x=self.run_fixture(f)
  self.assertEqual((len(f.calls),len(x['skipped']),x['unused_slots_expire']),(36,9,9))
  self.assertEqual({s['profile']for s in x['skipped']},{'pavo'})
  for view in p.VIEWS:self.assertEqual(x['scores']['views'][view]['joint'],{'planned':64,'correct':48,'missing':16})
 def test_invalid_enum_reference_skips_reviewed_and_its_tail_not_initial_controls(self):
  f=Fixture('review_id');x=self.run_fixture(f)
  self.assertEqual((len(f.calls),len(x['skipped']),x['unused_slots_expire']),(41,4,4))
  rec=next(r for r in x['records']if r['slot']==7);self.assertFalse(rec['request_schema_conformant']);self.assertTrue(rec['product_invalid'])
  for view in p.VIEWS:self.assertEqual(x['scores']['views'][view]['joint'],{'planned':64,'correct':48 if view.startswith('reviewed')else 64,'missing':16 if view.startswith('reviewed')else 0})
 def test_control_wire_transport_and_unknown_usage_close_no_retry(self):
  for fault,n in(('control',2),('wire',6),('transport',6),('usage',6)):
   with self.subTest(fault=fault):
    f=Fixture(fault);x=self.run_fixture(f);self.assertEqual((len(f.calls),x['status'],x['unused_slots_expire']),(n,'stopped',45-n));self.assertTrue(x['scope_closed'])
 def test_single_wrong_option_order_is_not_erased_by_other_views(self):
  x=self.run_fixture(Fixture('one_order'))
  self.assertEqual(x['scores']['views']['reviewed']['joint'],{'planned':64,'correct':63,'missing':0})
  self.assertEqual(x['scores']['views']['draft']['joint']['correct'],64)
 def test_each_tail_is_exact_own_card_length_and_review_has_own_raw_draft(self):
  graphs={(pid,stage):graph(pid,stage=='reviewed')for pid in p.PROFILES for stage in('draft','reviewed')}
  for pid in p.PROFILES:
   for stage in('draft','reviewed'):
    card=p.material(pid,stage,graphs);tail=p.material(pid,stage+'_tail',graphs)
    self.assertEqual(len(card),len(tail));self.assertEqual(tail,p.transcript(p.inputs()['sources'][pid])[-len(card):])
   slot=next(s for s in p.slots()if s['kind']=='review'and s['profile']==pid)
   req=p.request(slot,graphs);self.assertEqual(json.loads(req['prompt'].split('\nREVIEW_DRAFT_JSON:\n')[1]),graphs[pid,'draft'])
 def test_input_damage_refuses_before_any_transport_and_live_guard_has_zero_intents(self):
  with tempfile.TemporaryDirectory()as t:
   root=Path(t)/'i';p.prepare(root);f=Fixture();file=root/'reference.private.json';data=p.read(file);data[0]['gold']='U';file.write_text(json.dumps(data))
   with self.assertRaises(ValueError):e.run(root,Path(t)/'e',f,lambda _: {},simulated=True)
   self.assertFalse(f.calls)
  f=Fixture();x=self.run_fixture(f,False);self.assertFalse(f.calls);self.assertEqual(x['attempt_reservations'],0)
  self.assertTrue(x['stop'].startswith('pre_call_failure:PermissionError'))
if __name__=='__main__':unittest.main()
