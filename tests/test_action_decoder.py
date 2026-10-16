import unittest
from runaway.action_decoder import request,validate,evidence_issues
class ActionDecoderTests(unittest.TestCase):
 def test_maps_option_text_without_oracle_or_label_guessing(self):
  memory='可撤回时先尝试。';cases=[{'id':'q','question':'可以撤回。','A':'先完整规划。','B':'先试一试。'}]
  answer={'predictions':[{'id':'q','selection':'先试一试。','evidence':'可撤回时先尝试。'}]}
  self.assertEqual(validate(answer,memory,cases),{'q':'B'})
  swapped=[{**cases[0],'A':cases[0]['B'],'B':cases[0]['A']}]
  self.assertEqual(validate(answer,memory,swapped),{'q':'A'})
  self.assertNotIn('gold',request(memory,cases));self.assertNotIn('policy',request(memory,cases))
 def test_evidence_problems_reported_without_relabelling_choice(self):
  cases=[{'id':'q','question':'情境','A':'左','B':'右'}];a={'predictions':[{'id':'q','selection':'右','evidence':'虚构依据'}]}
  self.assertEqual(validate(a,'记忆',cases),{'q':'B'});self.assertEqual(len(evidence_issues(a,'记忆',cases)),1)
  with self.assertRaises(ValueError):validate(a,'记忆',cases,strict_evidence=True)
 def test_missing_duplicate_or_nonexistent_action_rejected(self):
  c=[{'id':'q','question':'情境','A':'左','B':'右'}]
  for rows in [[],[{'id':'q','selection':'B','evidence':'情境'}],[{'id':'q','selection':'unknown','evidence':''}]*2]:
   with self.assertRaises(ValueError):validate({'predictions':rows},'',c)
if __name__=='__main__':unittest.main()
