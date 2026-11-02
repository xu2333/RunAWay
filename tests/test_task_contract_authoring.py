"""Instrument calibration:typed tasks and discriminating witnesses,not NLP truth."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('task_contract_authoring_tests',ROOT/'benchmarks/task-contract-v1/authoring.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)


def fixture():
 source={'schema_version':1,'sources':[{'id':'u1','role':'user','text':'获准参加时，我今后选择全名为先铺桌后读书的方案。远程安排我尚未决定。上次借书的实际记录是已归还。'},
  {'id':'a1','role':'assistant','text':'我建议你接受远程安排。'}]}
 c={'version':a.VERSION,'id':'toy','target_object':'虚构读书活动','intent':'preferred_option','temporal_role':'future_policy',
  'answer_kind':'existing_option_label','facts':'已获准参加','options':['先铺桌后读书','先读书后铺桌'],
  'reference':'先铺桌后读书','unknown_reason':None,'support':[{'source_id':'u1','quote':source['sources'][0]['text']}],
  'contrasts':[{'fault':'erase_choice','predicted_answer':'U'}]}
 return c,source


class TaskContractAuthoringTests(unittest.TestCase):
 def test_future_choice_renderer_keeps_named_options_and_separates_private_reference(self):
  c,s=fixture();out=a.prepare(c,s);q1,q2=out['questions.public']
  self.assertIn('会选择哪个既有方案',q1['scenario']);self.assertNotIn('命名方式',q1['scenario'])
  self.assertEqual(q1['scenario'],q2['scenario']);self.assertEqual(q1['options']['A'],q2['options']['B'])
  self.assertEqual(set(q1),{'id','scenario','options'});self.assertNotIn('reference',q1)
  self.assertEqual((out['new_model_calls'],out['old_benchmark_metrics_changed']),(0,False))

 def test_past_observation_cannot_be_mislabeled_as_future_preference(self):
  c,s=fixture();c['temporal_role']='recorded_past';c['answer_kind']='observed_status_label'
  with self.assertRaises(ValueError):a.prepare(c,s)
  c['intent']='past_observation';c['options']=['已归还','未归还'];c['reference']='已归还'
  out=a.prepare(c,s);self.assertIn('上一次实际状态',out['questions.public'][0]['scenario'])
  self.assertFalse(out['audit.private']['semantic_entailment_verified'])

 def test_known_undecided_status_differs_from_unknown_decision_polarity(self):
  c,s=fixture();c.update(intent='decision_polarity',temporal_role='recorded_commitment',answer_kind='decision_polarity_label',
    options=['同意新安排','反对新安排'],reference='U',unknown_reason='not_decided',contrasts=[{'fault':'invent_adoption','predicted_answer':'同意新安排'}])
  self.assertTrue(a.prepare(c,s)['audit.private']['structural_contract_valid'])
  c['unknown_reason']=None
  with self.assertRaises(ValueError):a.prepare(c,s)
  c.update(intent='past_observation',temporal_role='recorded_past',answer_kind='observed_status_label',
    options=['尚未决定','已决定'],reference='尚未决定',unknown_reason=None,contrasts=[{'fault':'invent_commitment','predicted_answer':'已决定'}])
  self.assertTrue(a.prepare(c,s)['audit.private']['structural_contract_valid'])

 def test_remote_proposal_witness_outside_answer_space_exposes_blind_spot(self):
  c,s=fixture();c.update(reference='U',unknown_reason='uncovered_policy',contrasts=[{'fault':'adopt_assistant_proposal','predicted_answer':'接受远程安排'}])
  with self.assertRaisesRegex(ValueError,'outside options'):a.prepare(c,s)
  c['options']=['接受远程安排','拒绝远程安排']
  self.assertTrue(a.prepare(c,s)['audit.private']['structural_contract_valid'])
  self.assertFalse(a.prepare(c,s)['audit.private']['contrast_behaviour_observed'])

 def test_nondiscriminating_witness_and_unaccepted_reference_cannot_pass_as_proof(self):
  c,s=fixture();c['contrasts'][0]['predicted_answer']=c['reference']
  with self.assertRaises(ValueError):a.prepare(c,s)
  c['contrasts'][0]['predicted_answer']='U';audit=a.prepare(c,s)['audit.private']
  self.assertFalse(audit['reference_independently_accepted']);self.assertFalse(audit['question_source_equivalence_independently_accepted'])

 def test_assistant_forged_and_duplicate_source_support_rejected(self):
  for fault in ('assistant','quote','duplicate','known_label'):
   with self.subTest(fault=fault):
    c,s=fixture()
    if fault=='assistant':c['support']=[{'source_id':'a1','quote':s['sources'][1]['text']}]
    elif fault=='quote':c['support'][0]['quote']='不存在的说法'
    elif fault=='duplicate':s['sources'].append(copy.deepcopy(s['sources'][0]))
    else:c['options'][0]='无出处的名字';c['reference']='无出处的名字'
    with self.assertRaises(ValueError):a.prepare(c,s)

 def test_authoring_never_mutates_old_inputs_and_new_name_creation_is_different_task(self):
  c,s=fixture();before=copy.deepcopy((c,s));out=a.prepare(c,s);self.assertEqual((c,s),before)
  out['contract.private']['reference']='changed';self.assertEqual((c,s),before)
  c['intent']='create_new_name'
  with self.assertRaisesRegex(ValueError,'creating a new name'):a.prepare(c,s)


if __name__=='__main__':unittest.main()
