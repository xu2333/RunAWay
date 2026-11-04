"""Offline review entrypoint checked with the measured archived response."""
import contextlib,copy,importlib.util,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_memory_bridge_tests',ROOT/'scripts/review_memory.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ReviewMemoryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=v.p.read(ROOT/'benchmarks/source-id-review-v1/measured.synthetic.json')
  cls.record=next(r for r in cls.data['records']if r['kind']=='review')
  cls.answer=v.m.parse_answer(cls.record['raw'])
 def prepare(self,root,sources=None):
  v.m.prepare(sources or self.data['sources']['f7s'],'coverage',1536,root/'original')
  v.prepare(root/'original',self.data['draft'],root/'review');return root/'review'
 def test_exact_measured_request_without_model_and_original_bundle_preserved(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);prepared=self.prepare(root)
   expected=dict(self.record['request']);expected.pop('model')
   self.assertEqual(v.m.read_json(prepared/'request.private.json'),expected)
   self.assertEqual(v.prepared(prepared)[0],self.data['sources']['f7s'])
   self.assertEqual(v.m.prepared(root/'original')[0],self.data['sources']['f7s'])
   self.assertEqual(prepared.stat().st_mode&0o077,0)
   self.assertTrue(all(f.stat().st_mode&0o077==0 for f in prepared.iterdir()))
 def test_import_and_export_keep381public_bytes_and_unverified_flags(self):
  with tempfile.TemporaryDirectory()as tmp,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   root=Path(tmp);prepared=self.prepare(root);result=v.import_answer(prepared,self.answer,root/'candidate')
   self.assertEqual(result['characters'],381)
   self.assertFalse(result['behavioral_fidelity_verified']);self.assertFalse(result['semantic_support_verified'])
   self.assertFalse(result['source_coverage_verified']);self.assertEqual(result['model_calls'],0)
   expected=self.record['card']['prompt'];self.assertEqual((root/'candidate/prompt.md').read_text(),expected)
   exported=subprocess.run([sys.executable,'-B','-m','runaway','export',str(root/'candidate/portable.json')],cwd=ROOT,text=True,capture_output=True)
   self.assertEqual(exported.returncode,0,exported.stderr);self.assertEqual(exported.stdout,expected)
   backend.assert_not_called()
 def test_source_draft_request_manual_and_boolean_metadata_tampering_is_rejected(self):
  for name in('sources.private.json','draft.private.json','request.private.json','request.private.md','manifest.private.json'):
   with self.subTest(name=name),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);prepared=self.prepare(root);file=prepared/name
    if name.endswith('.md'):file.write_bytes(file.read_bytes().replace(b'\n',b'\r\n'))
    else:
     data=v.m.read_json(file)
     if name.startswith('sources'):data['sources'][0]['text']+='changed'
     elif name.startswith('draft'):data['name']+='changed'
     elif name.startswith('request'):data['prompt']+='changed'
     else:data['model_calls']=False
     file.write_text(json.dumps(data,ensure_ascii=False))
    with self.assertRaises(ValueError):v.import_answer(prepared,self.answer,root/'candidate')
    self.assertFalse((root/'candidate').exists())
 def test_foreign_id_old_schema_and_non_user_evidence_cannot_create_output(self):
  for fault in('id','old','role'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);prepared=self.prepare(root);answer=copy.deepcopy(self.answer)
    if fault=='old':answer=copy.deepcopy(self.data['draft'])
    else:answer['nodes'][0]['decisions'][0]['source_id']='absent'if fault=='id'else'm04'
    with self.assertRaises(ValueError):v.import_answer(prepared,answer,root/'candidate')
    self.assertFalse((root/'candidate').exists())
 def test_whole_message_limit_is_explicit_before_preparation_without_truncation(self):
  sources=copy.deepcopy(self.data['sources']['f7s']);sources['sources'][-1]['text']='x'*2001
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);v.m.prepare(sources,'coverage',1536,root/'original')
   with self.assertRaisesRegex(ValueError,'2000'):v.prepare(root/'original',self.data['draft'],root/'review')
   self.assertFalse((root/'review').exists());self.assertEqual(v.m.prepared(root/'original')[0],sources)
 def test_demo_is_archived_replay_refuses_overwrite_and_errors_do_not_echo_source(self):
  with tempfile.TemporaryDirectory()as tmp,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   root=Path(tmp);result=v.demo(root/'demo')
   self.assertEqual(result['characters'],381);self.assertTrue(result['archived_fictional_fixture_replay'])
   self.assertFalse(result['fresh_generation']);backend.assert_not_called()
   with self.assertRaises(FileExistsError):v.demo(root/'demo')
   file=root/'bad.json';file.write_text('{PRIVATE_SOURCE_SECRET')
   stdout,stderr=io.StringIO(),io.StringIO()
   with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
    code=v.main(['import','--prepared',str(root/'missing'),'--answer',str(file),'--out',str(root/'new')])
   self.assertEqual(code,2);self.assertNotIn('PRIVATE_SOURCE_SECRET',stdout.getvalue()+stderr.getvalue())
if __name__=='__main__':unittest.main()
