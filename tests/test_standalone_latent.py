"""Removal binding and fail-closed acceptance; never model accuracy evidence."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_latent_transfer import perfect
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('standalone_latent_test',ROOT/'benchmarks/standalone-latent-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class StandaloneLatentTests(unittest.TestCase):
 def test_exactly_shared_prefix_removed_no_card_repair(self):
  f=s.w.fixtures();products=s.cards()
  for group,pid in s.plan():
   old=s.base.request_for(f,group,pid,products);new=s.request_for(f,group,pid,products);self.assertEqual({k:v for k,v in old.items() if k!='prompt'},{k:v for k,v in new.items() if k!='prompt'});self.assertEqual(old['prompt'],f['decoder_contract']+new['prompt']);self.assertEqual(len(old['prompt'])-len(new['prompt']),619)
  self.assertEqual(products,s.read(ROOT/'benchmarks/latent-transfer-v1/observed.synthetic.json')['products'])
 def test19_call_interleaving_and_independent_repeats(self):
  p=s.plan();self.assertEqual(len(p),19);self.assertEqual(len({tuple(x) for x in p}),19);self.assertEqual(len({pid for g,pid in p[1:7]}),6);self.assertEqual(len({pid for g,pid in p[7:13]}),6);self.assertTrue(all(g=='wrong' for g,pid in p[13:]))
 def test_fake_complete19_calls13_inputs_and_exclusive_intent(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   f=s.w.fixtures();products=s.cards();calls=[]
   def fake(prompt,model,**kwargs):
    calls.append(prompt);material=json.loads(prompt.split('READER_INPUT_JSON:\n')[1])['material'];pid=next((p for p in s.w.PEOPLE if material in [s.canonical(f['histories'][p]),products[p]['prompt.md']]),None);labels=perfect(f,pid) if pid else {};answer={q['id']:('U' if labels.get(q['id'],'U')=='U' else q['options'][labels[q['id']]]) for q in f['queries']};return s.canonical(answer),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):r=s.execute(out,backend=fake)
   self.assertEqual(len(calls),19);self.assertEqual(r['ledger']['unique_request_fingerprints'],13);self.assertTrue(r['quality']['standalone_gate']);self.assertNotIn('tail',r['groups'])
   with self.assertRaises(FileExistsError):s.execute(out,backend=fake)
 def test_wire_failure_stops_after_one_attempt(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   calls=[]
   def fake(*args,**kwargs):calls.append(1);return '{"bad":"U"}',{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):r=s.execute(out,backend=fake)
   self.assertEqual(len(calls),1);self.assertEqual(r['status'],'stopped');self.assertEqual(r['groups']['own']['joint']['missing'],102);self.assertFalse(r['quality']['standalone_gate'])

if __name__=='__main__':unittest.main()
