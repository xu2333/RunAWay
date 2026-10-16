from pathlib import Path
import tempfile
import unittest
import json
from runaway.bound_experiment import freeze,run,controls
from runaway.bound_world import build_world
from runaway.decision_world import gold,NEW_POLICIES
from runaway.selfplay_world import POLICIES
from runaway.decision_transfer_world import POLICIES as TRANSFER_POLICIES


class BoundExperimentTests(unittest.TestCase):
 def test_new_cohort_is_not_any_consumed_policy_and_key_difference_is_automation(self):
  world=build_world();self.assertTrue(all(p['policy'] not in POLICIES+NEW_POLICIES+TRANSFER_POLICIES for p in world['personas']))
  a,b=world['personas'];self.assertEqual([k for k in a['policy'] if a['policy'][k]!=b['policy'][k]],['automate'])
  self.assertEqual(len({c['public']['id'] for c in world['training']+world['test']}),50)
 def test_control_gate_requires_actions_and_current_instruction_and_twin_coverage(self):
  world=build_world();pred={p['id']:{'oracle':{c['public']['id']:gold(p['policy'],c) for c in world['test']}} for p in world['personas']}
  self.assertTrue(controls(world,pred)['passed'])
  c=next(c for c in world['test'] if c['kind']=='explicit_request');del pred['b01']['oracle'][c['public']['id']]
  self.assertFalse(controls(world,pred)['passed'])
 def test_invalid_decoder_stops_before_extraction_and_unrun_is_not_zero(self):
  called=[]
  def fake(prompt,model,**kwargs):
   called.append(model);data=json.loads(prompt.split('\nINPUT_JSON:\n')[1])
   return json.dumps({'predictions':[{'id':c['id'],'selection':'unknown','evidence':''} for c in data['cases']]}),{'backend':'offline_fake','usage':[]}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'run';plan=freeze(root);self.assertEqual(plan['calls_limit'],24)
   self.assertIn('runaway/text_integrity.py',plan['code_hashes']);self.assertIn('web/dist/text-integrity.mjs',plan['code_hashes'])
   report=run(root,generate=fake);self.assertEqual(len(called),2);self.assertFalse(report['decoder_gate']['passed'])
   self.assertEqual(report['final_profiles'],0);self.assertIsNone(report['conditions']['compact']['primary']['end_to_end_rate'])
   with self.assertRaisesRegex(ValueError,'Completed output'):run(root,generate=fake)
 def test_backend_failure_stops_without_more_invocation_intents(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'run';freeze(root);calls=[]
   def broken(*a,**k):calls.append(1);raise ValueError('simulated timeout, offline fixture')
   result=run(root,generate=broken)
   self.assertEqual(len(calls),1);self.assertEqual(len(list((root/'calls').glob('*.attempt.json'))),1)
   self.assertIn('stopped',result['failures'])


if __name__=='__main__':unittest.main()
