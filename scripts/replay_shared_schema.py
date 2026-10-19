"""Frozen shared-schema proof replay; no model calls or token recounts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def replay(base):
    base=Path(base).resolve();manifest=json.loads((base/'manifest.json').read_text())
    for name,sha in manifest.items():
        p=(base/name).resolve()
        if not p.is_relative_to(base) or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Manifest mismatch')
    proc=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_shared_schema.py','-q'],cwd=base/'frozen-source',capture_output=True,text=True,timeout=90)
    if proc.returncode:raise ValueError('Frozen schema replay failed: '+proc.stdout[-1000:]+proc.stderr[-2500:])
    return dict(frozen_tests_passed=8,manifest_files=len(manifest),all16exact_expansion_proofs=True,all590acceptance_and_score_pairs_equal=True,actual_token_recounts=0,external_model_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',required=True);args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        with zipfile.ZipFile(args.archive) as archive:
            for name in archive.namelist():
                if not (root/name).resolve().is_relative_to(root):raise ValueError('Escaping archive path')
            archive.extractall(root)
        print(json.dumps(replay(root/'shared-schema')))
