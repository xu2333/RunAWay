import copy
import json
from pathlib import Path
import tempfile
import unittest

from runaway.synthetic_metric_world import build_world,persona_events,resolve,parse_history
from runaway.synthetic_metric import freeze,evaluate,score,score_external,normalized_retention


class SyntheticMetricTests(unittest.TestCase):
 def test_literal_strength_exception_constraint_update_and_revocation_semantics(self):
  events=persona_events(['dot','morning','direct','auto','minimal'],1)
  def value(key,at,**context):return resolve(events,{'key':key,'at':at,'context':context})[0]
  self.assertEqual(value('feedback',3),'direct')  # Later weak preference cannot erase stronger evidence.
  self.assertEqual(value('feedback',4,public=True),'gentle')
  self.assertEqual(value('auto',6,irreversible=True),'ask')
  self.assertEqual(value('auto',16,irreversible=True),'auto')  # Hard rule was explicitly revoked.
  self.assertEqual(value('time',8),'evening');self.assertEqual(value('time',10),'morning')
  self.assertEqual(value('layout',12),'restore');self.assertEqual(value('layout',13),'minimal')
  self.assertEqual(value('mark',11),'U');self.assertEqual(value('film',16),'U')
  events.append({'day':17,'id':'r17','op':'revoke','target':'r15'})
  self.assertEqual(value('auto',18,irreversible=True),'ask')  # Revoke the revocation restores the hard rule.
  events.append({'day':19,'id':'r19','op':'except','key':'auto','value':'auto','when':'irreversible'})
  self.assertEqual(value('auto',20,irreversible=True),'ask')  # Matching exception cannot override active hard constraint.
 def test_history_parsing_and_split_separation(self):
  world=build_world();self.assertEqual(world,build_world());self.assertNotEqual(world['id'],build_world(71318)['id'])
  dev={tuple(p['parameters']) for p in world['people'] if p['split']=='dev'};test={tuple(p['parameters']) for p in world['people'] if p['split']=='eval'};self.assertFalse(dev&test)
  self.assertEqual(len(world['people']),16)
  for p in world['people']:
   self.assertEqual(parse_history(p['history']),p['events']);self.assertEqual(len(p['queries']),24)
   for q in p['queries']:self.assertIn(q['allowed_answers'][0],q['public']['answer_options'])
 def test_compressor_and_decoder_jobs_exclude_hidden_state_and_answers(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'run';freeze(root,pairs=1,budgets=(0,4096));evaluate(root)
   for line in (root/'compressor-jobs.jsonl').read_text().splitlines():
    row=json.loads(line);self.assertEqual(set(row),{'persona_id','history','budget_tokens','instruction'})
    self.assertFalse(any(k in row for k in ['queries','seed','events','parameters','allowed_answers']))
   for line in (root/'decoder-jobs.jsonl').read_text().splitlines():
    row=json.loads(line);self.assertFalse(any(k in row for k in ['events','parameters','seed','history']))
    for q in row['queries']:self.assertNotIn('allowed_answers',q);self.assertNotIn('stratum',q)
 def test_metric_identifies_targeted_damage_and_missing_outputs(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'run';freeze(root,pairs=2,budgets=(0,256,4096));result=evaluate(root)
   self.assertTrue(result['passed'],result['discrimination_checks']);self.assertEqual(result['external_model_calls'],0)
   full=next(r for r in result['rows'] if r['split']=='eval' and r['condition']=='full_history')
   self.assertEqual(full['quality']['accuracy'],1)
   empty=score_external(root,{});self.assertEqual(empty['planned'],96);self.assertEqual(empty['correct'],0);self.assertEqual(empty['missing'],96)
   invalid=score_external(root,{'not-a-person':{}});self.assertEqual(invalid['correct'],0);self.assertEqual(invalid['planned'],96);self.assertTrue(invalid['validation_failures'])
 def test_missing_is_not_unknown_and_allowed_sets_are_supported(self):
  person=build_world(pairs_per_split=1)['people'][0];unknown=next(q for q in person['queries'] if q['stratum']=='unknowns')
  missing=score([person],{});pred={person['id']:{unknown['public']['id']:'U'}};answered=score([person],pred)
  self.assertEqual(missing['correct'],0);self.assertEqual(answered['correct'],1)
  p=copy.deepcopy(person);p['queries']=[p['queries'][0]];p['queries'][0]['allowed_answers']=['dot','line'];qid=p['queries'][0]['public']['id']
  self.assertEqual(score([p],{p['id']:{qid:'line'}})['correct'],1)
 def test_normalized_retention_is_unclipped_and_undefined_without_useful_baseline(self):
  self.assertLess(normalized_retention(0,.2,.8),0);self.assertGreater(normalized_retention(1,.1,.8),1)
  self.assertIsNone(normalized_retention(.8,.5,.5));self.assertIsNone(normalized_retention(.8,.5,.50000000001))
 def test_repeated_runs_and_reconstructed_runs_match_and_tampering_fails(self):
  with tempfile.TemporaryDirectory() as d:
   first=Path(d)/'a';second=Path(d)/'b'
   freeze(first,pairs=1,budgets=(0,4096));freeze(second,pairs=1,budgets=(0,4096))
   a=evaluate(first);self.assertEqual(a,evaluate(first));self.assertEqual(a,evaluate(second))
   world=json.loads((first/'world.private.json').read_text());world['people'][0]['queries'][0]['allowed_answers']=['U'];(first/'world.private.json').write_text(json.dumps(world))
   with self.assertRaisesRegex(ValueError,'World changed'):score_external(first,{})
   plan=json.loads((second/'snapshot.json').read_text());plan['budgets']=[999];(second/'snapshot.json').write_text(json.dumps(plan))
   with self.assertRaisesRegex(ValueError,'Frozen plan changed'):evaluate(second)


if __name__=='__main__':unittest.main()
