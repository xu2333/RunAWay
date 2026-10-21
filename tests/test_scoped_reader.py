import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from runaway.choice_reader import make_request,decode_response
from runaway.portable import make_expression

QUERIES=[{'id':'q1','scenario':'条件已记录时怎么选？','options':{'A':'先等一天','B':'马上行动'}}]
class ScopedReaderTests(unittest.TestCase):
 def test_explicit_contract_uses_two_fields_without_changing_default(self):
  base=make_request('原卡',QUERIES,answer_format='text');scoped=make_request('原卡',QUERIES,answer_format='text',reader_mode='scoped')
  self.assertEqual(base['schema']['properties']['q1']['type'],'string');self.assertEqual(scoped['schema']['properties']['q1']['required'],['scope','choice']);self.assertIn('"material":"原卡"',scoped['prompt']);self.assertNotIn('只返回题号到所选做法完整原文或U的完整JSON',scoped['prompt'])
 def test_decoder_keeps_disagreement_instead_of_repairing_choice(self):
  raw={'q1':{'scope':'uncovered','choice':'先等一天'}}
  self.assertEqual(decode_response(QUERIES,raw,answer_format='text',reader_mode='scoped'),{'q1':'A'});self.assertEqual(raw['q1']['scope'],'uncovered')
  for bad in [{'q1':{'scope':'guessed','choice':'U'}},{'q1':{'scope':'determinate','choice':'相似但不是选项'}},{'q1':{'scope':'determinate','choice':'U','reason':'x'}},{'q1':'U'}]:
   with self.assertRaises(ValueError):decode_response(QUERIES,bad,answer_format='text',reader_mode='scoped')
 def test_cli_prepare_and_import_are_zero_call_and_scope_is_retained(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'q.json').write_text(json.dumps(QUERIES));(p/'card.json').write_text(json.dumps(make_expression('仅为测试','source','manual')));(p/'a.json').write_text(json.dumps({'q1':{'scope':'determinate','choice':'先等一天'}}))
   def call(*args):
    r=subprocess.run([sys.executable,'-B','-m','runaway','choices',*args],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);return json.loads(r.stdout)
   prepared=call('prepare','--card',str(p/'card.json'),'--questions',str(p/'q.json'),'--reader-mode','scoped','--answer-format','text');self.assertEqual(prepared['model_calls'],0)
   imported=call('import','--questions',str(p/'q.json'),'--answer',str(p/'a.json'),'--reader-mode','scoped','--answer-format','text');self.assertEqual(imported['choices']['q1']['scope'],'determinate');self.assertEqual(imported['choices']['q1']['label'],'A');self.assertEqual(imported['model_calls'],0)

if __name__=='__main__':unittest.main()
