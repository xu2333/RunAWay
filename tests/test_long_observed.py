"""Offline binding/corruption controls; invented answers are never model evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_long_trajectory import mock_extraction,perfect
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('long_record_checker',ROOT/'benchmarks/long-trajectory-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check);s=check.s


def mock_fixture():
 f=s.w.fixtures();raw={};products={};invalid={};completed=[];skipped=[];records=[]
 for index,(group,pid) in enumerate(s.plan()):
  prefix,arm,budget=s.descriptor(group)
  if arm=='own' and pid not in products.get(str(budget),{}):skipped.append([group,pid,'invalid_or_missing_extraction:'+str(budget)+':'+pid]);continue
  req=s.request_for(f,group,pid,products)
  if arm=='extraction':
   answer=mock_extraction(f,pid)
   try:products.setdefault(str(budget),{})[pid]=s.h.extractor.bind(answer,f['histories'][pid],budget)
   except ValueError as exc:invalid[str(budget)+':'+pid]={'error':str(exc),'no_repair':True}
  else:
   labels=perfect(f,pid) if pid!='shared' else {};answer={q['id']:('U' if labels.get(q['id'],'U')=='U' else q['options'][labels[q['id']]]) for q in f['queries']}
  raw.setdefault(group,{})[pid]=answer;completed.append([group,pid]);record={'execution_id':'mock-only-slot-'+str(index),'identity_basis':'mock_not_service','request_id':s.digest(s.canonical(req)),'outcome':'completed','provenance':{'backend':'mock_not_model_evidence','model_requested':req['model'],'usage':[{'input_tokens':1,'output_tokens':1}]},'usage':{'input_tokens':1,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':1,'reasoning_output_tokens':0,'total_tokens':2},'artifacts':[{'path':'mock-only/'+str(index)}],'group':group,'person':pid,'answer_sha256':s.digest(s.canonical(answer))}
  record['result_checkpoint_sha256']=s.digest(s.canonical({'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']}));records.append(record)
 return {'synthetic':True,'backend_kind':'injected_fake_not_model_evidence','world':f,'calls_max':46,'planned_slots':s.plan(),'completed_plan':completed,'skipped':skipped,'status':'completed_with_invalid_products' if invalid else 'complete','stop_reason':None,'invalid_products':invalid,'products':products,'raw_answers':raw,'executions':records,'failure_checkpoints':{},'ledger':check.summarize(records),'analysis':s.analyze(f,raw)}

class LongObservedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=mock_fixture()
 def test_reproduction_keeps_planned_missing_products_and_fake_status(self):
  result=check.validate(self.fixture);self.assertTrue(result['passed']);self.assertEqual(result['actual_calls'],0);self.assertEqual(len(self.fixture['completed_plan'])+len(self.fixture['skipped']),46)
  bad=copy.deepcopy(self.fixture);bad['backend_kind']='actual_codex_service'
  with self.assertRaisesRegex(ValueError,'provenance'):check.validate(bad)
 def test_changed_current_source_and_scores_are_rejected(self):
  bad=copy.deepcopy(self.fixture);bad['world']['histories']['t04a']['sources'][-1]['text']='changed'
  with self.assertRaisesRegex(ValueError,'fixture'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['analysis']['quality']['sol']['stable_384_transfer_pass']=not bad['analysis']['quality']['sol']['stable_384_transfer_pass']
  with self.assertRaisesRegex(ValueError,'Scores'):check.validate(bad)
 def test_answer_edit_cannot_be_rebound_with_only_answer_digest(self):
  bad=copy.deepcopy(self.fixture);group='sol_full';pid='t04a';qid=next(iter(bad['raw_answers'][group][pid]));bad['raw_answers'][group][pid][qid]='U' if bad['raw_answers'][group][pid][qid]!='U' else 'invented'
  record=next(r for r in bad['executions'] if (r['group'],r['person'])==(group,pid));record['answer_sha256']=s.digest(s.canonical(bad['raw_answers'][group][pid]))
  with self.assertRaisesRegex(ValueError,'checkpoint'):check.validate(bad)
 def test_usage_duplicate_identity_and_skipped_slot_tampering_fail(self):
  bad=copy.deepcopy(self.fixture);bad['executions'][0]['usage']['input_tokens']+=1;bad['ledger']=check.summarize(bad['executions'])
  with self.assertRaisesRegex(ValueError,'usage'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['executions'][1]['execution_id']=bad['executions'][0]['execution_id']
  with self.assertRaisesRegex(ValueError,'identities'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['skipped']=[]
  with self.assertRaisesRegex(ValueError,'skip order'):check.validate(bad)
 def test_invalid_products_cannot_be_silently_removed(self):
  self.assertTrue(self.fixture['invalid_products']);bad=copy.deepcopy(self.fixture);bad['invalid_products']={}
  with self.assertRaisesRegex(ValueError,'Invalid products'):check.validate(bad)
 def test_real_failed_call_cannot_be_relabelled_zero_usage(self):
  data=s.read(ROOT/'benchmarks/long-trajectory-v1/observed.synthetic.json');bad=copy.deepcopy(data);record=next(r for r in bad['executions'] if r['outcome']=='failed');record['provenance']['usage']=[{'input_tokens':0,'output_tokens':0}];record['usage']=check.usage(record['provenance']);bad['ledger']=check.summarize(bad['executions'])
  with self.assertRaisesRegex(ValueError,'Failed checkpoint'):check.validate(bad)
 def test_real_recorded_study_and_portable_exports_reproduce(self):
  data=s.read(ROOT/'benchmarks/long-trajectory-v1/observed.synthetic.json');result=check.validate(data);self.assertGreater(result['actual_calls'],0);self.assertLessEqual(result['actual_calls'],46);self.assertEqual(check.verify_exports(data)['portable_cards_verified'],sum(map(len,data['products'].values())))

if __name__=='__main__':unittest.main()
