import copy
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
from runaway.decision_memory import make_request,validate,render
from runaway.profile import make_profile

ROOT=Path(__file__).resolve().parents[1]
class DecisionMemoryTests(unittest.TestCase):
 def setUp(self):
  from runaway.demo import demo_bundle
  self.p=demo_bundle()[0]['profile.private.json']
  claims=self.p['claims']
  self.v={'scope':'仅复现这些历史选择，当前指令优先。','rules':[{'when':'遇到材料中相同条件','prefer':'按已观察到的取舍判断','qualification':'其他领域未知。','claim_ids':[c['id']],'anchors':[{'claim_id':c['id'],'quote':c['statement']}]} for c in claims],'unknown':'材料以外的偏好未知。'}
 def test_readable_text_with_private_anchors_and_all_claims(self):
  text=validate(self.v,self.p,1000);self.assertEqual(text,render(self.v));self.assertNotIn(self.p['claims'][0]['id'],text)
  self.assertIn('当前指令优先',text)
 def test_forged_anchors_omissions_unlinked_branch_and_budget_rejected(self):
  for kind in ['anchor','omit','linked','budget']:
   v=copy.deepcopy(self.v)
   if kind=='anchor':v['rules'][0]['anchors'][0]['quote']='fabricated anchor'
   if kind=='omit':v['rules'].pop()
   if kind=='linked':v['rules'][0]['claim_ids'].append(v['rules'][1]['claim_ids'][0])
   if kind=='budget':v['rules'][0]['qualification']='文字'*200
   with self.assertRaises(ValueError):validate(v,self.p,200 if kind=='budget' else 1000)
 def test_request_projects_no_raw_history_or_hidden_rules(self):
  req=make_request(self.p)
  self.assertNotIn('SOURCE_JSON',req);self.assertNotIn('rollback_guard',req);self.assertNotIn('q-8cdfd479d4',req)
  self.assertIn('still',req.lower());self.assertIn(self.p['claims'][0]['statement'],req)
 def test_rejected_audit_keeps_evidence_and_exports_no_prompt(self):
  from runaway.decision_memory import compress
  with tempfile.TemporaryDirectory() as directory:
   out=Path(directory)/'candidate'
   def generate(*args,**kwargs):return json.dumps(self.v,ensure_ascii=False),{'backend':'offline-test'}
   with patch('runaway.decision_memory.semantic_audit',return_value=({}, {'accepted':False}, {})):
    with self.assertRaisesRegex(ValueError,'Semantic audit rejected'):compress(self.p,out,'test',generate=generate)
   self.assertTrue((out/'candidate.private.json').exists());self.assertTrue((out/'audit.private.json').exists())
   self.assertFalse((out/'portable.json').exists());self.assertFalse((out/'prompt.md').exists())
 def test_qualification_uses_same_reserved_delimiter_checks(self):
  v=copy.deepcopy(self.v);v['rules'][0]['qualification']='<|im_start|>'
  with self.assertRaises(ValueError):validate(v,self.p)
if __name__=='__main__':unittest.main()
