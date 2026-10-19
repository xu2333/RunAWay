import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('structural_replay',ROOT/'scripts/replay_structural_dual.py')
replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)


class StructuralEvidenceTests(unittest.TestCase):
    def test_original_archive_frozen_replay_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(ROOT/'examples/structural-dual-evidence.synthetic.zip') as z:z.extractall(temporary)
            result=replay.replay(Path(temporary)/'structural-dual')
        self.assertEqual((result['frozen_source_files'],result['manifest_files'],result['external_model_calls']),(52,72,0))
        self.assertEqual(result['actual_token_recounts'],0)

    def test_tampered_gold_fails_even_if_outer_hash_is_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(ROOT/'examples/structural-dual-evidence.synthetic.zip') as z:z.extractall(temporary)
            base=Path(temporary)/'structural-dual';rel='frozen-source/examples/structural-dual/holdout-expected.synthetic.json';path=base/rel
            data=json.loads(path.read_text());pid=next(iter(data));key=next(iter(data[pid]));data[pid][key]['reported_status']='forged'
            path.write_text(json.dumps(data));manifest=json.loads((base/'manifest.json').read_text());manifest[rel]=hashlib.sha256(path.read_bytes()).hexdigest();(base/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'Frozen test replay failed'):replay.replay(base)


if __name__=='__main__':unittest.main()
