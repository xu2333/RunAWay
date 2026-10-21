"""Frozen13-slot acceptance; injected answers are not model-quality evidence."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_long_trajectory import perfect
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen384_test_study',ROOT/'benchmarks/frozen384-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class Frozen384Tests(unittest.TestCase):
 def test_all_cards_original_and_requests_do_not_leak_oracle(self):
  products=s.cards();old=s.read(ROOT/'benchmarks/long-trajectory-v1/observed.synthetic.json');self.assertEqual(products,old['products']['384']);f=s.w.fixtures()
  for pid,bundle in products.items():
   self.assertLessEqual(len(bundle['prompt.md']),384);req=s.request_for(f,'card',pid,products);self.assertEqual(req,s.request_for(f,'repeat',pid,products));data=json.loads(req['prompt'].split('READER_INPUT_JSON:\n')[1]);self.assertEqual(data['material'],bundle['prompt.md']);self.assertEqual(data['queries'],f['queries']);self.assertNotIn('policies',data);self.assertNotIn('gold',data)
 def test_plan_balances_people_before_repeats_and_keeps_physical_calls(self):
  plan=s.plan();self.assertEqual(len(plan),13);self.assertEqual(len({tuple(slot) for slot in plan}),13);self.assertEqual(plan,json.loads(json.dumps(plan)));self.assertEqual(len({p for g,p in plan[1:5]}),4);self.assertEqual(len({p for g,p in plan[5:9]}),4);self.assertTrue(all(g=='repeat' for g,p in plan[9:]));self.assertEqual({p for g,p in plan if g=='full'},set(s.w.PEOPLE))
 def test_complete_fake_run_has13_unique_executions_but9_inputs(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   f=s.w.fixtures();products=s.cards();calls=[]
   def fake(prompt,model,**kwargs):
    calls.append(prompt);material=json.loads(prompt.split('READER_INPUT_JSON:\n')[1])['material'];pid=next((p for p in s.w.PEOPLE if material in [s.canonical(f['histories'][p]),products[p]['prompt.md']]),None);labels=perfect(f,pid) if pid else {};answer={q['id']:('U' if labels.get(q['id'],'U')=='U' else q['options'][labels[q['id']]]) for q in f['queries']};return s.canonical(answer),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(result['status'],'complete');self.assertEqual(len(calls),13);self.assertEqual(result['ledger']['execution_records'],13);self.assertEqual(result['ledger']['unique_request_fingerprints'],9);self.assertTrue(result['quality']['stable384_pass']);self.assertFalse(result['repeat_disagreements'])
   with self.assertRaises(FileExistsError):s.execute(out,backend=fake)
 def test_wire_failure_is_retained_and_stops_without_repair(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   calls=[]
   def fake(*args,**kwargs):calls.append(1);return '{"bad":"U"}',{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(len(calls),1);self.assertEqual(result['status'],'stopped');self.assertEqual(result['groups']['card']['joint']['missing'],160);self.assertTrue(result['rejected_answers']);self.assertFalse(result['quality']['stable384_pass'])
 def test_perfect_cards_cannot_replace_failed_contemporaneous_full(self):
  f=s.w.fixtures();raw={g:{p:{q['id']:('U' if perfect(f,p)[q['id']]=='U' else q['options'][perfect(f,p)[q['id']]]) for q in f['queries']} for p in s.w.PEOPLE} for g in ['card','repeat']};raw['none']={'shared':{q['id']:'U' for q in f['queries']}};result=s.analyze(f,raw);self.assertTrue(result['groups']['card']['strict_choice_pass']);self.assertFalse(result['quality']['contemporaneous_full_qualified']);self.assertFalse(result['quality']['stable384_pass'])
 def test_missing_and_actual_disagreement_are_not_conflated(self):
  f=s.w.fixtures();pid=s.w.PEOPLE[0];labels=perfect(f,pid);answer={q['id']:('U' if labels[q['id']]=='U' else q['options'][labels[q['id']]]) for q in f['queries']};raw={'card':{pid:answer},'repeat':{}};self.assertEqual(s.analyze(f,raw)['repeat_disagreements'],[]);changed=dict(answer);qid=next(q for q,v in answer.items() if v!='U');changed[qid]='U';raw['repeat'][pid]=changed;self.assertEqual(len(s.analyze(f,raw)['repeat_disagreements']),1)

if __name__=='__main__':unittest.main()
