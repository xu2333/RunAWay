"""Measured repeated-review damage controls; no inference or new gold."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('repeat35_evidence',ROOT/'scripts/replay_source_id_review_repeat.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class ReviewRepeatEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=r.p.read(r.DEFAULT)
 def reject(self,data):
  with self.assertRaises((ValueError,KeyError)):r.replay(data)
 def test_actual_archive_replays31attempts_with_missing_cases_and_no_new_service(self):
  with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:out=r.check()
  backend.assert_not_called();self.assertEqual(out['actual_original_attempts'],31)
  self.assertEqual(out['actual_original_children'],31);self.assertEqual(out['known_original_usage']['total_tokens'],379663)
  self.assertEqual(out['missing_original_usage'],0);self.assertEqual(len(out['reviewed_cards']),6)
  self.assertEqual(len(out['invalid_products']),2);self.assertEqual(len(out['skipped']),4)
  self.assertEqual(out['summary']['all']['endpoints']['original'],{'planned':60,'correct':53,'missing':0})
  self.assertEqual(out['summary']['all']['endpoints']['both_reviews'],{'planned':60,'correct':45,'missing':15})
  self.assertEqual(out['summary']['all']['recovered_from_observed_error'],3)
  self.assertEqual(out['summary']['all']['observed_regressions'],0)
  self.assertEqual(out['summary']['previously_complete']['endpoints']['both_reviews']['correct'],30)
  self.assertEqual(len(out['undefined_reference_occurrences']),3)
  self.assertEqual(sum(s['total_tokens']for s in out['reported_usage_by_stage'].values()),379663)
 def test_source_questions_parent_reference_and_implementation_cannot_change(self):
  for fault in('source','question','parent','reference','implementation','manifest'):
   data=copy.deepcopy(self.data)
   if fault=='source':data['sources']['c2v']['sources'][0]['text']+='changed'
   elif fault=='question':data['queries']['all'][0]['scenario']+='changed'
   elif fault=='parent':data['parents']['p0']['draft']['name']+='changed'
   elif fault=='reference':next(x for x in data['reference_rows']if x['gold']!='U')['gold']='U'
   elif fault=='implementation':data['implementation_sha256']={}
   else:data['source_input_manifest_sha256']='foreign'
   self.reject(data)
 def test_parent_repeat_and_exact_request_routing_cannot_be_substituted(self):
  for fault in('parent','repeat','prompt'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x['view']=='reviewed')
   if fault=='parent':rec['parent']='p2'
   elif fault=='repeat':rec['review_repeat']=1-rec['review_repeat']
   else:rec['request']['prompt']+='changed';rec['request_sha256']=r.p.digest(rec['request'])
   self.reject(data)
 def test_missing_cells_skips_or_strict_joint_denominators_cannot_be_removed(self):
  for fault in('skip','planned','missing','correct'):
   data=copy.deepcopy(self.data)
   if fault=='skip':data['status']['skipped'].pop()
   else:
    joint=data['status']['scores']['by_parent']['p3']['both_reviews']['joint']
    joint[fault]=0 if fault in('planned','missing')else 15
   self.reject(data)
 def test_manual_id_correction_is_not_an_observed_candidate(self):
  data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x['slot']==9)
  answer=json.loads(rec['raw']);answer['nodes'][0]['decisions'][1]['source_id']='m05'
  rec['raw']=json.dumps(answer,ensure_ascii=False);rec['raw_value_sha256']=r.p.digest(rec['raw'])
  self.reject(data)
 def test_invalid_flag_and_fabricated_review_artifact_are_rejected(self):
  for fault in('flag','artifact'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x['slot']==9)
   if fault=='flag':rec.pop('product_invalid')
   else:rec['card']={'prompt':'manually repaired'};rec['artifact_sha256']=r.p.digest(rec['card'])
   self.reject(data)
 def test_actual_card_and_raw_reply_bytes_are_preserved(self):
  for fault in('card','raw'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if'card'in x)
   if fault=='card':rec['card']['prompt']+='changed'
   else:rec['raw']+='changed'
   self.reject(data)
 def test_cost_child_and_expired_slot_ledgers_cannot_be_changed(self):
  for field in('local_cli_child_intents','unused_slots_expire','attempt_reservations'):
   data=copy.deepcopy(self.data);data['status'][field]+=1;self.reject(data)
  data=copy.deepcopy(self.data);data['status']['known_usage']['total_tokens']+=1;self.reject(data)
 def test_selected_development_evidence_cannot_be_promoted_to_general_fidelity(self):
  for field in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
   'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old_scores_replaced','external_reader_decoder','token_matched_tail','optimal_tail_selection'):
   data=copy.deepcopy(self.data);data[field]=True;self.reject(data)
if __name__=='__main__':unittest.main()
