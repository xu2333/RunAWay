"""Hand-oracle and executor controls, never synthetic model-quality claims."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('latent_transfer_tests',ROOT/'benchmarks/latent-transfer-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);w=s.w


def perfect(f,pid,uninformed=False):
 labels={}
 for case in f['cases']:
  gold=case['uninformed_gold'] if uninformed else case['gold'][pid]
  for order in case['orders']:labels[order['public']['id']]='U' if gold=='U' else next(k for k,v in order['semantic_options'].items() if v==gold)
 return labels


def mock_extraction(f,pid):
 rows=f['histories'][pid]['sources'];branches=[]
 for j,index in enumerate(w.TRAIN):
  episode='episode'+str(j+1);context=w.features(w.STATES[index]);source=next(r for r in rows if r['episode_id']==episode and context in r['text']);action=w.ACTIONS[w.predict(w.HIDDEN[pid],w.STATES[index])];decision=next(r for r in rows if r['episode_id']==episode and r['role']=='user' and '我最后明确选：'+action in r['text']);old=[r['id'] for r in rows if r['episode_id']==episode and r['role']=='user' and r['text'].startswith('早先')]
  branches.append({'when':'个人笔记自动整理；'+context,'choose':action,'priority':0,'decisions':[{'source_id':decision['id'],'quote':decision['text']}],'contexts':[{'source_id':source['id'],'quote':context}],'supersedes':old})
 return {'name':'离线测试团子','tagline':'只验证管线，不是模型结果','branches':branches,'unknowns':['候选有分歧时不猜；未定义取值和其他领域未知。']}

class LatentTransferTests(unittest.TestCase):
 def test_independent_oracles_and_nonidentifiability(self):
  f=w.fixtures();self.assertEqual(f['versions'],w.HAND_V);self.assertEqual(len(f['queries']),34)
  for pid in ['u06k','u42r']:
   versions=f['versions'][pid];self.assertEqual(len(versions),2);self.assertTrue(all(w.predict(versions[0],w.STATES[i])==w.predict(versions[1],w.STATES[i]) for i in w.TRAIN));witness=[c for c in f['cases'] if c['cohort']=='heldout_combination' and c['gold'][pid]=='U'];self.assertEqual(len(witness),2)
   for case in witness:self.assertNotEqual(w.predict(versions[0],case['states'][0]),w.predict(versions[1],case['states'][0]));self.assertIn(w.predict(w.HIDDEN[pid],case['states'][0]),[0,1])
 def test_denominators_personal_known_and_uninformed_control(self):
  f=w.fixtures();r=w.evaluate(f,{p:perfect(f,p) for p in w.PEOPLE});self.assertTrue(r['strict_pass']);self.assertEqual((r['joint']['planned'],r['known']['planned'],r['unknown']['planned']),(102,55,47));self.assertEqual(r['personal_known']['planned'],43);self.assertEqual(r['structural_known']['planned'],12);self.assertEqual(r['cohort_details']['heldout_combination']['personal_known']['planned'],14);self.assertEqual(r['cohort_details']['heldout_combination']['unknown']['planned'],4)
  unknown={p:{q['id']:'U' for q in f['queries']} for p in w.PEOPLE};r=w.evaluate(f,unknown);self.assertEqual(r['known']['correct'],0);self.assertEqual(r['unknown']['correct'],47)
  r=w.evaluate(f,{p:perfect(f,p,True) for p in w.PEOPLE});self.assertEqual(r['joint']['correct'],59);self.assertEqual(r['personal_known']['correct'],0)
 def test_queries_and_decoder_identical_across_users_no_oracle_in_encoder(self):
  f=w.fixtures();products={p:s.h.extractor.bind(mock_extraction(f,p),f['histories'][p],512) for p in w.PEOPLE};encoder=s.request_for(f,'extraction','u06k',{});data=json.loads(encoder['prompt'].split('EXTRACTION_INPUT_JSON:\n')[1]);self.assertEqual(data['sources'],f['histories']['u06k']);self.assertEqual(set(data),{'sources','budget_characters','fixed_header','fixed_guide'});self.assertNotIn('hidden_author_rules',encoder['prompt']);self.assertNotIn('hand_gold',encoder['prompt'])
  for group,pid in [('none','shared'),('full','u06k'),('own','u06k'),('tail','u06k'),('wrong','u06k')]:
   request=s.request_for(f,group,pid,products);self.assertTrue(request['prompt'].startswith(f['decoder_contract']));payload=json.loads(request['prompt'].split('READER_INPUT_JSON:\n')[1]);self.assertEqual(payload['queries'],f['queries']);self.assertNotIn('versions',payload)
 def test_donor_repeat_request_equal_and_raw_tail_character_match(self):
  f=w.fixtures();products={p:s.h.extractor.bind(mock_extraction(f,p),f['histories'][p],512) for p in w.PEOPLE}
  for pid in w.PEOPLE:
   donor=f['donors'][pid];self.assertEqual(s.request_for(f,'wrong',pid,products),s.request_for(f,'own',donor,products));self.assertEqual(len(s.raw_tail(f,pid,len(products[pid]['prompt.md']))),len(products[pid]['prompt.md']))
 def test_fixed_plan_and_full_gate_not_replaceable_by_cards(self):
  plan=s.plan();self.assertEqual(len(plan),31);self.assertEqual(len({tuple(x) for x in plan}),31);self.assertEqual(plan,json.loads(json.dumps(plan)));f=w.fixtures();raw={}
  for group in ['own','wrong']:
   raw[group]={}
   for pid in w.PEOPLE:
    labels=perfect(f,f['donors'][pid] if group=='wrong' else pid);raw[group][pid]={q['id']:('U' if labels[q['id']]=='U' else q['options'][labels[q['id']]]) for q in f['queries']}
  r=s.analyze(f,raw);self.assertTrue(r['groups']['own']['strict_pass']);self.assertTrue(r['wrong_against_donor']['strict_pass']);self.assertTrue(r['quality']['identity_specificity_verified']);self.assertFalse(r['quality']['contemporary_full_qualified']);self.assertFalse(r['quality']['strict_transport_pass'])
 def test_invalid_extraction_retains_three_dependent_missing_slots(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   f=w.fixtures();products={p:s.h.extractor.bind(mock_extraction(f,p),f['histories'][p],512) for p in w.PEOPLE};calls=[]
   def fake(prompt,model,**kwargs):
    calls.append(prompt)
    if 'EXTRACTION_INPUT_JSON:\n' in prompt:
     data=json.loads(prompt.split('EXTRACTION_INPUT_JSON:\n')[1]);pid=next(p for p in w.PEOPLE if f['histories'][p]==data['sources']);answer=mock_extraction(f,pid)
     if pid=='u06k':answer['branches'][0]['decisions'][0]['quote']='not a quote'
    else:
     material=json.loads(prompt.split('READER_INPUT_JSON:\n')[1])['material'];pid=next((p for p in w.PEOPLE if material in [s.canonical(f['histories'][p]),products[p]['prompt.md'],s.raw_tail(f,p,len(products[p]['prompt.md']))]),None);labels=perfect(f,pid) if pid else {};answer={q['id']:('U' if labels.get(q['id'],'U')=='U' else q['options'][labels[q['id']]]) for q in f['queries']}
    return s.canonical(answer),{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):r=s.execute(out,backend=fake)
   self.assertEqual(r['status'],'completed_with_invalid_products');self.assertEqual(len(calls),28);self.assertEqual(len(r['skipped']),3);self.assertEqual(r['groups']['own']['joint']['missing'],17);self.assertFalse(r['quality']['strict_transport_pass'])
   with self.assertRaises(FileExistsError):s.execute(out,backend=fake)
 def test_wire_failure_stops_at_first_call_without_repair(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   calls=[]
   def fake(*args,**kwargs):calls.append(1);return '{"bad":"U"}',{'usage':[{'input_tokens':1,'output_tokens':1}]}
   with redirect_stdout(io.StringIO()):r=s.execute(out,backend=fake)
   self.assertEqual(len(calls),1);self.assertEqual(r['status'],'stopped');self.assertEqual(r['groups']['own']['joint']['missing'],102);self.assertTrue(r['rejected_answers'])

if __name__=='__main__':unittest.main()
