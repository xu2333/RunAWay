"""Damage controls for measured fresh45responses;no inference or new reference."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fresh45_evidence',ROOT/'scripts/replay_fresh_enum_pipeline.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class FreshPipelineEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=r.p.read(r.DEFAULT)
 def reject(self,data):
  with self.assertRaises((ValueError,KeyError)):r.replay(data)
 def test_actual45_attempts_preserve64_cases_and_all_usage_without_extra_service(self):
  with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:out=r.check()
  backend.assert_not_called();self.assertEqual(out['actual_original_attempts'],45);self.assertEqual(out['actual_original_children'],45)
  self.assertEqual(out['known_original_usage']['total_tokens'],543815);self.assertEqual(out['missing_original_usage'],0)
  self.assertTrue(out['controls_qualified']);self.assertTrue(out['compression_evidence_available']);self.assertEqual(out['invalid_products'],[]);self.assertEqual(out['skipped'],[])
  self.assertEqual(len(out['cards']),8)
  self.assertEqual(out['product_availability']['draft']['public_characters'],[440,460,454,434])
  self.assertEqual(out['product_availability']['reviewed']['public_characters'],[490,487,474,496])
  for view in r.p.VIEWS:
   self.assertEqual(out['summary']['all']['endpoints'][view],{'planned':64,'correct':48 if view.endswith('_tail')else 64,'missing':0})
   self.assertEqual(out['summary']['known']['endpoints'][view]['correct'],8 if view.endswith('_tail')else 24)
   self.assertEqual(out['summary']['unknown']['endpoints'][view]['correct'],40)
  self.assertEqual(out['summary']['all']['recovered_from_observed_draft_error'],0);self.assertEqual(out['summary']['all']['observed_review_regressions'],0)
  self.assertEqual(out['summary']['all']['paired_card_tail_cells']['draft'],{'card_only_correct':16,'both_correct':48})
  self.assertEqual(sum(s['total_tokens']for s in out['reported_usage_by_stage'].values()),543815)
  self.assertEqual(len(out['failed_or_missing_cases']),32)
 def test_inputs_source_version_reference_and_author_evidence_are_fixed(self):
  for fault in('source','question','reference','author','implementation','manifest','source_ref'):
   d=copy.deepcopy(self.data)
   if fault=='source':d['sources']['pavo']['sources'][0]['text']+='changed'
   elif fault=='question':d['queries']['all'][0]['scenario']+='changed'
   elif fault=='reference':next(x for x in d['reference_rows']if x['gold']!='U')['gold']='U'
   elif fault=='author':d['author_evidence']={}
   elif fault=='implementation':d['implementation_sha256']={}
   elif fault=='manifest':d['source_input_manifest_sha256']='foreign'
   else:d['scientific_source_ref']='current-unverified-tree'
   self.reject(d)
 def test_person_view_repeat_and_exact_request_cannot_be_substituted(self):
  for fault in('person','view','repeat','request'):
   d=copy.deepcopy(self.data);rec=next(x for x in d['records']if x['kind']=='read')
   if fault=='person':rec['profile']='rill'
   elif fault=='view':rec['view']='reviewed_tail'if rec['view']!='reviewed_tail'else'draft'
   elif fault=='repeat':rec['read_repeat']=1-rec['read_repeat']
   else:rec['request']['prompt']+='changed';rec['request_sha256']=r.p.digest(rec['request'])
   self.reject(d)
 def test_raw_answers_cards_and_model_graphs_cannot_be_repaired_after_observation(self):
  for fault in('raw','card','graph'):
   d=copy.deepcopy(self.data);rec=next(x for x in d['records']if'card'in x)
   if fault=='raw':rec['raw']+='changed'
   elif fault=='card':rec['card']['prompt']+='changed'
   else:
    answer=json.loads(rec['raw']);answer['name']+='人工修改'
    rec['raw']=json.dumps(answer,ensure_ascii=False);rec['raw_value_sha256']=r.p.digest(rec['raw'])
   self.reject(d)
 def test_fixed64_denominators_and_missing_counts_cannot_be_shrunk(self):
  for view in r.p.VIEWS:
   for field in('planned','correct','missing'):
    d=copy.deepcopy(self.data);d['status']['scores']['views'][view]['joint'][field]+=1;self.reject(d)
 def test_fresh_review_request_must_keep_own_original_model_draft(self):
  d=copy.deepcopy(self.data);rec=next(x for x in d['records']if x['kind']=='review')
  prefix,body=rec['request']['prompt'].split('\nREVIEW_DRAFT_JSON:\n');draft=json.loads(body);draft['name']+='changed'
  rec['request']['prompt']=prefix+'\nREVIEW_DRAFT_JSON:\n'+json.dumps(draft,ensure_ascii=False);rec['request_sha256']=r.p.digest(rec['request'])
  self.reject(d)
 def test_equal_character_tail_is_not_replaced_by_selected_source(self):
  d=copy.deepcopy(self.data);rec=next(x for x in d['records']if x['kind']=='read'and x['view'].endswith('_tail'))
  rec['request']['prompt']='oracle selected source\n'+rec['request']['prompt'];rec['request_sha256']=r.p.digest(rec['request']);self.reject(d)
 def test_attempt_child_expired_usage_and_request_conformance_ledgers_are_fixed(self):
  for field in('local_cli_child_intents','unused_slots_expire','attempt_reservations'):
   d=copy.deepcopy(self.data);d['status'][field]+=1;self.reject(d)
  d=copy.deepcopy(self.data);d['status']['known_usage']['total_tokens']+=1;self.reject(d)
  d=copy.deepcopy(self.data);rec=next(x for x in d['records']if x['kind']=='review');rec['request_schema_conformant']=not rec['request_schema_conformant'];self.reject(d)
 def test_synthetic_single_draw_cannot_claim_stability_holdout_or_real_person_fidelity(self):
  for field in r.FALSE_CLAIMS:
   d=copy.deepcopy(self.data);d[field]=True;self.reject(d)
if __name__=='__main__':unittest.main()
