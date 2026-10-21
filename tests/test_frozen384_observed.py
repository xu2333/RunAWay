"""Evidence corruption checks use explicitly invented model answers."""
import copy
import importlib.util
from pathlib import Path
import unittest
from test_long_trajectory import perfect
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('frozen384_checker_tests',ROOT/'benchmarks/frozen384-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check);s=check.s

def mock_fixture():
 f=s.w.fixtures();products=s.cards();raw={};records=[]
 for i,(group,pid) in enumerate(s.plan()):
  request=s.request_for(f,group,pid,products);labels=perfect(f,pid) if pid!='shared' else {};answer={q['id']:('U' if labels.get(q['id'],'U')=='U' else q['options'][labels[q['id']]]) for q in f['queries']};raw.setdefault(group,{})[pid]=answer;record={'execution_id':'mock-only-'+str(i),'identity_basis':'mock_not_service','request_id':s.digest(s.canonical(request)),'outcome':'completed','provenance':{'backend':'mock_not_model_evidence','model_requested':s.MODEL,'usage':[{'input_tokens':1,'output_tokens':1}]},'usage':{'input_tokens':1,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':1,'reasoning_output_tokens':0,'total_tokens':2},'artifacts':[{'path':'mock-only/'+str(i)}],'group':group,'person':pid,'answer_sha256':s.digest(s.canonical(answer))};record['result_checkpoint_sha256']=s.digest(s.canonical({'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']}));records.append(record)
 return {'synthetic':True,'backend_kind':'injected_fake_not_model_evidence','world':f,'products':products,'calls_max':13,'planned_slots':s.plan(),'completed_plan':s.plan(),'status':'complete','stop_reason':None,'raw_answers':raw,'executions':records,'failure_checkpoints':{},'ledger':check.summarize(records),'analysis':s.analyze(f,raw)}

class Frozen384ObservedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=mock_fixture()
 def test_mock_reproduction_does_not_claim_actual_calls(self):
  result=check.validate(self.fixture);self.assertEqual(result['actual_calls'],0);self.assertEqual(result['recorded_executions'],13);self.assertEqual(result['unique_request_fingerprints'],9)
  bad=copy.deepcopy(self.fixture);bad['backend_kind']='actual_codex_service'
  with self.assertRaisesRegex(ValueError,'provenance'):check.validate(bad)
 def test_frozen_cards_and_quality_flags_cannot_change(self):
  bad=copy.deepcopy(self.fixture);bad['products']['t04a']['prompt.md']+='manual repair'
  with self.assertRaisesRegex(ValueError,'products'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['analysis']['quality']['stable384_pass']=False
  with self.assertRaisesRegex(ValueError,'Scores'):check.validate(bad)
 def test_answer_digest_replacement_does_not_rebind_original_checkpoint(self):
  bad=copy.deepcopy(self.fixture);pid='t11b';qid=next(iter(bad['raw_answers']['repeat'][pid]));bad['raw_answers']['repeat'][pid][qid]='U' if bad['raw_answers']['repeat'][pid][qid]!='U' else 'invented';record=next(r for r in bad['executions'] if (r['group'],r['person'])==('repeat',pid));record['answer_sha256']=s.digest(s.canonical(bad['raw_answers']['repeat'][pid]))
  with self.assertRaisesRegex(ValueError,'checkpoint'):check.validate(bad)
 def test_reused_execution_identity_and_reordered_plan_fail(self):
  bad=copy.deepcopy(self.fixture);bad['executions'][-1]['execution_id']=bad['executions'][1]['execution_id']
  with self.assertRaisesRegex(ValueError,'identities'):check.validate(bad)
  bad=copy.deepcopy(self.fixture);bad['planned_slots'][1:3]=reversed(bad['planned_slots'][1:3])
  with self.assertRaisesRegex(ValueError,'plan'):check.validate(bad)
 def test_actual_recorded_result_and_unchanged_cards_reproduce(self):
  data=s.read(ROOT/'benchmarks/frozen384-v1/observed.synthetic.json');result=check.validate(data);self.assertGreater(result['actual_calls'],0);self.assertLessEqual(result['actual_calls'],13);self.assertEqual(check.verify_exports(data)['unchanged_portable_cards_verified'],4)

if __name__=='__main__':unittest.main()
