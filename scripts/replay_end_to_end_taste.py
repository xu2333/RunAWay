"""Offline replay of frozen browser compression and four blind reader arms."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def replay(root):
    if sys.flags.optimize:
        raise ValueError('Optimized Python unsupported')
    root = Path(root).resolve()
    manifest = json.loads((root / 'manifest.json').read_text())
    actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name != 'manifest.json'}
    if actual != set(manifest):
        raise ValueError('Evidence file inventory mismatch')
    for name, want in manifest.items():
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root) or hashlib.sha256(p.read_bytes()).hexdigest() != want:
            raise ValueError('Evidence manifest mismatch')
    proc = subprocess.run([sys.executable, '-I', '-B', 'verify.py'], cwd=root,
                          capture_output=True, text=True, timeout=60)
    if proc.returncode:
        raise ValueError('End-to-end replay failed: ' + proc.stderr[-1800:])
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        with zipfile.ZipFile(args.archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate archive entries')
            for item in z.infolist():
                if not (root / item.filename).resolve().is_relative_to(root) or item.file_size > 8_000_000:
                    raise ValueError('Escaping/oversized archive entry')
            z.extractall(root)
        print(json.dumps(replay(root / 'end-to-end-taste')))


if __name__ == '__main__':
    main()
