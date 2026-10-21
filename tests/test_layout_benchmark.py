import copy
import importlib.util
import json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parents[1]/'benchmarks/support-extraction-v1';spec=importlib.util.spec_from_file_location('layout_public_check',HERE/'check_layout.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
class LayoutBenchmarkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.value=json.loads((HERE/'layout-observed.synthetic.json').read_text())
 def test_actual_matrix_and_both_draws_reproduce(self):
  result=check.validate(self.value);self.assertTrue(result['passed']);self.assertEqual(result['actual_calls'],50);self.assertEqual(result['unique_request_fingerprints'],38);self.assertFalse(result['stable_rows_strict_pass']);self.assertEqual(result['model_calls'],0)
 def test_changed_order_and_changed_facts_are_rejected(self):
  bad=copy.deepcopy(self.value);bad['completed_plan'][7],bad['completed_plan'][8]=bad['completed_plan'][8],bad['completed_plan'][7]
  with self.assertRaises(ValueError):check.validate(bad)
  bad=copy.deepcopy(self.value);pid=next(iter(bad['materials']['rows']));bad['materials']['rows'][pid]+='额外推断'
  with self.assertRaises(ValueError):check.validate(bad)
 def test_favorable_draw_substitution_and_duplicate_execution_are_rejected(self):
  bad=copy.deepcopy(self.value);first=bad['groups']['luna_rows'];repeat=bad['groups']['luna_rows_repeat']
  for field in ['answers','answers_sha256','summary']:first[field]=copy.deepcopy(repeat[field])
  with self.assertRaises(ValueError):check.validate(bad)
  bad=copy.deepcopy(self.value);bad['executions'][1]['execution_id']=bad['executions'][0]['execution_id']
  with self.assertRaises(ValueError):check.validate(bad)
if __name__=='__main__':unittest.main()
