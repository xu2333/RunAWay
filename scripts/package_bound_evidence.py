"""Package declared synthetic D-0011 evidence, redacting checkout prefixes in copies."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    source=ROOT/'runs/decision-memory-v2'
    plan=json.loads((source/'fresh-validation/snapshot.synthetic.json').read_text())
    if plan['origin']!='fully_synthetic':raise ValueError('Synthetic plan required')
    entries=[source/'transport-diagnosis.json']
    for stage in ['fresh-validation','offline-replay','execution-ledger']:
        entries.extend(p for p in sorted((source/stage).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.json','.py','.mjs','.jsonl'))
    manifest={}
    target=ROOT/'examples/bound-memory-evidence.synthetic.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in entries:
            if path.is_symlink():raise ValueError('Refusing symlink evidence')
            original=path.read_bytes();published=original.decode('utf-8').replace(str(ROOT),'<PROJECT_ROOT>').encode('utf-8')
            name=str(path.relative_to(source));manifest[name]={'original_sha256':hashlib.sha256(original).hexdigest(),'published_sha256':hashlib.sha256(published).hexdigest(),'checkout_prefix_redacted':published!=original}
            archive.writestr('decision-memory-v2/'+name,published)
        archive.writestr('decision-memory-v2/redaction-manifest.json',json.dumps({'files':manifest,'note':'Original request fingerprints refer to original unredacted requests. Redacted copies are for inspection, not exact-request cache reuse.'},indent=2)+'\n')
    print(json.dumps({'files':len(entries),'redacted_files':sum(row['checkout_prefix_redacted'] for row in manifest.values()),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
