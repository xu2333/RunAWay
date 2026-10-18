import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from scripts.build_temporal_protocol import protocol

ROOT = Path(__file__).resolve().parents[1]


class TemporalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(ROOT / 'examples/temporal-evidence.synthetic.zip') as archive:
            for name in archive.namelist():
                if not name.startswith('d0021/') or '..' in Path(name).parts:
                    raise ValueError('Unsafe archive member')
            archive.extractall(cls.temp.name)
        cls.base = Path(cls.temp.name) / 'd0021'

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def replay(self):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/replay_temporal_evidence.py'), '--base', str(self.base)], text=True, capture_output=True)

    def test_sealed_actual_calls_replay_against_saved_runtime_not_changed_product(self):
        result = self.replay()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout)
        stored = json.loads((self.base / 'report.synthetic.json').read_text())
        self.assertTrue(stored['checks']['actual_tokenizer_recounted'])
        actual['checks']['actual_tokenizer_recounted'] = True
        self.assertEqual(actual, stored)
        self.assertEqual(stored, json.loads((ROOT / 'examples/temporal-results.synthetic.json').read_text()))
        self.assertEqual(stored['calls']['execution_records'], 6)
        self.assertEqual(stored['scores']['temporal']['current_choice']['correct'], 16)
        self.assertEqual(stored['scores']['temporal']['historical_reconstruction']['planned'], 4)
        self.assertEqual(stored['paired_statistical_units'], 1)
        self.assertFalse(stored['new_holdout'])
        self.assertFalse(stored['real_person_fidelity_verified'])

    def test_manifest_privacy_and_frozen_source_bindings(self):
        manifest = json.loads((self.base / 'manifest.json').read_text())
        self.assertEqual(set(manifest), {str(p.relative_to(self.base)) for p in self.base.rglob('*') if p.is_file() and p.name != 'manifest.json'})
        for name, sha in manifest.items():
            data = (self.base / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), sha)
            self.assertNotIn('approval', name)
            self.assertNotIn('execution-intent', name)
            if not name.startswith(('frozen-source/', 'runtime-source/')):
                self.assertNotIn('/Users/', data.decode())
                self.assertNotIn('human_source', data.decode())
        contract = json.loads((self.base / 'contract.synthetic.json').read_text())
        for name, sha in contract['source_hashes'].items():
            self.assertEqual(hashlib.sha256((self.base / 'frozen-source' / name).read_bytes()).hexdigest(), sha)

    def test_tampered_raw_usage_is_rejected(self):
        path = next((self.base / 'calls').glob('*.response.json'))
        original = path.read_bytes()
        try:
            value = json.loads(original); value['provenance']['usage'][0]['input_tokens'] += 1
            path.write_text(json.dumps(value))
            self.assertNotEqual(self.replay().returncode, 0)
        finally:
            path.write_bytes(original)

    def test_browser_protocol_is_generated_from_current_product(self):
        self.assertEqual(json.loads((ROOT / 'web/dist/temporal-protocol.json').read_text()), protocol())

    def test_optimized_mode_cannot_skip_replay_checks(self):
        result = subprocess.run([sys.executable, '-O', '-B', str(ROOT / 'scripts/replay_temporal_evidence.py'), '--base', str(self.base)], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Evidence replay requires assertions enabled', result.stderr)


if __name__ == '__main__':
    unittest.main()
