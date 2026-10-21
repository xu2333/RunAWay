"""Power guard ownership and fail-closed controls; no real model calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('guarded384_test_study',ROOT/'benchmarks/guarded384-v1/study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class Guarded384Tests(unittest.TestCase):
 def test_unrelated_idle_assertion_does_not_count_as_owned(self):
  output='pid 999999(caffeinate): [0xtest] PreventUserIdleSystemSleep named: test'
  with patch.object(s.platform,'system',return_value='Darwin'),patch.object(s.subprocess,'check_output',side_effect=[output,'999998']):self.assertFalse(s.guard_status()['owned_active'])
  with patch.object(s.platform,'system',return_value='Darwin'),patch.object(s.subprocess,'check_output',side_effect=[output,str(s.os.getpid())]):self.assertTrue(s.guard_status()['owned_active'])
 def test_missing_guard_stops_before_intent_and_backend(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'proposal'
   with patch.object(s.h,'runtime_metadata',return_value={'mock':True}):s.prepare(out)
   with patch.object(s,'guard_status',return_value={'owned_active':False}),patch.object(s.h.generation,'codex_generate') as backend:
    with self.assertRaisesRegex(ValueError,'Owned idle-sleep'):s.execute(out)
    backend.assert_not_called();self.assertFalse((out/'service-intent.json').exists())
 def test_fake_complete_matrix_still_executes13_independent_calls(self):
  import test_frozen384 as baseline
  with patch.object(baseline,'s',s):baseline.Frozen384Tests().test_complete_fake_run_has13_unique_executions_but9_inputs()
 def test_fixed_scope_matches_earlier_plan_without_old_answers(self):
  f=s.w.fixtures();products=s.cards();self.assertEqual(len(s.plan()),13);self.assertEqual(set(products),set(s.w.PEOPLE));self.assertEqual(s.request_for(f,'card','t35c',products),s.request_for(f,'repeat','t35c',products));self.assertIn('scripts/with_awake.py',s.source_names());self.assertIn('benchmarks/frozen384-v1/observed.synthetic.json',s.source_names())

if __name__=='__main__':unittest.main()
