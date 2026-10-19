import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from runaway import shared_schema_executor as executor

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot_replay', ROOT / 'scripts/replay_shared_schema_pilot.py')
replay = importlib.util.module_from_spec(spec); spec.loader.exec_module(replay)


class PilotEvidenceTests(unittest.TestCase):
    def test_frozen_real_outputs_scores_usage_and_new_call_exclusion(self):
        archive = ROOT / 'examples/shared-schema-pilot-evidence.synthetic.zip'
        summary = json.loads((ROOT / 'examples/shared-schema-pilot-results.synthetic.json').read_text())
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), summary['archive_sha256'])
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(archive) as z: z.extractall(temporary)
            result = replay.replay(Path(temporary) / 'shared-schema-pilot')
        self.assertEqual(result['original_responses'], 2)
        self.assertEqual(result['usage_total'], 14976)
        self.assertEqual(result['new_model_calls'], 0)
        source = executor.shared.load_source(ROOT / executor.SOURCE)
        self.assertTrue(set(summary['request_ids']) <= set(executor.forbidden_ids(source, executor.archives())))

    def test_rehashed_changed_request_still_fails_exact_original_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(ROOT / 'examples/shared-schema-pilot-evidence.synthetic.zip') as z: z.extractall(temporary)
            base = Path(temporary) / 'shared-schema-pilot'
            path = next((base / 'calls').glob('*.request.json'))
            value = json.loads(path.read_text()); value['prompt'] += 'changed'
            path.write_text(json.dumps(value))
            manifest = json.loads((base / 'manifest.json').read_text())
            manifest[str(path.relative_to(base))] = hashlib.sha256(path.read_bytes()).hexdigest()
            (base / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError): replay.replay(base)
