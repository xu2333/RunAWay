"""Corruption controls use invented checkpoints; never model-quality evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_fresh_boundary import mock_extraction,perfect
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fresh_record_checker',ROOT/'benchmarks/fresh-boundary-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check);s=check.s


def mock_recorded_fixture():
 f=s.w.fixtures();products={p:s.extractor.bind(mock_extraction(f,p),f['histories'][p],768) for p in s.w.PEOPLE};labels,scopes=perfect(f);raw={};records=[]
 for index,(group,pid) in enumerate(s.plan()):
  req=s.request_for(f,group,pid,products);arm=s.descriptor(group)[2];mode=s.descriptor(group)[1]
  if arm=='extraction':answer=mock_extraction(f,pid)
  else:
   target=f['donors'][pid] if arm=='wrong' else pid;answer={}
   for q in f['queries']:
    label='U' if arm=='none' else labels[target][q['id']];choice='U' if label=='U' else q['options'][label];scope='uncovered' if arm=='none' else scopes[target][q['id']];answer[q['id']]={'scope':scope,'choice':choice} if mode=='scoped' else choice
  raw.setdefault(group,{})[pid]=answer;record={'execution_id':'mock-only-slot-'+str(index),'identity_basis':'mock_not_service','request_id':s.digest(s.canonical(req)),'outcome':'completed','provenance':{'backend':'mock_not_model_evidence','model_requested':req['model'],'usage':[{'input_tokens':1,'output_tokens':1}]},'usage':{'input_tokens':1,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':1,'reasoning_output_tokens':0,'total_tokens':2},'artifacts':[{'path':'mock-only/'+str(index)}],'group':group,'person':pid,'answer_sha256':s.digest(s.canonical(answer))}
  record['result_checkpoint_sha256']=s.digest(s.canonical({'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']}));records.append(record)
 return {'synthetic':True,'backend_kind':'injected_fake_not_model_evidence','world':f,'calls_max':56,'planned_slots':s.plan(),'completed_plan':s.plan(),'skipped':[],'status':'complete','stop_reason':None,'invalid_products':{},'products':products,'raw_answers':raw,'executions':records,'ledger':check.summarize(records),'analysis':s.analyze(f,raw)}

class FreshObservedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=mock_recorded_fixture()
 def test_offline_reproduction_never_labels_fake_calls_as_models(self):
  result=check.validate(self.fixture);self.assertTrue(result['passed']);self.assertEqual(result['recorded_executions'],56);self.assertEqual(result['unique_request_fingerprints'],40);self.assertEqual(result['actual_calls'],0)
  bad=copy.deepcopy(self.fixture);bad['backend_kind']='actual_codex_service'
  with self.assertRaisesRegex(ValueError,'provenance'):check.validate(bad)
 def test_card_edit_and_score_edit_are_rejected(self):
  bad=copy.deepcopy(self.fixture);bad['products']['t04a']['prompt.md']+='猜出来的偏好'
  with self.assertRaisesRegex(ValueError,'Production'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['analysis']['quality']['luna_standard']['stable_transfer_pass']=False
  with self.assertRaisesRegex(ValueError,'Scores'):check.validate(bad)
 def test_answer_replacement_still_fails_original_checkpoint_binding(self):
  bad=copy.deepcopy(self.fixture);group='luna_standard_own';pid='t04a';qid=next(iter(bad['raw_answers'][group][pid]));bad['raw_answers'][group][pid][qid]='U' if bad['raw_answers'][group][pid][qid]!='U' else 'not_an_offered_choice'
  record=next(r for r in bad['executions'] if (r['group'],r['person'])==(group,pid));record['answer_sha256']=s.digest(s.canonical(bad['raw_answers'][group][pid]))
  with self.assertRaisesRegex(ValueError,'checkpoint'):check.validate(bad)
 def test_duplicate_execution_and_changed_usage_are_rejected(self):
  bad=copy.deepcopy(self.fixture);bad['executions'][1]['execution_id']=bad['executions'][0]['execution_id']
  with self.assertRaisesRegex(ValueError,'identities'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['executions'][0]['usage']['input_tokens']+=9;bad['ledger']=check.summarize(bad['executions'])
  with self.assertRaisesRegex(ValueError,'usage'):check.validate(bad)

 def test_actual_recorded_study_and_exports_reproduce_offline(self):
  data=s.read(ROOT/'benchmarks/fresh-boundary-v1/observed.synthetic.json');result=check.validate(data);self.assertEqual(result['actual_calls'],56);self.assertEqual(result['unique_request_fingerprints'],40);self.assertTrue(result['quality']['sol_standard']['own_strict_pass']);self.assertFalse(result['quality']['luna_scoped']['full_qualified']);self.assertEqual(check.verify_exports(data)['portable_cards_verified'],4)

if __name__=='__main__':unittest.main()
