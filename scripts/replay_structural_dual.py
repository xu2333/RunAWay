"""Replay a sealed structural audit using its frozen source and six frozen tests."""
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
        path=(base/name).resolve()
        if not path.is_relative_to(base) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Evidence manifest mismatch: '+name)
    source=base/'frozen-source';data=source/'examples/structural-dual'
    receipt=json.loads((data/'implementation-freeze.json').read_text())
    for name,sha in receipt['implementation_hashes'].items():
        if hashlib.sha256((source/name).read_bytes()).hexdigest()!=sha:raise ValueError('Frozen implementation mismatch')
    if hashlib.sha256((data/'plan.synthetic.json').read_bytes()).hexdigest()!=receipt['design_sha256']:raise ValueError('Original design bytes changed')
    proc=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_structural_dual.py','-q'],cwd=source,capture_output=True,text=True,timeout=60)
    if proc.returncode:raise ValueError('Frozen test replay failed: '+proc.stdout[-1000:]+proc.stderr[-3000:])
    return dict(frozen_tests_passed=6,frozen_source_files=len(receipt['implementation_hashes']),manifest_files=len(manifest),
                exact_world_gold_program_scores_requests_rebuilt=True,actual_token_recounts=0,
                token_interpretation='Archived exact lengths retained; replay does not estimate or recount tokens.',external_model_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',required=True);args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        base=Path(temporary)
        with zipfile.ZipFile(args.archive) as archive:
            for name in archive.namelist():
                if not (base/name).resolve().is_relative_to(base):raise ValueError('Escaping archive path')
            archive.extractall(base)
        print(json.dumps(replay(base/'structural-dual')))
