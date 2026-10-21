import copy
import io
from contextlib import redirect_stdout
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fresh_boundary_study',ROOT/'benchmarks/fresh-boundary-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);w=s.w
from runaway.card import canonical


def perfect(f):
 answers={p:{} for p in w.PEOPLE};scopes=copy.deepcopy(answers)
 for case in f['cases']:
  for p in w.PEOPLE:
   for order in case['orders']:
    qid=order['public']['id'];gold=case['gold'][p];answers[p][qid]='U' if gold=='U' else next(k for k,v in order['semantic_options'].items() if v==gold);scopes[p][qid]=case['scope_gold'][p]
 return answers,scopes


def mock_extraction(f,pid):
 sources=f['histories'][pid]['sources'];branches=[]
 for axis,actions in w.CHOICES[pid].items():
  contexts=[r for r in sources if r['role']=='user' and r['text'] in w.HISTORY_CONTEXT[axis]]
  for index,(context,action) in enumerate(zip(contexts,actions)):
   start=sources.index(context);following=sources[start+1:];decision=next(r for r in following if r['role']=='user' and (r['text'].startswith('还是刚才') if index==0 else r['text'].startswith('这次我明确')))
   branches.append({'when':context['text'],'choose':w.ACTIONS[axis][action],'priority':index,'decisions':[{'source_id':decision['id'],'quote':decision['text']}],'contexts':[{'source_id':context['id'],'quote':context['text']}],'supersedes':[]})
 return {'name':'离线管道测试团子','tagline':'这是测试夹具，不是模型输出','branches':branches,'unknowns':['其他条件和领域未知。']}

class FreshBoundaryTests(unittest.TestCase):
 def test_new_world_denominators_and_independent_hand_table(self):
  f=w.fixtures();a,c=perfect(f);score=w.evaluate(f,a,c)
  self.assertEqual((len(f['cases']),len(f['queries']),score['known']['planned'],score['unknown']['planned']),(32,92,40,88));self.assertTrue(score['strict_choice_pass']);self.assertEqual(score['scope_choice_joint']['correct'],128)
  reasons=score['by_unknown_reason'];self.assertEqual(reasons['unobserved_domain']['planned'],64);self.assertEqual(reasons['outside_observed_conditions']['planned'],16);self.assertEqual(reasons['ambiguous']['planned'],4);self.assertEqual(reasons['known_action_not_offered']['planned'],4)
 def test_scope_and_choice_errors_remain_separate(self):
  f=w.fixtures();a,c=perfect(f);c['t04a'][f['queries'][0]['id']]='bogus';score=w.evaluate(f,a,c);self.assertTrue(score['strict_choice_pass']);self.assertEqual(score['scope']['correct'],127);self.assertEqual(score['scope_choice_joint']['correct'],127)
  unknown={p:{q['id']:'U' for q in f['queries']} for p in w.PEOPLE};score=w.evaluate(f,unknown);self.assertEqual(score['known']['correct'],0);self.assertEqual(score['unknown']['correct'],88);self.assertFalse(score['strict_choice_pass'])
 def test_order_variants_must_all_be_right(self):
  f=w.fixtures();a,c=perfect(f);case=f['cases'][0];qid=case['orders'][0]['public']['id'];a['t04a'][qid]='U';score=w.evaluate(f,a,c);self.assertEqual(score['known']['correct'],39);self.assertFalse(score['strict_choice_pass'])
 def test_source_only_extraction_and_material_only_reader(self):
  f=w.fixtures();req=s.request_for(f,'extraction','t04a',{});payload=json.loads(req['prompt'].split('EXTRACTION_INPUT_JSON:\n')[1]);self.assertEqual(payload['sources'],f['histories']['t04a']);self.assertNotIn('policies',payload)
  req=s.request_for(f,'luna_scoped_full','t04a',{});payload=json.loads(req['prompt'].split('READER_INPUT_JSON:\n')[1]);self.assertEqual(set(payload),{'material','queries'});self.assertEqual(payload['material'],canonical(f['histories']['t04a']));self.assertEqual(payload['queries'],f['queries'])
 def test_mock_products_fit_without_truncation_and_do_not_enter_static_plan(self):
  f=w.fixtures()
  for pid in w.PEOPLE:
   card=s.extractor.bind(mock_extraction(f,pid),f['histories'][pid],768);self.assertLessEqual(len(card['prompt.md']),768);self.assertFalse(card['summary.private.json']['behavioral_fidelity_verified'])
  self.assertEqual(len(s.plan()),56);self.assertEqual(len({tuple(slot) for slot in s.plan()}),56)
 def test_single_use_executor_with_fake_backend_and_invalid_product_accounting(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   f=w.fixtures();a,c=perfect(f);requests=[]
   def fake(prompt,model,**kwargs):
    requests.append(prompt)
    if 'EXTRACTION_INPUT_JSON:\n' in prompt:
     data=json.loads(prompt.split('EXTRACTION_INPUT_JSON:\n')[1]);pid=next(p for p in w.PEOPLE if f['histories'][p]==data['sources']);value=mock_extraction(f,pid)
     if pid=='t04a':value['branches'][0]['decisions'][0]['quote']='not present in source'
    else:
     data=json.loads(prompt.split('READER_INPUT_JSON:\n')[1]);pid=next((p for p in w.PEOPLE if canonical(f['histories'][p])==data['material']),'t11b');value={}
     for q in f['queries']:
      label=a[pid][q['id']];choice='U' if label=='U' else q['options'][label];value[q['id']]={'scope':c[pid][q['id']],'choice':choice} if '先报告scope' in prompt else choice
    return canonical(value),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(result['status'],'completed_with_invalid_products');self.assertEqual(len(requests),48);self.assertEqual(len(result['skipped']),8);self.assertEqual(result['ledger']['execution_records'],48);self.assertIn('t04a',result['invalid_products']);self.assertFalse(result['quality']['luna_standard']['stable_transfer_pass'])
   with self.assertRaises(FileExistsError):s.execute(out,backend=fake)

 def test_schema_failure_stops_all_calls_and_keeps_denominators(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   calls=[]
   def fake(*args,**kwargs):calls.append(1);return canonical({'not_a_query':'U'}),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):result=s.execute(out,backend=fake)
   self.assertEqual(result['status'],'stopped');self.assertEqual(len(calls),1);self.assertEqual(result['groups']['luna_standard_full']['joint']['planned'],128);self.assertEqual(result['groups']['luna_standard_full']['joint']['missing'],128);self.assertEqual(len(result['rejected_answers']),1)

if __name__=='__main__':unittest.main()
