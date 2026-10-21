import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from runaway import support_extract as s
from runaway.card import canonical,digest
from test_support_extract import ANSWER,SOURCES

class RelayoutCLITests(unittest.TestCase):
 def run_cli(self,profile,out,*extra):
  return subprocess.run([sys.executable,'-B','-m','runaway','relayout',str(profile),'--layout','rows','--out',str(out),*extra],capture_output=True,text=True)
 def test_relayout_rows_back_to_paragraph_without_calls_or_source_edits(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);profile=folder/'profile.json';original=s.bind(ANSWER,SOURCES);profile.write_text(json.dumps(original['profile.private.json']));before=profile.read_bytes();out=folder/'rows';result=self.run_cli(profile,out)
   self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['model_calls'],0);self.assertEqual(profile.read_bytes(),before)
   private=json.loads((out/'profile.private.json').read_text());self.assertEqual(private['answer'],ANSWER);self.assertEqual(private['provenance']['source_profile_id'],original['profile.private.json']['id']);self.assertFalse(json.loads((out/'summary.private.json').read_text())['behavioral_fidelity_verified'])
   restored=folder/'paragraph';result=subprocess.run([sys.executable,'-B','-m','runaway','relayout',str(out/'profile.private.json'),'--layout','paragraph','--out',str(restored)],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertEqual((restored/'prompt.md').read_text(),original['prompt.md']);self.assertNotEqual(self.run_cli(profile,out).returncode,0)
 def test_checksum_and_source_hash_damage_are_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);profile=folder/'profile.json';private=s.bind(ANSWER,SOURCES)['profile.private.json'];bad=copy.deepcopy(private);bad['answer']['name']='被改过的卡';profile.write_text(json.dumps(bad));self.assertNotEqual(self.run_cli(profile,folder/'bad-id').returncode,0)
   bad=copy.deepcopy(private);bad['sources']['sources'][0]['text']+='编辑';bad['id']=digest(canonical({k:v for k,v in bad.items() if k!='id'}));profile.write_text(json.dumps(bad));result=self.run_cli(profile,folder/'bad-source');self.assertNotEqual(result.returncode,0);self.assertIn('source checksum',result.stderr)
 def test_duplicate_keys_and_other_profile_types_are_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);profile=folder/'profile.json';profile.write_text('{"schema_version":1,"schema_version":2}');self.assertNotEqual(self.run_cli(profile,folder/'duplicate').returncode,0)
   profile.write_text(json.dumps({'schema_version':1,'artifact_type':'claim_profile'}));self.assertNotEqual(self.run_cli(profile,folder/'wrong-type').returncode,0)
 def test_overbudget_relayout_never_writes_a_truncated_card(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);profile=folder/'profile.json';answer=copy.deepcopy(ANSWER);answer['unknowns']=[''.join(chr(0x4e00+i*160+j) for j in range(160)) for i in range(4)];profile.write_text(json.dumps(s.bind(answer,SOURCES,16000)['profile.private.json']));out=folder/'overflow';result=self.run_cli(profile,out,'--budget-chars','300');self.assertNotEqual(result.returncode,0);self.assertIn('no truncation',result.stderr);self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
