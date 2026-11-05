"""Historical checks retain their bytes and cannot hide live executor regressions."""
import copy
import importlib.util
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


if __name__ == '__main__':
    unittest.main()
