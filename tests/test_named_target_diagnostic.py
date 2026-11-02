"""Fixed-parent marker conservation and finite read-only calibration;no model calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('named_target_diagnostic_tests',ROOT/'benchmarks/named-target-diagnostic-v1/engine.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)


class Fixture:
 def __init__(self,fault=None,at=None,neutral_fixes=False):self.calls=0;self.fault=fault;self.at=at;self.neutral_fixes=neutral_fixes;self.data=e.plan.inputs()
 def __call__(self,req,folder,slot):
  self.calls+=1;fault=self.fault if slot['slot']==self.at else None
  if fault=='transport':raise TimeoutError('Offline fixture')
  answer={q:r['gold'] for r in self.data['rows'] for q in r['query_ids']}
  if slot['kind']=='none':answer={q:'U' for q in answer}
  if slot['kind']=='read' and (slot['method']=='original' or slot['method']=='neutral' and not self.neutral_fixes):
   for q in next(r for r in self.data['rows'] if r['case']=='c05')['query_ids']:answer[q]='U'
  if fault=='control':answer[self.data['rows'][0]['query_ids'][0]]='U'
  if fault=='wire':answer={}
  return json.dumps(answer,ensure_ascii=False),{'backend':'offline_fixture','model_requested':e.plan.MODEL,'usage':None if fault=='usage' else [{'input_tokens':0,'output_tokens':0}]}


class NamedTargetDiagnosticTests(unittest.TestCase):
 def execute(self,tmp,f):
  root=Path(tmp)/'review';e.plan.prepare(root)
  return root,e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_fixed_first_parent_three_views_only_one_question_field_changes(self):
  views=e.plan.views();self.assertEqual([(v['method'],v['characters'],v['parent_slot']) for v in views],[('original',495,9),('neutral',503,9),('named',503,9)])
  dense=e.plan.prototype.dense;original=dense.parse(views[0]['prompt']);g,r=views[0]['selected_group'],views[0]['selected_rule']
  for v in views[1:]:
   value=dense.parse(v['prompt']);self.assertEqual(value['groups'][g]['rules'][r]['choose'],'先摆书后讲故事')
   value['groups'][g]['rules'][r]['question']=original['groups'][g]['rules'][r]['question'];self.assertEqual(value,original)
  self.assertTrue(all(v['parent_answer_sha256']==views[0]['parent_answer_sha256'] for v in views))

 def test_eight_fixture_calls_keep_all12cases_and_repeat_requests_identical(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Fixture();root,r=self.execute(tmp,f)
   self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(8,'complete',0))
   for m,c in (('original',11),('neutral',11),('named',12)):
    self.assertEqual(r['scores']['methods'][m]['strict_both_reads']['joint'],{'planned':12,'correct':c,'missing':0})
    hashes=[x['request_sha256'] for x in r['records'] if x['kind']=='read' and x['method']==m];self.assertEqual(hashes[0],hashes[1])
   self.assertEqual((r['scores']['new_extractions'],r['scores']['inherited_parents'],r['scores']['answers_per_case_per_view']),(0,1,4))
   self.assertFalse(r['scores']['independent_semantic_acceptance'])
   with self.assertRaises(FileExistsError):e.run(root,root/'fixture',f,lambda _: {},simulated=True)

 def test_neutral_recovery_is_reported_without_uniquely_accepting_name_hypothesis(self):
  with tempfile.TemporaryDirectory() as tmp:
   _,r=self.execute(tmp,Fixture(neutral_fixes=True))
   self.assertEqual(r['scores']['methods']['neutral']['strict_both_reads']['joint']['correct'],12)
   self.assertEqual(r['scores']['methods']['named']['strict_both_reads']['joint']['correct'],12)
   self.assertFalse(r['scores']['independent_semantic_acceptance'])

 def test_bad_selection_mode_and_budget_do_not_repair_or_reflow(self):
  p=e.plan.views()[0]['prompt'];proto=e.plan.prototype
  for name,mode,cap in (('missing','named',1536),('先摆书后讲故事','foreign',1536),('先摆书后讲故事','named',500)):
   with self.subTest(mode=mode),self.assertRaises(ValueError):proto.modify(p,name,mode,cap)

 def test_control_wire_usage_and_final_failure_close_without_retry(self):
  for fault,at in (('control',2),('wire',3),('usage',1),('transport',8)):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
    f=Fixture(fault,at);_,r=self.execute(tmp,f);self.assertEqual((f.calls,r['status'],r['unused_slots_expire']),(at,'stopped',8-at))

 def test_all_static_requests_exclude_old_responses_scores_and_binding_metadata(self):
  slots=e.plan.slots();self.assertEqual([s['kind'] for s in slots],['none','full']+['read']*6)
  for slot in slots:
   req=e.plan.request(slot);self.assertEqual(req['model'],'gpt-6.1-sol')
   self.assertNotIn('parent_answer_sha256',req['prompt']);self.assertNotIn('source_name_anchor',req['prompt'])
  with self.assertRaises(ValueError):e.plan.request(dict(slots[-1],generation=1))

 def test_unapproved_exclusive_frozen_inputs_reject_drift(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'review';p=e.plan.prepare(root)
   self.assertFalse(p['approved']);self.assertFalse(p['new_service_authority']);self.assertEqual(len(e.plan.read(root/'static-requests.json')),8)
   self.assertEqual(e.plan.read(root/'dynamic-rules.json')['slots'],[]);self.assertTrue(e.plan.verify(root))
   with self.assertRaises(FileExistsError):e.plan.prepare(root)
   (root/'views.public.json').write_text('[]')
   with self.assertRaises(ValueError):e.plan.verify(root)


if __name__=='__main__':unittest.main()
