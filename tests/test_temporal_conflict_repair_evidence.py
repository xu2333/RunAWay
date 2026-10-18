import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ConflictRepairEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(ROOT / 'examples/temporal-conflict-repair-evidence.synthetic.zip') as archive:
            if any(not n.startswith('d0026/') or '..' in Path(n).parts for n in archive.namelist()):
                raise ValueError('Unsafe evidence member')
            archive.extractall(cls.temp.name)
        cls.base = Path(cls.temp.name) / 'd0026'

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def replay(self, optimized=False):
        return subprocess.run([sys.executable, *(['-O'] if optimized else []), '-B', str(ROOT / 'scripts/replay_temporal_scale_evidence.py'), '--base', str(self.base)], capture_output=True, text=True)

    def test_actual_four_calls_replay_without_model_or_current_product(self):
        result = self.replay(); self.assertEqual(result.returncode, 0, result.stderr)
        actual = json.loads(result.stdout); stored = json.loads((self.base / 'report.synthetic.json').read_text())
        self.assertTrue(stored['checks']['actual_tokenizer_recounted'])
        actual['checks']['actual_tokenizer_recounted'] = True
        self.assertEqual(actual['actual_memory_token_recounts'], 0)
        actual['actual_memory_token_recounts'] = 2
        self.assertEqual(actual, stored)
        self.assertEqual(stored, json.loads((ROOT / 'examples/temporal-conflict-repair-results.synthetic.json').read_text()))
        self.assertEqual(stored['calls']['execution_records'], 4)
        self.assertEqual(stored['calls']['known_usage']['total_tokens'], 58038)
        self.assertEqual(stored['scores']['current_choice']['correct'], 112)
        self.assertEqual(stored['scores']['historical_reconstruction']['planned'], 38)
        self.assertEqual(stored['scores']['joint']['planned'], 150)
        self.assertEqual(stored['decision'], 'D-0026')
        self.assertEqual(stored['actual_memory_token_recounts'], 2)
        self.assertTrue(all(len(c['current_statuses']) == 27 and all(c['current_statuses']) for c in stored['source_to_event_checks'].values()))
        self.assertEqual(stored['paired_statistical_units'], 1)
        self.assertFalse(stored['new_holdout']); self.assertFalse(stored['real_person_fidelity_verified'])

    def test_manifest_input_source_bindings_and_private_data_exclusion(self):
        manifest = json.loads((self.base / 'manifest.json').read_text())
        self.assertEqual(set(manifest), {str(p.relative_to(self.base)) for p in self.base.rglob('*') if p.is_file() and p.name != 'manifest.json'})
        for name, sha in manifest.items():
            data = (self.base / name).read_bytes(); self.assertEqual(hashlib.sha256(data).hexdigest(), sha)
            self.assertNotIn('approval', name); self.assertNotIn('execution-intent', name)
            if not name.startswith('frozen-source/'):
                for private in ('/Users/', 'human_source', 'access_token', 'refresh_token'):
                    self.assertNotIn(private, data.decode())
        contract = json.loads((self.base / 'contract.synthetic.json').read_text())
        for name, sha in contract['source_hashes'].items():
            self.assertEqual(hashlib.sha256((self.base / 'frozen-source' / name).read_bytes()).hexdigest(), sha)
        for name, sha in contract['input_hashes'].items():
            self.assertEqual(hashlib.sha256((self.base / contract['input_aliases'][name]).read_bytes()).hexdigest(), sha)

    def test_tampered_raw_usage_rejected(self):
        path = next((self.base / 'calls').glob('*.response.json')); original = path.read_bytes()
        try:
            d = json.loads(original); d['provenance']['usage'][0]['input_tokens'] += 1
            path.write_text(json.dumps(d)); self.assertNotEqual(self.replay().returncode, 0)
        finally: path.write_bytes(original)

    def test_changed_scores_and_old_controls_rejected(self):
        for name in ('raw-report.synthetic.json', 'prior-controls.synthetic.json'):
            path = self.base / name; original = path.read_bytes()
            try:
                d = json.loads(original)
                if isinstance(d, list): d[0]['response']['answer'][next(iter(d[0]['response']['answer']))] = 'U'
                else: d['scores']['current_choice']['correct'] -= 1
                path.write_text(json.dumps(d)); self.assertNotEqual(self.replay().returncode, 0)
            finally: path.write_bytes(original)

    def test_optimized_mode_does_not_skip_replay(self):
        result = self.replay(True); self.assertNotEqual(result.returncode, 0)
        self.assertIn('Evidence replay requires assertions enabled', result.stderr)


if __name__ == '__main__': unittest.main()
