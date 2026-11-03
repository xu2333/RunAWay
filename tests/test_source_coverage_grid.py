"""Grid accounting and actual-archive checks; oracle fixtures are not model evidence."""
import copy,json,tempfile,importlib.util
from pathlib import Path
import unittest
from collections import Counter
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_grid_tests',ROOT/'scripts/replay_source_coverage_grid.py')
grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)

def oracle_arithmetic_fixture():
 rows=grid.canonical.inputs()['rows'];count=grid.MODULES['a8r_repeat'].engine.score.counts;reports={}
 for study,(_,people)in grid.STUDIES.items():
  profiles={};controls={label:{}for label in('full_control_strict','no_memory_strict_reused')}
  for pid in people:
   own=[r for r in rows if r['person']==pid];answer={q:r['gold']for r in own for q in r['query_ids']}
   for method in grid.METHODS:profiles[pid+':'+method+':card']={'strict_both_generations':count(own,[answer]*4)}
   for label,prediction in(('full_control_strict',answer),('no_memory_strict_reused',{q:'U'for q in answer})):
    for cohort,value in count(own,[prediction]).items():controls[label].setdefault(cohort,Counter()).update(value)
  reports[study]={'fixture_only_not_measured':True,'scores':{'profiles':profiles},
   'known_original_usage':{'input_tokens':2,'output_tokens':1,'cached_input_tokens':1,'reasoning_output_tokens':1,'total_tokens':3},
   'missing_original_usage':1,'actual_original_attempts':2,**{l:{k:dict(v)for k,v in c.items()}for l,c in controls.items()}}
 return reports

class GridArithmeticTests(unittest.TestCase):
 def test_arithmetic_fixed_profile_mapping_does_not_double_count_methods(self):
  result=grid.combine_reports(oracle_arithmetic_fixture())
  self.assertEqual(result['fictional_source_worlds'],8)
  for method in grid.METHODS:
   self.assertEqual(result['methods'][method]['joint'],{'planned':120,'correct':120,'missing':0})
   self.assertEqual(result['methods'][method]['known']['planned'],58)
   self.assertEqual(result['methods'][method]['unknown']['planned'],62)
  self.assertFalse(result['methods_cases_are_independent'])
 def test_arithmetic_missing_parent_retains_original_known_and_unknown_denominators(self):
  reports=oracle_arithmetic_fixture();rows=[r for r in grid.canonical.inputs()['rows']if r['person']=='b6t']
  reports['remaining_repeat']['scores']['profiles']['b6t:source-order-v3:card']['strict_both_generations']=grid.MODULES['a8r_repeat'].engine.score.counts(rows,[{}]*4)
  result=grid.combine_reports(reports)['methods']['source-order-v3']
  self.assertEqual(result['joint'],{'planned':120,'correct':105,'missing':15})
  self.assertEqual(result['known'],{'planned':58,'correct':51,'missing':7})
  self.assertEqual(result['unknown'],{'planned':62,'correct':54,'missing':8})
 def test_arithmetic_unknown_cost_is_not_filled_or_subsets_added(self):
  result=grid.combine_reports(oracle_arithmetic_fixture())
  self.assertEqual(result['actual_original_attempts'],6)
  self.assertEqual(result['known_original_usage']['total_tokens'],9)
  self.assertEqual(result['missing_original_usage'],3)
  self.assertEqual(result['new_model_calls'],0)

class GridArchiveTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=grid.archives()
 def test_actual_three_studies_replay_without_service_or_replacing_old49(self):
  old=ROOT/'benchmarks/epistemic-transfer-v1/measured.synthetic.json';before=grid.canonical.sha(old)
  with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:result=grid.summarize(self.data)
  backend.assert_not_called();self.assertEqual(grid.canonical.sha(old),before)
  self.assertEqual(result['primary_cases_per_method'],120);self.assertEqual(result['answers_per_primary_case'],8)
  self.assertLessEqual(result['actual_original_attempts'],107)
  self.assertFalse(result['old49_missing_cases_filled']);self.assertFalse(result['population_stability_estimated'])
 def test_missing_study_and_other_scope_substitution_are_rejected(self):
  data=dict(self.data);data.pop('remaining_repeat')
  with self.assertRaises(ValueError):grid.summarize(data)
  data=dict(self.data);data['remaining_repeat']=data['ambiguous_repeat']
  with self.assertRaises(ValueError):grid.summarize(data)
 def test_profile_substitution_cannot_silently_fill_the_grid(self):
  data=copy.deepcopy(self.data);data['remaining_repeat']['sources']['b6t']=data['remaining_repeat']['sources']['e4q']
  with self.assertRaises(ValueError):grid.summarize(data)
 def test_saved_derived_report_cannot_drift_even_with_a_new_checksum(self):
  report=grid.summarize(self.data)
  with tempfile.TemporaryDirectory()as tmp:
   path=Path(tmp)/'summary.json';report['methods']['source-order-v3']['joint']['planned']-=1
   path.write_text(json.dumps(report,ensure_ascii=False));path.with_suffix('.sha256').write_text(grid.canonical.sha(path)+'\n')
   with self.assertRaises(ValueError):grid.check_saved(path)
if __name__=='__main__':unittest.main()
