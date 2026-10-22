"""Corruption controls are invented fixtures, not evidence of model quality."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_latent_transfer import perfect,mock_extraction
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('latent_observed_checker',ROOT/'benchmarks/latent-transfer-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check);s=check.s


def mock_fixture():
 f=s.w.fixtures();products={p:s.h.extractor.bind(mock_extraction(f,p),f['histories'][p],512) for p in s.w.PEOPLE};raw={};records=[]
 for index,(group,pid) in enumerate(s.plan()):
  request=s.request_for(f,group,pid,products)
  if group=='extraction':answer=mock_extraction(f,pid)
  else:
   labels=perfect(f,pid,True) if group=='none' else perfect(f,f['donors'][pid] if group=='wrong' else pid);answer={q['id']:('U' if labels[q['id']]=='U' else q['options'][labels[q['id']]]) for q in f['queries']}
  raw.setdefault(group,{})[pid]=answer;record={'execution_id':'mock-only-'+str(index),'identity_basis':'mock_not_service','request_id':s.digest(s.canonical(request)),'outcome':'completed','provenance':{'backend':'mock_not_model_evidence','model_requested':s.MODEL,'usage':[{'input_tokens':1,'output_tokens':1}]},'usage':{'input_tokens':1,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':1,'reasoning_output_tokens':0,'total_tokens':2},'artifacts':[{'path':'mock-only/'+str(index)}],'group':group,'person':pid,'answer_sha256':s.digest(s.canonical(answer))};record['result_checkpoint_sha256']=s.digest(s.canonical({'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']}));records.append(record)
 return {'synthetic':True,'backend_kind':'injected_fake_not_model_evidence','world':f,'products':products,'calls_max':31,'planned_slots':s.plan(),'completed_plan':s.plan(),'skipped':[],'invalid_products':{},'status':'complete','stop_reason':None,'raw_answers':raw,'executions':records,'failure_checkpoints':{},'ledger':check.summarize(records),'analysis':s.analyze(f,raw)}

class LatentObservedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=mock_fixture()
 def test_full_mock_matrix_reproduces_without_actual_model_claim(self):
  r=check.validate(self.fixture);self.assertEqual(r['actual_calls'],0);self.assertEqual(r['recorded_executions'],31);self.assertEqual(r['unique_request_fingerprints'],25);self.assertTrue(r['quality']['strict_transport_pass']);bad=copy.deepcopy(self.fixture);bad['backend_kind']='actual_codex_service'
  with self.assertRaisesRegex(ValueError,'provenance'):check.validate(bad)
 def test_card_edit_hidden_rule_gold_and_gate_edit_are_rejected(self):
  bad=copy.deepcopy(self.fixture);bad['products']['u06k']['prompt.md']+='manual repair'
  with self.assertRaisesRegex(ValueError,'Production'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['world']['cases'][3]['gold']['u06k']=1
  with self.assertRaisesRegex(ValueError,'fixture'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['analysis']['quality']['strict_transport_pass']=False
  with self.assertRaisesRegex(ValueError,'Scores'):check.validate(bad)
 def test_rebinding_answer_digest_cannot_hide_original_checkpoint_edit(self):
  bad=copy.deepcopy(self.fixture);group='own';pid='u06k';qid=next(q for q,value in bad['raw_answers'][group][pid].items() if value=='U');bad['raw_answers'][group][pid][qid]='启用自动处理';record=next(r for r in bad['executions'] if (r['group'],r['person'])==(group,pid));record['answer_sha256']=s.digest(s.canonical(bad['raw_answers'][group][pid]))
  with self.assertRaisesRegex(ValueError,'checkpoint'):check.validate(bad)
 def test_duplicate_execution_and_changed_usage_are_rejected(self):
  bad=copy.deepcopy(self.fixture);bad['executions'][-1]['execution_id']=bad['executions'][0]['execution_id']
  with self.assertRaisesRegex(ValueError,'identities'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['executions'][0]['usage']['input_tokens']+=5;bad['ledger']=check.summarize(bad['executions'])
  with self.assertRaisesRegex(ValueError,'usage'):check.validate(bad)
 def test_real_recorded_result_and_exports_reproduce(self):
  data=s.read(ROOT/'benchmarks/latent-transfer-v1/observed.synthetic.json');r=check.validate(data);self.assertGreater(r['actual_calls'],0);self.assertLessEqual(r['actual_calls'],31);self.assertEqual(check.verify_exports(data)['portable_cards_verified'],len(data['products']))

if __name__=='__main__':unittest.main()
