"""Offline replay of the two real shared-schema reads. Never calls a model."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def replay(base):
    if sys.flags.optimize:raise ValueError('Optimized Python unsupported')
    base=Path(base).resolve();manifest=json.loads((base/'manifest.json').read_text())
    for name,want in manifest.items():
        p=(base/name).resolve()
        if not p.is_relative_to(base) or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=want:
            raise ValueError('Pilot evidence manifest mismatch')
    proc=subprocess.run([sys.executable,'-B','verify.py'],cwd=base,capture_output=True,text=True,timeout=30)
    if proc.returncode:raise ValueError('Pilot replay failed: '+proc.stderr[-1800:])
    return json.loads(proc.stdout)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',required=True);args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary).resolve()
        with zipfile.ZipFile(args.archive) as z:
            for name in z.namelist():
                if not (root/name).resolve().is_relative_to(root):raise ValueError('Escaping archive')
            z.extractall(root)
        print(json.dumps(replay(root/'shared-schema-pilot')))
