import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]/'benchmarks/support-extraction-v1'
spec=importlib.util.spec_from_file_location('coverage_public_check',HERE/'check_coverage.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)

class CoverageBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.value=json.loads((HERE/'coverage-observed.synthetic.json').read_text())

    def test_actual_outputs_and_negative_gate_are_reproducible(self):
        result=check.validate(self.value)
        self.assertTrue(result['passed'])
        self.assertFalse(result['stable_coverage_strict_pass'])
        self.assertEqual(result['whole_turn_attempts'],62)
        self.assertEqual(result['missing_usage_records'],1)

    def test_duplicate_execution_and_substituted_answer_are_rejected(self):
        value=copy.deepcopy(self.value);value['executions'][1]['execution_id']=value['executions'][0]['execution_id']
        with self.assertRaises(ValueError):check.validate(value)
        value=copy.deepcopy(self.value);group=value['groups']['luna_coverage_card'];pid=next(iter(group['answers']));key=next(iter(group['answers'][pid]));group['answers'][pid][key]='invented answer'
        with self.assertRaises(ValueError):check.validate(value)

    def test_failed_diagnostic_cannot_be_replaced_or_replayed(self):
        value=copy.deepcopy(self.value);failed=next(row for row in value['closed_diagnostic']['executions'] if row['outcome']=='failed');value['executions'][0]['request_id']=failed['request_id']
        with self.assertRaises(ValueError):check.validate(value)
        value=copy.deepcopy(self.value);failed=next(row for row in value['closed_diagnostic']['executions'] if row['outcome']=='failed');value['closed_diagnostic']['raw_answers'][failed['group']][failed['diagnostic']]={'q12':'U'}
        with self.assertRaises(ValueError):check.validate(value)

if __name__=='__main__':unittest.main()
