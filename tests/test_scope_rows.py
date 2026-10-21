import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from runaway import support_extract as s
from runaway.scope_rows import parse_pairs,render_pairs
from test_support_extract import ANSWER,SOURCES

class ScopeRowsTests(unittest.TestCase):
 def test_reserved_characters_and_random_pairs_roundtrip(self):
  pairs=[('条件含「括号」→箭头\\n和实际\n换行\r','选择含」→和反斜杠\\'),('',''),('🌱甲','乙')]
  rng=random.Random(30);alphabet='条件选择「」→\\\n\r🌱ABC123'
  pairs.extend((''.join(rng.choice(alphabet) for _ in range(40)),''.join(rng.choice(alphabet) for _ in range(40))) for _ in range(80))
  body=render_pairs(pairs);self.assertEqual(parse_pairs(body),pairs);self.assertEqual(len(body.split('\n')),len(pairs));self.assertEqual(parse_pairs(render_pairs([])),[])
  for bad in ['not a row','「missing separator','「x」→bad\\x']:
   with self.assertRaises(ValueError):parse_pairs(bad)
 def test_paragraph_unchanged_rows_keep_priority_and_source(self):
  legacy=s.HEADER+ANSWER['name']+'｜'+ANSWER['tagline']+'\n'+s.GUIDE+'4%错误的对外结果不能撤回，我选默认自动处理。本地副本4%错误且可立即恢复、不外发，我选默认自动处理。\n未覆盖的错误率与用途未知。\n'
  self.assertEqual(s.render(ANSWER),legacy);self.assertEqual(s.bind(ANSWER,SOURCES),s.bind(ANSWER,SOURCES,layout='paragraph'))
  rows=s.bind(ANSWER,SOURCES,layout='rows');self.assertIn('「4%错误的对外结果不能撤回」→默认自动处理',rows['prompt.md']);self.assertLessEqual(len(rows['prompt.md']),768)
  self.assertEqual(rows['profile.private.json']['answer'],ANSWER);self.assertEqual(rows['profile.private.json']['sources'],SOURCES);self.assertEqual(rows['profile.private.json']['render_layout'],'rows');self.assertTrue(rows['summary.private.json']['condition_action_roundtrip_exact'])
  self.assertNotEqual(rows['portable.json']['id'],s.bind(ANSWER,SOURCES)['portable.json']['id'])
 def test_rows_still_reject_bad_evidence_and_overflow(self):
  bad=copy.deepcopy(ANSWER);bad['branches'][0]['decisions']=[{'source_id':'a1','quote':'我建议逐项确认。'}]
  with self.assertRaises(ValueError):s.bind(bad,SOURCES,layout='rows')
  bad=copy.deepcopy(ANSWER);bad['unknowns']=[''.join(chr(0x4e00+i*160+j) for j in range(160)) for i in range(4)]
  with self.assertRaisesRegex(ValueError,'no truncation'):s.bind(bad,SOURCES,300,layout='rows')
  with self.assertRaises(ValueError):s.bind(ANSWER,SOURCES,layout='guess')
 def test_cli_rows_import_and_generation_layout(self):
  with tempfile.TemporaryDirectory() as directory:
   folder=Path(directory);source=folder/'sources.json';answer=folder/'answer.json';source.write_text(json.dumps(SOURCES));answer.write_text(json.dumps(ANSWER));out=folder/'rows'
   result=subprocess.run([sys.executable,'-B','-m','runaway','distill','--input',str(source),'--answer',str(answer),'--out',str(out),'--layout','rows'],capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['model_calls'],0);self.assertEqual(json.loads((out/'summary.private.json').read_text())['render_layout'],'rows')
   observed=[]
   def backend(prompt,model,**kwargs):observed.append(prompt);return json.dumps(ANSWER),{'backend':'fixture'}
   s.generate(SOURCES,folder/'generated','fixture',backend=backend,layout='rows');self.assertEqual(len(observed),1);self.assertEqual(observed[0],s.make_request(SOURCES)['prompt']);self.assertEqual(json.loads((folder/'generated/request.private.json').read_text())['render_layout'],'rows')

if __name__=='__main__':unittest.main()
