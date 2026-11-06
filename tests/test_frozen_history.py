"""Historical checks retain their bytes and cannot hide live executor regressions."""
import copy
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('frozen_history_tests_helper', ROOT / 'scripts/frozen_history.py')
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


class FrozenHistoryTests(unittest.TestCase):
    def run_report_fixture(self, current, historical, current_code=0):
        calls = []
        output = io.StringIO()
        def fake_child(root, mode, payload):
            calls.append(mode)
            report = current if mode == 'current-tests' else historical
            if report is not None:
                text = report if isinstance(report, str) else json.dumps(report)
                Path(payload['result']).write_text(text)
            return current_code if mode == 'current-tests' else 0
        with patch.object(history, 'partition', return_value=(['current_fixture'], ['historical_fixture'])), \
                patch.object(history, 'snapshot', return_value=contextlib.nullcontext(history.ROOT)), \
                patch.object(history, 'child', side_effect=fake_child), contextlib.redirect_stdout(output):
            code = history.check_tests()
        summary = json.loads(output.getvalue().splitlines()[-1])['offline_test_suites']
        self.assertEqual(calls, ['current-tests', 'historical-tests'])
        return code, summary

    def test_zero_exit_without_result_cannot_pass_and_other_partition_still_runs(self):
        valid = {'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0}
        for current, historical in ((None, valid), (valid, None), (None, None)):
            with self.subTest(current=current, historical=historical):
                code, rows = self.run_report_fixture(current, historical)
                self.assertEqual(code, 1)
                self.assertTrue(any(not row['report_valid'] for row in rows.values()))
                self.assertTrue(all(row['exit_code'] == 0 for row in rows.values()))

    def test_complete_success_reports_keep_counts_for_both_partitions(self):
        valid = {'tests': 3, 'failures': 0, 'errors': 0, 'skipped': 0}
        code, rows = self.run_report_fixture(valid, valid)
        self.assertEqual(code, 0)
        self.assertEqual(sum(row['tests'] for row in rows.values()), 6)
        self.assertTrue(all(row['report_valid'] for row in rows.values()))

    def test_malformed_empty_and_forged_results_cannot_hide_missing_tests(self):
        valid = {'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0}
        for bad in ('{', [], {**valid, 'tests': 0}, {**valid, 'tests': True},
                    {**valid, 'failures': -1}, {**valid, 'exit_code': 0},
                    {'tests': 1, 'failures': 0, 'errors': 0}):
            with self.subTest(report=bad):
                code, rows = self.run_report_fixture(bad, valid)
                self.assertEqual(code, 1)
                self.assertFalse(rows['current-tests']['report_valid'])
                self.assertTrue(rows['historical-tests']['report_valid'])

    def test_process_failure_or_reported_failures_cannot_be_overridden(self):
        valid = {'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0}
        for report, exit_code in ((valid, 1), ({**valid, 'failures': 1}, 0),
                                  ({**valid, 'errors': 1}, 0), ({**valid, 'exit_code': 0}, 1)):
            with self.subTest(report=report, exit_code=exit_code):
                code, rows = self.run_report_fixture(report, valid, exit_code)
                self.assertEqual(code, 1)
                self.assertEqual(rows['current-tests']['exit_code'], exit_code)

    def test_partition_assigns_every_module_once_and_keeps_regressions_current(self):
        current, historical = history.partition()
        expected = {p.stem for p in (ROOT / 'tests').glob('test*.py')}
        self.assertEqual(set(current) | set(historical), expected)
        self.assertFalse(set(current) & set(historical))
        self.assertIn('test_taste_executor', current)
        self.assertIn('test_frozen_history', current)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'tests/testfuture.py').touch()
            (root / 'tests/unit').mkdir()
            (root / 'tests/unit/__init__.py').touch()
            (root / 'tests/unit/test_nested.py').touch()
            with patch.object(history, 'manifest', return_value={'test_modules': []}):
                self.assertEqual(history.partition(root), (['testfuture', 'unit.test_nested'], []))
        value = copy.deepcopy(history.manifest())
        for extra in ('test_taste_executor', 'test_missing_history_module', historical[0]):
            bad = copy.deepcopy(value)
            bad['test_modules'].append(extra)
            with patch.object(history, 'manifest', return_value=bad):
                with self.assertRaises(ValueError):
                    history.partition()

    def test_snapshot_keeps_original_bytes_and_leaves_live_source_and_evidence_unchanged(self):
        live = (ROOT / history.EXECUTOR).read_bytes()
        evidence = Path('benchmarks/source-id-enum-repeat-v1/measured.synthetic.json')
        with history.snapshot() as root:
            self.assertEqual(history.sha(root / history.EXECUTOR), history.ORIGINAL_SHA256)
            self.assertNotEqual((root / history.EXECUTOR).read_bytes(), live)
            self.assertEqual((root / evidence).read_bytes(), (ROOT / evidence).read_bytes())
            self.assertEqual((root / 'runaway/card.py').read_bytes(), (ROOT / 'runaway/card.py').read_bytes())
            self.assertFalse((root / '.git').exists())
            (root / history.EXECUTOR).write_text('discarded temporary change')
        self.assertFalse(root.exists())
        self.assertEqual((ROOT / history.EXECUTOR).read_bytes(), live)

    def test_changed_snapshot_or_override_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / history.ARCHIVE
            archive.mkdir(parents=True)
            value = history.manifest()
            (archive / 'manifest.json').write_text(json.dumps(value))
            blob = archive / 'taste_executor.py.txt'
            blob.write_bytes((ROOT / history.ARCHIVE / blob.name).read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'snapshot differs'):
                history.manifest(root)
            value['source_overrides']['runaway/card.py'] = value['source_overrides'][history.EXECUTOR]
            (archive / 'manifest.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'source override'):
                history.manifest(root)

    def test_isolated_child_loads_original_module_blocks_service_and_detects_other_drift(self):
        with history.snapshot() as root:
            probe = root / 'tests/test_history_isolation_probe.py'
            probe.write_text('''import hashlib, importlib.util, unittest
from pathlib import Path
from runaway import generation, taste_executor
ROOT = Path(__file__).resolve().parents[1]
class Probe(unittest.TestCase):
 def test_isolation_and_integrity(self):
  self.assertEqual(Path(taste_executor.__file__).resolve(), ROOT/'runaway/taste_executor.py')
  self.assertEqual(hashlib.sha256(Path(taste_executor.__file__).read_bytes()).hexdigest(),
   "57b7165a596cc731547a804b7b81f2a2c22feaa14b44182f478f222acdebb041")
  with self.assertRaisesRegex(RuntimeError, 'cannot invoke'):
   generation.codex_generate('offline guard probe', 'no-model')
  spec=importlib.util.spec_from_file_location('drift_probe',ROOT/'benchmarks/fresh-source-contrast-v1/plan.py')
  plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
  plan.implementation()
  path=ROOT/'runaway/card.py';path.write_bytes(path.read_bytes()+b'\\n')
  with self.assertRaisesRegex(ValueError, 'dependency drift'):plan.implementation()
''')
            result = root / 'probe-result.json'
            code = history.child(root, 'historical-tests',
                                 {'modules': [probe.stem], 'result': str(result)})
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(result.read_text())['tests'], 1)

    def test_replay_refuses_unlisted_or_real_execution_entry(self):
        with self.assertRaises(ValueError):
            history.replay('runaway/taste_executor.py', [])
        with self.assertRaises(ValueError):
            history.replay('scripts/memory.py', ['--run'])
        with patch.object(history, 'child', return_value=0) as child:
            self.assertEqual(history.replay('scripts/review_memory.py', ['demo', '--out', 'review-output']), 0)
        payload = child.call_args.args[2]
        self.assertEqual(payload['args'], ['demo', '--out', str(Path('review-output').resolve())])
        with patch.object(history, 'child', return_value=0) as child:
            self.assertEqual(history.replay('scripts/export_fresh_enum_pipeline.py',
                ['--observations', 'observed-run', '--out=portable.json']), 0)
        self.assertEqual(child.call_args.args[2]['args'],
            ['--observations', str(Path('observed-run').resolve()),
             '--out=' + str(Path('portable.json').resolve())])


if __name__ == '__main__':
    unittest.main()
