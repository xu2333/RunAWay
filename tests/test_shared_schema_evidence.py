import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('shared_replay',ROOT/'scripts/replay_shared_schema.py');replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)


class SharedSchemaEvidenceTests(unittest.TestCase):
    def test_frozen_proofs_replay_without_services_or_token_recounts(self):
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(ROOT/'examples/shared-schema-evidence.synthetic.zip') as z:z.extractall(temporary)
            result=replay.replay(Path(temporary)/'shared-schema')
        self.assertEqual(result['frozen_tests_passed'],8);self.assertEqual(result['actual_token_recounts'],0);self.assertEqual(result['external_model_calls'],0)

    def test_required_id_tamper_rejected_after_outer_rehash(self):
        with tempfile.TemporaryDirectory() as temporary:
            with zipfile.ZipFile(ROOT/'examples/shared-schema-evidence.synthetic.zip') as z:z.extractall(temporary)
            base=Path(temporary)/'shared-schema';rel='frozen-source/examples/shared-schema/requests.synthetic.json';path=base/rel
            value=json.loads(path.read_text());value['development_jobs'][0]['request']['schema']['properties']['answers']['required'].pop();path.write_text(json.dumps(value))
            manifest=json.loads((base/'manifest.json').read_text());manifest[rel]=hashlib.sha256(path.read_bytes()).hexdigest();(base/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'Frozen schema replay failed'):replay.replay(base)


if __name__=='__main__':unittest.main()
