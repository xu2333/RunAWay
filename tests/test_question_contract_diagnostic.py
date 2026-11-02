"""Unchanged-memory,isolated question-packet diagnostics;fixtures are not fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('question_contract_tests',ROOT/'benchmarks/question-contract-diagnostic-v1/engine.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)


class Fixture:
 def __init__(self,fault=None,at=None):self.calls=0;self.fault=fault;self.at=at;self.data=e.plan.inputs()
 def __call__(self,req,folder,slot):
  self.calls+=1;fault=self.fault if slot['slot']==self.at else None
  if fault=='transport':raise TimeoutError('Offline fixture')
  answer={q:r['gold'] for r in self.data['rows'] for q in r['query_ids']}
  if slot['kind']=='none':answer={q:'U' for q in answer}
  if slot['kind']=='read' and slot['method']=='original':
   for q in next(r for r in self.data['rows'] if r['case']=='c05')['query_ids']:answer[q]='U'
  if fault=='control':answer[self.data['rows'][0]['query_ids'][0]]='U'
  if fault=='wire':answer={}
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,'usage':None if fault=='usage' else [{'input_tokens':0,'output_tokens':0}]}


class QuestionContractTests(unittest.TestCase):
 def execute(self,tmp,f):
  root=Path(tmp)/'review';e.plan.prepare(root)
  return root,e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_only_two_task_descriptors_change_no_memory_facts_options_or_references(self):
  d=e.plan.inputs();old=e.plan.old.inputs();a,b=e.plan.views()
  self.assertEqual(a['prompt'],b['prompt']);self.assertEqual((a['characters'],b['characters']),(495,495))
  self.assertEqual(d['sources'],old['sources']);self.assertEqual(d['rows'],old['rows']);self.assertEqual(len(d['rows']),12)
  changed=[]
  for original,explicit in zip(d['queries']['original'],d['queries']['explicit']):
   if original!=explicit:
    changed.append(original['id']);restored=copy.deepcopy(explicit)
    restored['scenario']=restored['scenario'].replace(e.plan.NEW_TARGET,e.plan.OLD_TARGET);self.assertEqual(restored,original)
  self.assertEqual(changed,['editing_05_ab','editing_05_ba'])

 def test_packets_are_separate_and_each_has_own_none_full_controls(self):
  slots=e.plan.slots();self.assertEqual([s['kind'] for s in slots],['none','full','none','full']+['read']*4)
  for slot in slots:
   req=e.plan.request(slot)
   if slot['method']=='original':self.assertIn(e.plan.OLD_TARGET,req['prompt']);self.assertNotIn(e.plan.NEW_TARGET,req['prompt'])
   else:self.assertIn(e.plan.NEW_TARGET,req['prompt']);self.assertNotIn(e.plan.OLD_TARGET,req['prompt'])
  self.assertEqual(sum(len(x) for x in e.plan.inputs()['queries'].values()),48)

 def test_eight_fixture_attempts_report_each_packet_without_replacing_old_scores(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fixture();root,r=self.execute(tmp,f)
   self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(8,'complete',0));self.assertEqual(set(r['control_gates']),{'original','explicit'})
   for method,n in (('original',11),('explicit',12)):
    self.assertEqual(r['scores']['methods'][method]['strict_both_reads']['joint'],{'planned':12,'correct':n,'missing':0})
    hs=[x['request_sha256'] for x in r['records'] if x['kind']=='read' and x['method']==method];self.assertEqual(hs[0],hs[1])
   self.assertFalse(r['scores']['old_question_gold_replaced']);self.assertFalse(r['scores']['semantic_paraphrase_equivalence_accepted'])
   self.assertEqual(r['scores']['new_extractions'],0)

 def test_either_full_control_failure_closes_before_any_memory_read(self):
  for at in (2,4):
   with self.subTest(at=at),tempfile.TemporaryDirectory() as tmp:
    f=Fixture('control',at);_,r=self.execute(tmp,f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',8-at));self.assertFalse(any(x['kind']=='read' for x in r['records']))

 def test_wire_usage_final_failure_and_exclusive_run_prevent_retry(self):
  for fault,at in (('wire',5),('usage',1),('transport',8)):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    f=Fixture(fault,at);root,r=self.execute(tmp,f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',8-at))
    with self.assertRaises(FileExistsError):e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_one_order_wrong_keeps_the_full12case_denominator(self):
  rows=e.plan.inputs()['rows'];answers={('e0',m,0,r):{q:row['gold'] for row in rows for q in row['query_ids']} for m in e.plan.METHODS for r in (0,1)}
  answers['e0','explicit',0,1][rows[4]['query_ids'][1]]='U'
  score=e.score.summarize(rows,answers)
  self.assertEqual(score['methods']['explicit']['strict_both_reads']['joint'],{'planned':12,'correct':11,'missing':0})
  self.assertEqual(score['methods']['original']['strict_both_reads']['joint']['correct'],12)

 def test_exclusive_unapproved_static_freeze_rejects_question_drift(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'review';p=e.plan.prepare(root);self.assertFalse(p['approved']);self.assertFalse(p['new_service_authority'])
   self.assertEqual(len(e.plan.read(root/'static-requests.json')),8);self.assertEqual(e.plan.read(root/'dynamic-rules.json')['slots'],[])
   self.assertTrue(e.plan.verify(root));(root/'queries.public.json').write_text('{}')
   with self.assertRaises(ValueError):e.plan.verify(root)


if __name__=='__main__':unittest.main()
