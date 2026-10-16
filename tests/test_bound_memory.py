import copy
import unittest
import tempfile
import json
import subprocess
from pathlib import Path
from runaway.bound_memory import bind,make_request
from runaway.demo import demo_bundle


class BoundMemoryTests(unittest.TestCase):
 def setUp(self):
  self.profile=demo_bundle()[0]['profile.private.json'];self.value={'scope':'仅描述已观察到的取舍。','clauses':[{'claim_ids':[c['id']],'text':c['statement']} for c in self.profile['claims']],'unknown':'范围外未知。'}
 def test_original_facets_bound_by_code_no_quote_reconstruction(self):
  text,binding=bind(self.value,self.profile,16000)
  self.assertEqual(len(binding['bindings']),len(self.profile['claims']))
  self.assertTrue(all(row['original_facets'] for row in binding['bindings']))
  self.assertNotIn(self.profile['claims'][0]['id'],text)
  self.assertIn('No hidden policies',make_request(self.profile,1000))
 def test_omitted_repeated_forged_or_damaged_clauses_fail(self):
  for mode in ['omit','duplicate','unknown','damaged']:
   v=copy.deepcopy(self.value)
   if mode=='omit':v['clauses'].pop()
   if mode=='duplicate':v['clauses'][1]['claim_ids']=v['clauses'][0]['claim_ids']
   if mode=='unknown':v['clauses'][0]['claim_ids']=['fabricated']
   if mode=='damaged':v['clauses'][0]['text']+='\ufffd'
   with self.assertRaises(ValueError):bind(v,self.profile,16000)
  with self.assertRaisesRegex(ValueError,'no truncation'):bind(self.value,self.profile,200)
 def test_offline_cli_import_exports_unvalidated_candidate_with_private_bindings(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);profile=root/'profile.json';answer=root/'answer.json'
   profile.write_text(json.dumps(self.profile));answer.write_text(json.dumps(self.value))
   result=subprocess.run(['python3','-m','runaway','profile','bound-import',str(profile),'--answer',str(answer),'--budget-chars','16000','--out',str(root/'result')],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   summary=json.loads((root/'result/summary.private.json').read_text());self.assertEqual(summary['model_calls'],0);self.assertFalse(summary['semantic_preservation_verified'])
   portable=json.loads((root/'result/portable.json').read_text());self.assertNotIn('bindings',portable);self.assertEqual(portable['status'],'candidate_unvalidated')
 def test_bound_prompt_survives_all_existing_file_adapters_without_private_bindings(self):
  from runaway.bound_memory import import_candidate
  from runaway.adapters import attach,detach,TARGETS
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);project=root/'project';project.mkdir()
   import_candidate(self.value,self.profile,root/'candidate',16000)
   expression=json.loads((root/'candidate/portable.json').read_text());attach(expression,project,list(TARGETS))
   for name in {value[0] for value in TARGETS.values()}:
    text=(project/name).read_text();self.assertEqual(text.count(expression['text']),1);self.assertNotIn('original_facets',text)
   detach(project)
   self.assertTrue(all(not (project/value[0]).exists() for value in TARGETS.values()))


if __name__=='__main__':unittest.main()
