import copy
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('long_budget_test_study',ROOT/'benchmarks/long-trajectory-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);w=s.w


def perfect(f,pid):
 result={}
 for case in f['cases']:
  for order in case['orders']:
   gold=case['gold'][pid];result[order['public']['id']]='U' if gold=='U' else next(key for key,value in order['semantic_options'].items() if value==gold)
 return result


def mock_extraction(f,pid):
 rows=f['histories'][pid]['sources'];branches=[]
 for axis,choices in w.base.CHOICES[pid].items():
  for index,action in enumerate(choices):
   context=w.base.HISTORY_CONTEXT[axis][index];source=next(r for r in reversed(rows) if r['role']=='user' and context in r['text']);position=rows.index(source);decision=rows[position+2]
   branches.append({'when':context,'choose':w.base.ACTIONS[axis][action],'priority':index,'decisions':[{'source_id':decision['id'],'quote':decision['text']}],'contexts':[{'source_id':source['id'],'quote':context}],'supersedes':[]})
 return {'name':'离线测试团子','tagline':'测试数据，不是模型结论','branches':branches,'unknowns':['未观察条件和领域未知。']}

class LongTrajectoryTests(unittest.TestCase):
 def test_denominators_cohorts_and_always_unknown_control(self):
  f=w.fixtures();answers={p:perfect(f,p) for p in w.PEOPLE};score=w.evaluate(f,answers)
  self.assertEqual((len(f['cases']),len(f['queries']),score['known']['planned'],score['unknown']['planned']),(40,116,43,117));self.assertTrue(score['strict_choice_pass']);self.assertEqual(score['cohorts']['consumed_regression']['joint']['planned'],128);self.assertEqual(score['cohorts']['new_stress']['known']['planned'],3)
  unknown={p:{q['id']:'U' for q in f['queries']} for p in w.PEOPLE};score=w.evaluate(f,unknown);self.assertEqual(score['known']['correct'],0);self.assertEqual(score['unknown']['correct'],117);self.assertFalse(score['strict_choice_pass'])
 def test_long_source_contains_current_and_superseded_user_choices(self):
  f=w.fixtures()
  for pid in w.PEOPLE:
   rows=f['histories'][pid]['sources'];self.assertEqual(len(rows),90);self.assertGreater(sum(len(r['text']) for r in rows),5000);self.assertLess(len(s.canonical(f['histories'][pid]).encode()),96000)
   decisions=[r for r in rows if r['role']=='user' and any(x in r['text'] for x in ['我当时明确决定','这一阶段我重新决定','以我这次明确决定为准'])];self.assertEqual(len(decisions),18);self.assertEqual(sum('以我这次明确决定为准' in r['text'] for r in decisions),6)
   for axis,choices in w.base.CHOICES[pid].items():
    for state,action in enumerate(choices):
     context=w.base.HISTORY_CONTEXT[axis][state];source=next(r for r in reversed(rows) if context in r['text']);position=rows.index(source);self.assertIn(w.base.ACTIONS[axis][action],rows[position+2]['text']);self.assertIn('2026-09-01',source['text'])
 def test_new_scope_gap_and_three_way_cases_match_hand_oracle(self):
  f=w.fixtures();new=[c for c in f['cases'] if c['cohort']=='new_stress'];self.assertEqual(len(new),8)
  for case in new:
   if case['kind']=='supported_plus_gap':
    self.assertEqual(set(case['gold'].values()),{'U'});self.assertEqual(set(case['scope_gold'].values()),{'uncovered'});self.assertIn(w.GAP_CONTEXT[case['axis']],case['orders'][0]['public']['scenario']);self.assertNotIn('记录从未出现过',case['orders'][0]['public']['scenario'])
   else:self.assertEqual(case['gold'],w.THREE_HAND[case['axis']])
 def test_encoder_never_receives_gold_queries_or_other_users(self):
  f=w.fixtures();request=s.request_for(f,'extract_384','t04a',{});payload=json.loads(request['prompt'].split('EXTRACTION_INPUT_JSON:\n')[1]);self.assertEqual(payload['sources'],f['histories']['t04a']);self.assertEqual(payload['budget_characters'],384);self.assertNotIn('queries',payload);self.assertNotIn('policies',payload)
  full=s.request_for(f,'sol_full','t04a',{});short=s.request_for(f,'sol_short','t04a',{});a=json.loads(full['prompt'].split('READER_INPUT_JSON:\n')[1]);b=json.loads(short['prompt'].split('READER_INPUT_JSON:\n')[1]);self.assertEqual(a['queries'],b['queries']);self.assertNotEqual(a['material'],b['material']);self.assertEqual(full['schema'],short['schema'])
 def test_plan_roundtrip_and_budget_balance(self):
  plan=s.plan();self.assertEqual(len(plan),46);self.assertEqual(plan,json.loads(json.dumps(plan)));self.assertEqual(len({tuple(slot) for slot in plan}),46)
  self.assertEqual(sum(g.startswith('extract_') for g,p in plan),12);self.assertEqual([p for g,p in plan if g=='sol_384_repeat'],list(reversed(w.PEOPLE)))
 def test_invalid_budget_products_keep_denominators_and_single_use(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   f=w.fixtures();calls=[]
   def fake(prompt,model,**kwargs):
    calls.append(prompt)
    if 'EXTRACTION_INPUT_JSON:\n' in prompt:
     data=json.loads(prompt.split('EXTRACTION_INPUT_JSON:\n')[1]);pid=next(p for p in w.PEOPLE if f['histories'][p]==data['sources']);value=mock_extraction(f,pid)
     if data['budget_characters']==384:value['branches'][0]['decisions'][0]['quote']='not a source quote'
    else:
     data=json.loads(prompt.split('READER_INPUT_JSON:\n')[1]);pid=next((p for p in w.PEOPLE if s.canonical(f['histories'][p])==data['material']),'t04a');labels=perfect(f,pid);value={q['id']:('U' if labels[q['id']]=='U' else q['options'][labels[q['id']]]) for q in f['queries']}
    return s.canonical(value),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(result['status'],'completed_with_invalid_products');self.assertTrue(all('384:'+p in result['invalid_products'] for p in w.PEOPLE));self.assertEqual(result['groups']['sol_384']['joint']['missing'],160);self.assertEqual(result['groups']['sol_384_repeat']['joint']['missing'],160);self.assertEqual(len(result['completed_plan'])+len(result['skipped']),46);self.assertEqual(result['ledger']['execution_records'],len(calls));self.assertFalse(result['quality']['sol']['stable_384_transfer_pass'])
   with self.assertRaises(FileExistsError):s.execute(out,backend=fake)
 def test_wire_failure_stops_after_one_fake_call(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   calls=[]
   def fake(*args,**kwargs):calls.append(1);return '{"bad":"U"}',{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(result['status'],'stopped');self.assertEqual(len(calls),1);self.assertEqual(result['groups']['sol_full']['joint']['missing'],160);self.assertTrue(result['rejected_answers'])

if __name__=='__main__':unittest.main()
