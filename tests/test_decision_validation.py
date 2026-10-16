import copy
import json
from pathlib import Path
import tempfile
import unittest
from runaway.decision_world import build_world,gold
from runaway.selfplay_world import POLICIES
from runaway.decision_validation import score,freeze,CONDITIONS
from runaway.decision_experiment import LimitedCalls

class ValidationTests(unittest.TestCase):
 def test_new_world_is_disjoint_and_explicit_requests_are_separate(self):
  w=build_world();self.assertEqual(len(w['personas']),4);self.assertEqual(len(w['training']),16);self.assertEqual(len(w['test']),34)
  self.assertTrue(all(p['policy'] not in POLICIES for p in w['personas']))
  ids=[c['public']['id'] for c in w['training']+w['test']];self.assertEqual(len(ids),len(set(ids)))
  for p in w['personas']:
   for c in w['test']:self.assertIn(gold(p['policy'],c),('A','B','U'))
  self.assertEqual(sum(c['kind']=='heldout' for c in w['test']),24)
  self.assertEqual(sum(c['kind']=='explicit_request' for c in w['test']),4)
 def test_metrics_keep_failures_and_constraint_violations(self):
  w=build_world();pred={p['id']:{'compact':{c['public']['id']:('unknown' if gold(p['policy'],c)=='U' else gold(p['policy'],c)) for c in w['test']}} for p in w['personas']}
  r=score(w,pred,'compact');self.assertEqual(r['correct'],96);self.assertEqual(r['planned'],96);self.assertEqual(r['constraint_violations'],0);self.assertEqual(r['order_consistency'],1);self.assertEqual(r['twins_correct'],6)
  del pred['n01']['compact'];r=score(w,pred,'compact');self.assertEqual(r['correct'],72);self.assertEqual(r['planned'],96);self.assertEqual(r['constraint_violations'],4)
 def test_frozen_limits_are_new_and_bounded_not_old_budget_reuse(self):
  with tempfile.TemporaryDirectory() as d:
   p=freeze(Path(d)/'plan');self.assertEqual(p['calls_limit'],31);self.assertEqual(p['combined_limit'],45);self.assertEqual(p['development_calls_limit'],14)
   self.assertIn('reject_constant_oracle',p['decoder_gate']);self.assertTrue((Path(d)/'plan/frozen-source/runaway/decision_memory.py').is_file())
 def test_call_bound_and_backend_failure_stop_network_attempts(self):
  with tempfile.TemporaryDirectory() as d:
   called=[]
   def fake(*a,**k):called.append(1);return '{"value":1}',{'backend':'test'}
   c=LimitedCalls(Path(d),1,fake);c.call('first',{},'test');
   with self.assertRaises(ValueError):c.call('second',{},'test')
   self.assertEqual(len(called),1)
if __name__=='__main__':unittest.main()
