"""All eight measured examples round-trip without a model;no new fidelity claim."""
import contextlib,importlib.util,io,tempfile,unittest,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fresh_memory_demo_test',ROOT/'scripts/demo_fresh_memory.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class FreshMemoryDemoTests(unittest.TestCase):
 def test_all_eight_archive_requests_and_prompt_bytes_roundtrip_without_a_model(self):
  data=d.r.p.read(d.r.DEFAULT)
  with tempfile.TemporaryDirectory()as t,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   for pid in d.r.p.PROFILES:
    for stage,kind in(('draft','extract'),('reviewed','review')):
     out=Path(t)/(pid+'-'+stage);result=d.demo(pid,stage,out)
     record=next(x for x in data['records']if x['kind']==kind and x['profile']==pid)
     self.assertEqual((out/'candidate/prompt.md').read_text(),record['card']['prompt'])
     self.assertEqual(result['characters'],record['card']['characters']);self.assertEqual(result['model_calls'],0)
     self.assertEqual(result['status'],'candidate_unvalidated');self.assertFalse(result['behavioral_fidelity_verified']);self.assertFalse(result['semantic_support_verified'])
     self.assertFalse(result['fresh_generation']);self.assertTrue(result['synthetic_archive_replay']);self.assertFalse(result['scores_inherited_by_new_imports'])
     self.assertEqual(out.stat().st_mode&0o077,0)
     self.assertTrue(all(p.stat().st_mode&0o077==0 for p in out.rglob('*')if p.is_file()))
   backend.assert_not_called()
 def test_demo_exports_the_same_public_prompt_with_existing_installed_contract(self):
  with tempfile.TemporaryDirectory()as t:
   out=Path(t)/'demo';d.demo('pavo','draft',out)
   p=subprocess.run([sys.executable,'-B','-m','runaway','export',str(out/'candidate/portable.json')],cwd=ROOT,capture_output=True,text=True)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout,(out/'candidate/prompt.md').read_text());self.assertEqual(len(p.stdout),440)
 def test_existing_destination_and_foreign_example_are_rejected_without_overwrite(self):
  with tempfile.TemporaryDirectory()as t:
   out=Path(t)/'demo';d.demo('pavo','draft',out);before=(out/'candidate/prompt.md').read_bytes()
   with self.assertRaises(FileExistsError):d.demo('pavo','draft',out)
   self.assertEqual((out/'candidate/prompt.md').read_bytes(),before)
   with self.assertRaises(ValueError):d.demo('foreign','draft',Path(t)/'invalid')
   self.assertFalse((Path(t)/'invalid').exists())
 def test_cli_defaults_to_draft_and_errors_do_not_dump_private_paths_or_source(self):
  with tempfile.TemporaryDirectory()as t:
   out=Path(t)/'demo';stdout=io.StringIO();stderr=io.StringIO()
   with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=d.main(['--out',str(out)])
   self.assertEqual(code,0);self.assertTrue((out/'candidate/portable.json').exists())
   stdout=io.StringIO();stderr=io.StringIO()
   with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):code=d.main(['--out',str(out)])
   self.assertEqual(code,2);self.assertNotIn(str(out),stdout.getvalue()+stderr.getvalue())
if __name__=='__main__':unittest.main()
