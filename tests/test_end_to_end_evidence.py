import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from runaway import end_to_end_runner as runner, shared_schema_executor as previous

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('end_to_end_replay', ROOT/'scripts/replay_end_to_end_taste.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class EndToEndEvidenceTests(unittest.TestCase):
    def test_exact_product_outputs_scores_usage_and_consumed_call_exclusion(self):
        archive = ROOT/'examples/end-to-end-taste-evidence.synthetic.zip'
        summary = json.loads((ROOT/'examples/end-to-end-taste-results.synthetic.json').read_text())
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), summary['archive_sha256'])
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(archive) as z:
                z.extractall(tmp)
            result = replay.replay(Path(tmp)/'end-to-end-taste')
        self.assertEqual(result, summary['replay'])
        self.assertEqual(result['correct'], {'full_history': 48, 'none': 10, 'own': 48, 'wrong': 28})
        self.assertEqual(result['known_service_usage']['total_tokens'], 93007)
        self.assertEqual(result['complete_characters'], {'p-eb31': 584, 'p-7a96': 607})
        self.assertEqual((result['new_model_calls'], result['prediction_denominator']), (0, 192))
        self.assertTrue(set(summary['request_ids']) <= runner.forbidden_ids(previous.archives()))
        with zipfile.ZipFile(archive) as z:
            f = json.loads(z.read('end-to-end-taste/frozen/fixtures.synthetic.json'))
        audit = json.loads((ROOT/'examples/end-to-end-taste/length-audit.synthetic.json').read_text())
        for p in f['histories']['people']:
            chars = sum(len(s['text']) for s in p['sources']['sources'])
            self.assertEqual(audit['people'][p['id']]['source_text_only_characters'], chars)
        self.assertEqual(audit['aggregate']['source_text_only_characters'], 1637)
        self.assertEqual(audit['aggregate']['complete_export_characters'], 1191)

    def test_rehashed_request_and_response_corruption_rejected(self):
        archive = ROOT/'examples/end-to-end-taste-evidence.synthetic.zip'
        for suffix in ('request', 'response'):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                with zipfile.ZipFile(archive) as z:
                    z.extractall(tmp)
                base = Path(tmp)/'end-to-end-taste'
                path = next((base/'service'/'calls').glob('*.'+suffix+'.json'))
                data = json.loads(path.read_text())
                if suffix == 'request':
                    data['prompt'] += ' changed'
                else:
                    # Corrupt the logical answer and rehash the envelope, so
                    # the manifest/envelope hash alone cannot detect the edit.
                    data['answer'] = {}
                    from runaway.card import canonical, digest
                    data['sha256'] = digest(canonical({k: v for k, v in data.items() if k != 'sha256'}))
                path.write_text(json.dumps(data))
                manifest = json.loads((base/'manifest.json').read_text())
                manifest[str(path.relative_to(base))] = hashlib.sha256(path.read_bytes()).hexdigest()
                (base/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    replay.replay(base)


if __name__ == '__main__':
    unittest.main()
