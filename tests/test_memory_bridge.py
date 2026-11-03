"""Offline user bridge checks against archived model output; no fresh inference."""
import contextlib,copy,importlib.util,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('memory_bridge_tests',ROOT/'scripts/memory.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MemoryBridgeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=m.read_json(ROOT/'benchmarks/ambiguous-source-repeat-v1/measured.synthetic.json',2000000)
  cls.sources=cls.data['sources']['c2v'];cls.good=next(r for r in cls.data['records']if r['slot']==7)
 def prepare(self,root,method='coverage'):
  m.prepare(self.sources,method,1536,root/'prepared');return root/'prepared'
 def test_prepared_json_matches_the_measured_request_without_provider_model(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);prepared=self.prepare(root);req=m.read_json(prepared/'request.private.json')
   expected=dict(self.good['request']);expected.pop('model')
   self.assertEqual(req,expected)
   self.assertEqual(m.prepared(prepared)[0],self.sources)
 def test_import_is_byte_identical_and_uses_existing_export_and_harness_adapter(self):
  with tempfile.TemporaryDirectory()as tmp,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   root=Path(tmp);p=self.prepare(root);out=root/'candidate'
   result=m.import_answer(p,m.parse_answer(self.good['raw']),out)
   self.assertEqual((out/'prompt.md').read_text(),self.good['card']['prompt'])
   self.assertEqual(result['model_calls'],0)
   exported=subprocess.run([sys.executable,'-B','-m','runaway','export',str(out/'portable.json')],cwd=ROOT,text=True,capture_output=True)
   self.assertEqual(exported.returncode,0,exported.stderr);self.assertEqual(exported.stdout,self.good['card']['prompt'])
   project=root/'harness';project.mkdir()
   attach=subprocess.run([sys.executable,'-B','-m','runaway','attach',str(out/'portable.json'),'--project',str(project),'--target','codex,claude,opencode,antigravity,deepseek','--dry-run'],cwd=ROOT,text=True,capture_output=True)
   self.assertEqual(attach.returncode,0,attach.stderr);self.assertEqual(list(project.iterdir()),[])
   backend.assert_not_called()
 def test_all_published_v3_producer_cards_round_trip_including_losing_cards(self):
  folders=('extraction-readiness-v1','object-coverage-comparison-v1','source-coverage-repeat-v1','ambiguous-source-repeat-v1','remaining-source-repeat-v1')
  checked=0
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for folder in folders:
    path=ROOT/'benchmarks'/folder/'measured.synthetic.json'
    self.assertEqual(m.provenance.sha(path),path.with_suffix('.sha256').read_text().strip())
    data=m.read_json(path,5000000);records=data['records']if 'records'in data else[data['record']]
    for rec in records:
     if 'card'not in rec:continue
     body=json.loads(rec['request']['prompt'].split('\nGRAPH_INPUT_JSON:\n')[1])
     sources=body['sources'];method='coverage'if rec.get('method')=='object-coverage-guidance-v1'else'baseline'
     expected=dict(rec['request']);expected.pop('model')
     self.assertEqual(m.request(sources,method,1536),expected)
     prepared=root/str(checked)/'request';m.prepare(sources,method,1536,prepared)
     out=root/str(checked)/'candidate';m.import_answer(prepared,m.parse_answer(rec['raw']),out)
     self.assertEqual((out/'prompt.md').read_text(),rec['card']['prompt'])
     checked+=1
  self.assertEqual(checked,36)
 def test_unsupported_anchor_fails_before_output_and_never_repairs(self):
  answer=m.parse_answer(self.good['raw']);answer['nodes'][0]['decisions'][0]['quote']='UNSUPPORTED_QUOTE'
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);p=self.prepare(root)
   with self.assertRaises(ValueError):m.import_answer(p,answer,root/'candidate')
   self.assertFalse((root/'candidate').exists())
 def test_changed_source_json_or_manual_request_is_rejected(self):
  for name in('sources.private.json','request.private.json','request.private.md'):
   with self.subTest(name=name),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);p=self.prepare(root);f=p/name
    if name.endswith('.md'):f.write_text(f.read_text()+' ALTERED_MANUAL_REQUEST')
    else:
     value=m.read_json(f)
     if name.startswith('sources'):value['sources'][0]['text']+=' ALTERED_SOURCE'
     else:value['prompt']+=' ALTERED_PROMPT'
     f.write_text(json.dumps(value,ensure_ascii=False))
    with self.assertRaises(ValueError):m.import_answer(p,m.parse_answer(self.good['raw']),root/'candidate')
    self.assertFalse((root/'candidate').exists())
 def test_structurally_valid_losing_cards_are_not_promoted_to_verified_fidelity(self):
  newer=m.read_json(ROOT/'benchmarks/remaining-source-repeat-v1/measured.synthetic.json',5000000)
  cases=[(self.data,next(r for r in self.data['records']if r['slot']==19),'baseline',312),
         (newer,next(r for r in newer['records']if r['slot']==49),'coverage',240)]
  for data,bad,method,characters in cases:
   with self.subTest(method=method),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);p=root/'prepared';m.prepare(data['sources'][bad['profile']],method,1536,p)
    result=m.import_answer(p,m.parse_answer(bad['raw']),root/'candidate')
    self.assertEqual(result['characters'],characters);self.assertFalse(result['behavioral_fidelity_verified'])
    self.assertFalse(result['semantic_support_verified']);self.assertIn('import.private.json',result['private_files'])
 def test_ambiguous_json_and_oversize_input_are_not_silently_normalized(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);p=root/'sources.json';p.write_text('{"schema_version":1,"sources":[{"id":"s","episode_id":"e","role":"assistant","role":"user","text":"SECRET"}]}')
   with self.assertRaises(ValueError):m.source_file(p)
   p=root/'resume.txt';p.write_text('x'*64001)
   with self.assertRaises(ValueError):m.source_file(p)
 def test_existing_output_and_private_error_content_are_preserved(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);p=self.prepare(root);out=root/'candidate';out.mkdir();(out/'marker').write_text('keep')
   with self.assertRaises(FileExistsError):m.import_answer(p,m.parse_answer(self.good['raw']),out)
   self.assertEqual((out/'marker').read_text(),'keep')
   answer=root/'answer.json';answer.write_text('{"PRIVATE_ERROR_SECRET":}')
   stdout,stderr=io.StringIO(),io.StringIO()
   with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
    code=m.main(['import','--prepared',str(p),'--answer',str(answer),'--out',str(root/'new')])
   self.assertEqual(code,2);self.assertNotIn('PRIVATE_ERROR_SECRET',stdout.getvalue()+stderr.getvalue())
 def test_method_choice_is_explicit_and_private_bundle_permissions_are_restricted(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);p=self.prepare(root)
   self.assertEqual(p.stat().st_mode&0o077,0)
   self.assertTrue(all(f.stat().st_mode&0o077==0 for f in p.iterdir()))
   with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):m.main(['prepare','--input','resume.txt','--out',str(root/'other')])
if __name__=='__main__':unittest.main()
