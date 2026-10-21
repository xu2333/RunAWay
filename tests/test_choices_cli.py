import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from runaway.portable import make_expression

class ChoicesCLITests(unittest.TestCase):
 def test_prepare_and_import_do_not_call_a_model(self):
  with tempfile.TemporaryDirectory() as name:
   folder=Path(name);card=folder/'card.json';qs=folder/'questions.json';answer=folder/'answer.json'
   card.write_text(json.dumps(make_expression('Local and reversible: prefer a prototype.','fixture','test')))
   qs.write_text(json.dumps([{'id':'q1','scenario':'Local and reversible?','options':{'A':'Make a prototype','B':'Map the structure','C':'Interview first'}}]))
   answer.write_text(json.dumps({'q1':'Make a prototype'}))
   run=lambda *args:subprocess.run([sys.executable,'-B','-m','runaway','choices',*args],capture_output=True,text=True)
   prep=run('prepare','--card',str(card),'--questions',str(qs),'--answer-format','text');self.assertEqual(prep.returncode,0,prep.stderr)
   p=json.loads(prep.stdout);self.assertEqual(p['model_calls'],0);self.assertEqual(p['schema']['properties']['q1']['enum'],['Make a prototype','Map the structure','Interview first','U'])
   imported=run('import','--questions',str(qs),'--answer',str(answer),'--answer-format','text');self.assertEqual(imported.returncode,0,imported.stderr)
   self.assertEqual(json.loads(imported.stdout)['choices']['q1'],{'label':'A','text':'Make a prototype','unknown':False,'raw':'Make a prototype'})
   answer.write_text(json.dumps({'q1':'Make a prototype.'}));self.assertNotEqual(run('import','--questions',str(qs),'--answer',str(answer),'--answer-format','text').returncode,0)
 def test_duplicate_keys_are_rejected_before_choice_decoding(self):
  from runaway.cli import read_choice_json
  with tempfile.TemporaryDirectory() as name:
   path=Path(name)/'answer.json'
   for raw in ['{"q1":"U","q1":"A"}', '{"q1":NaN}']:
    path.write_text(raw)
    with self.assertRaises(ValueError):read_choice_json(path)

if __name__=='__main__':unittest.main()
