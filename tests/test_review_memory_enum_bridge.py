"""Opt-in enum request entrypoint against the measured51-attempt archive."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('enum_review_bridge',ROOT/'scripts/review_memory.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class EnumReviewMemoryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=v.p.read(ROOT/'benchmarks/source-id-enum-repeat-v1/measured.synthetic.json')
  cls.record=next(x for x in cls.data['records']if x['kind']=='review'and x['parent']=='p3'and x['method']=='enumerated'and x['review_repeat']==0)
  cls.answer=v.m.parse_answer(cls.record['raw'])
 def prepare(self,root):
  v.m.prepare(self.data['sources']['f7s'],'coverage',1536,root/'original')
  v.prepare(root/'original',self.data['parents']['p3']['draft'],root/'review','enumerated');return root/'review'
 def test_explicit_enum_preparation_matches_exact_measured_request(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);folder=self.prepare(root);expected=dict(self.record['request']);expected.pop('model')
   self.assertEqual(v.m.read_json(folder/'request.private.json'),expected)
   manifest=v.m.read_json(folder/'manifest.private.json');self.assertEqual(manifest['request_schema'],'enumerated')
   self.assertIn('benchmarks/source-id-enum-v1/candidate.py',manifest['implementation_sha256'])
   self.assertEqual(v.prepared(folder)[0],self.data['sources']['f7s'])
   self.assertEqual(folder.stat().st_mode&0o077,0);self.assertTrue(all(f.stat().st_mode&0o077==0 for f in folder.iterdir()))
 def test_import_preserves395_public_characters_without_inheriting_demo_scores(self):
  with tempfile.TemporaryDirectory()as tmp,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   root=Path(tmp);folder=self.prepare(root);result=v.import_answer(folder,self.answer,root/'candidate')
   self.assertEqual(result['characters'],395);self.assertEqual(result['method'],'source-id-enum-v1')
   self.assertEqual((root/'candidate/prompt.md').read_text(),self.record['card']['prompt'])
   self.assertEqual(result['status'],'candidate_unvalidated');self.assertFalse(result['behavioral_fidelity_verified'])
   self.assertFalse(result['semantic_support_verified']);self.assertFalse(result['source_coverage_verified']);backend.assert_not_called()
 def test_mode_removal_foreign_mode_and_enum_implementation_drift_reject(self):
  for fault in('remove','foreign','boolean','implementation'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);folder=self.prepare(root);file=folder/'manifest.private.json';value=v.m.read_json(file)
    if fault=='remove':value.pop('request_schema')
    elif fault=='foreign':value['request_schema']='foreign'
    elif fault=='boolean':value['request_schema']=False
    else:value['implementation_sha256']['benchmarks/source-id-enum-v1/candidate.py']='0'*64
    file.write_text(json.dumps(value,ensure_ascii=False))
    with self.assertRaises(ValueError):v.import_answer(folder,self.answer,root/'candidate')
    self.assertFalse((root/'candidate').exists())
 def test_enum_membership_does_not_bypass_role_or_reference_binding(self):
  for source_id in('m05冒','m04'):
   with self.subTest(source_id=source_id),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp);folder=self.prepare(root);answer=copy.deepcopy(self.answer)
    answer['nodes'][0]['decisions'][0]['source_id']=source_id
    with self.assertRaises(ValueError):v.import_answer(folder,answer,root/'candidate')
    self.assertFalse((root/'candidate').exists())
 def test_enum_demo_cli_replays_archive_without_a_model_and_refuses_overwrite(self):
  with tempfile.TemporaryDirectory()as tmp,patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
   root=Path(tmp);self.assertEqual(v.main(['demo','--request-schema','enumerated','--out',str(root/'demo')]),0)
   self.assertEqual((root/'demo/prompt.md').read_text(),self.record['card']['prompt']);backend.assert_not_called()
   with self.assertRaises(FileExistsError):v.demo(root/'demo','enumerated')
 def test_new_enum_packet_size_is_checked_before_writing(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp);v.m.prepare(self.data['sources']['f7s'],'coverage',1536,root/'original')
   with patch.object(v.enum,'make_request',return_value={'prompt':'x'*256001,'schema':{}}):
    with self.assertRaisesRegex(ValueError,'packet'):v.prepare(root/'original',self.data['parents']['p3']['draft'],root/'review','enumerated')
   self.assertFalse((root/'review').exists())
if __name__=='__main__':unittest.main()
