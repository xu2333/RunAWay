import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.package_stress_service import equal, replay

ROOT = Path(__file__).resolve().parents[1]


class StressServiceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        with zipfile.ZipFile(ROOT / 'examples/stress-service-evidence.synthetic.zip') as archive:
            for name in archive.namelist():
                if not name.startswith('d0018/') or '..' in Path(name).parts:
                    raise ValueError('Unsafe archive member')
            archive.extractall(cls.root)
        cls.base = cls.root / 'd0018'

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_raw_evidence_reconstructs_all_predictions_products_scores_gates_and_costs(self):
        stored = json.loads((self.base / 'report.synthetic.json').read_text())
        computed = replay(self.base)
        self.assertTrue(stored['checks']['actual_tokenizer_recounted'])
        # Public replay needs no tokenizer installation; the sealed audit did the recount.
        computed['checks']['actual_tokenizer_recounted'] = True
        equal(computed, stored)
        equal(stored, json.loads((ROOT / 'examples/stress-service-results.synthetic.json').read_text()))
        self.assertEqual(stored['independent_paired_clusters'], 2)
        self.assertFalse(stored['real_person_fidelity_verified'])
        for tasks in stored['scores'].values():
            self.assertEqual(tasks['current_choice']['planned'], 224)
            self.assertEqual(tasks['historical_reconstruction']['planned'], 76)
            self.assertEqual(tasks['joint']['planned'], 300)

    def test_manifest_and_data_scope(self):
        manifest = json.loads((self.base / 'manifest.json').read_text())
        self.assertEqual(set(manifest), {str(p.relative_to(self.base)) for p in self.base.rglob('*')
                                        if p.is_file() and p.name != 'manifest.json'})
        for name, sha in manifest.items():
            path = self.base / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
            self.assertNotIn('approval', name)
            self.assertNotIn('execution-intent', name)
            if not name.startswith('frozen-source/'):
                text = path.read_text()
                self.assertNotIn('/Users/', text)
                self.assertNotIn('human_source', text)
                self.assertNotIn('access_token', text)

    def test_changed_report_score_is_rejected(self):
        path = self.base / 'raw-report.synthetic.json'
        original = path.read_bytes()
        try:
            value = json.loads(original)
            value['scores']['full_history']['current_choice']['correct'] -= 1
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                replay(self.base)
        finally:
            path.write_bytes(original)

    def test_changed_raw_response_is_rejected(self):
        path = next((self.base / 'calls').glob('*.response.json'))
        original = path.read_bytes()
        try:
            value = json.loads(original)
            value['provenance']['usage'][0]['input_tokens'] += 1
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                replay(self.base)
        finally:
            path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
