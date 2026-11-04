"""Damage controls for an archived matched source-ID request comparison."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('enum59_evidence',ROOT/'scripts/replay_source_id_enum_comparison.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class SourceIdEnumEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=r.p.read(r.DEFAULT)
 def reject(self,data):
  with self.assertRaises((ValueError,KeyError)):r.replay(data)
 def test_actual51_attempts_replay_availability_and_strict_joint_fidelity(self):
  with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:out=r.check()
  backend.assert_not_called();self.assertEqual(out['actual_original_attempts'],51)
  self.assertEqual(out['actual_original_children'],51);self.assertEqual(out['known_original_usage']['total_tokens'],630372)
  self.assertEqual(out['missing_original_usage'],0);self.assertEqual(len(out['reviewed_cards']),12)
  self.assertEqual(len(out['invalid_products']),4);self.assertEqual(len(out['skipped']),8)
  all_=out['summary']['all'];self.assertEqual(all_['original'],{'planned':60,'correct':53,'missing':0})
  self.assertEqual(all_['methods']['existing']['endpoints']['both_reviews'],{'planned':60,'correct':15,'missing':45})
  self.assertEqual(all_['methods']['enumerated']['endpoints']['both_reviews'],{'planned':60,'correct':60,'missing':0})
  self.assertEqual(all_['methods']['enumerated']['recovered_from_observed_error'],7)
  self.assertEqual(all_['methods']['enumerated']['observed_regressions'],0)
  self.assertEqual(all_['paired_joint_cells_existing_to_enumerated'],{'missing__to__correct':45,'correct__to__correct':15})
  self.assertEqual(out['summary']['known']['methods']['enumerated']['endpoints']['both_reviews']['correct'],26)
  self.assertEqual(out['summary']['unknown']['methods']['enumerated']['endpoints']['both_reviews']['correct'],34)
  self.assertEqual(out['review_product_availability']['existing']['valid_bound_cards'],4)
  self.assertEqual(out['review_product_availability']['enumerated']['valid_bound_cards'],8)
  self.assertEqual(out['review_product_availability']['enumerated']['public_characters'],[549,395,434,491,486,434,381,573])
  self.assertEqual(len(out['undefined_reference_occurrences']),5);self.assertEqual(out['request_schema_violations'],[])
  self.assertEqual(sum(s['total_tokens']for s in out['reported_usage_by_stage'].values()),630372)
 def test_sources_questions_original_parents_and_reference_are_fixed(self):
  for fault in('source','question','parent','reference','implementation','manifest'):
   data=copy.deepcopy(self.data)
   if fault=='source':data['sources']['c2v']['sources'][0]['text']+='changed'
   elif fault=='question':data['queries']['all'][0]['scenario']+='changed'
   elif fault=='parent':data['parents']['p0']['draft']['name']+='changed'
   elif fault=='reference':next(x for x in data['reference_rows']if x['gold']!='U')['gold']='U'
   elif fault=='implementation':data['implementation_sha256']={}
   else:data['source_input_manifest_sha256']='foreign'
   self.reject(data)
 def test_parent_method_repeat_and_prompt_cannot_be_substituted(self):
  for fault in('parent','method','repeat','prompt'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x['kind']=='review')
   if fault=='parent':rec['parent']='p2'
   elif fault=='method':rec['method']='enumerated'if rec['method']=='existing'else'existing'
   elif fault=='repeat':rec['review_repeat']=1-rec['review_repeat']
   else:rec['request']['prompt']+='changed';rec['request_sha256']=r.p.digest(rec['request'])
   self.reject(data)
 def test_request_schema_and_its_observed_conformance_are_bound(self):
  for fault in('schema','conformance'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x['kind']=='review')
   if fault=='schema':rec['request']['schema']={};rec['request_sha256']=r.p.digest(rec['request'])
   else:rec['request_schema_conformant']=not rec['request_schema_conformant']
   self.reject(data)
 def test_joint_denominators_and_missing_cells_cannot_be_removed(self):
  for fault in('planned','missing','correct'):
   data=copy.deepcopy(self.data)
   joint=data['status']['scores']['by_parent']['p0']['methods']['existing']['both_reviews']['joint']
   joint[fault]+=1;self.reject(data)
  data=copy.deepcopy(self.data);data['status']['skipped']=[];self.reject(data)
 def test_invalid_source_id_cannot_be_silently_repaired_or_read(self):
  for fault in('repair','flag','artifact'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if x.get('product_invalid'))
   if fault=='repair':
    answer=json.loads(rec['raw']);ids={x['id']for x in data['sources'][rec['profile']]['sources']}
    def walk(v):
     if isinstance(v,list):
      for x in v:walk(x)
     elif isinstance(v,dict):
      if set(v)=={'source_id'}and v['source_id']not in ids:v['source_id']=next(iter(sorted(ids)))
      for x in v.values():walk(x)
    walk(answer);rec['raw']=json.dumps(answer,ensure_ascii=False);rec['raw_value_sha256']=r.p.digest(rec['raw'])
   elif fault=='flag':rec.pop('product_invalid')
   else:rec['card']={'prompt':'invented repaired card'};rec['artifact_sha256']=r.p.digest(rec['card'])
   self.reject(data)
 def test_raw_answers_and_bound_artifact_bytes_are_preserved(self):
  for fault in('raw','artifact'):
   data=copy.deepcopy(self.data);rec=next(x for x in data['records']if'card'in x)
   if fault=='raw':rec['raw']+='changed'
   else:rec['card']['prompt']+='changed'
   self.reject(data)
 def test_attempt_child_expired_and_cost_ledgers_are_fixed(self):
  for field in('local_cli_child_intents','unused_slots_expire','attempt_reservations'):
   data=copy.deepcopy(self.data);data['status'][field]+=1;self.reject(data)
  data=copy.deepcopy(self.data);data['status']['known_usage']['total_tokens']+=1;self.reject(data)
 def test_development_comparison_cannot_be_promoted_to_general_fidelity(self):
  for field in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
   'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old_scores_replaced','external_reader_decoder','token_matched_tail','optimal_tail_selection'):
   data=copy.deepcopy(self.data);data[field]=True;self.reject(data)
if __name__=='__main__':unittest.main()
