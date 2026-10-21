"""Recorded power condition binding, without new service calls."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('guarded384_record_tests',ROOT/'benchmarks/guarded384-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)

class Guarded384ObservedTests(unittest.TestCase):
 def test_real_records_and_per_call_owned_guard_reproduce(self):
  data=check.s.read(ROOT/'benchmarks/guarded384-v1/observed.synthetic.json');r=check.validate(data);self.assertGreater(r['actual_calls'],0);self.assertLessEqual(r['actual_calls'],13);self.assertEqual(check.verify_exports(data)['owned_guard_observations_verified'],r['actual_calls'])
 def test_guard_loss_or_erasing_previous_unknown_usage_is_rejected(self):
  data=check.s.read(ROOT/'benchmarks/guarded384-v1/observed.synthetic.json');bad=copy.deepcopy(data);bad['guard_observations'][0]['owned_active']=False
  with self.assertRaisesRegex(ValueError,'guard missing'):check.verify_exports(bad)
  bad=copy.deepcopy(data);bad['preceding_unguarded_ledger']['executions_missing_usage']=0
  with self.assertRaisesRegex(ValueError,'Preceding'):check.verify_exports(bad)

if __name__=='__main__':unittest.main()
