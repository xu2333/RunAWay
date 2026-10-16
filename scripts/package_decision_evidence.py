"""Package only the declared synthetic experiment folders, never the workspace."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('development', 'development-audited', 'validation', 'action-control-development', 'transfer-validation')


def main():
    run = ROOT / 'runs/decision-memory-v1'
    entries = []
    for stage in STAGES:
        folder = run / stage
        plan_path = folder / ('snapshot.synthetic.json' if (folder / 'snapshot.synthetic.json').exists() else 'plan.json')
        plan = json.loads(plan_path.read_text())
        if plan.get('origin', plan.get('world', {}).get('origin')) != 'fully_synthetic':
            raise ValueError('Not an explicitly synthetic stage')
        for p in sorted(folder.rglob('*')):
            if not p.is_file():
                continue
            if p.is_symlink() or '__pycache__' in p.parts or p.suffix not in ('.json', '.jsonl', '.py', '.mjs'):
                continue
            entries.append(p)
    manifest = {str(p.relative_to(run)): hashlib.sha256(p.read_bytes()).hexdigest() for p in entries}
    target = ROOT / 'examples/decision-memory-evidence.synthetic.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in entries:
            archive.write(p, str(Path('decision-memory-v1') / p.relative_to(run)))
        archive.writestr('decision-memory-v1/manifest.json', json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'files': len(entries), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size}))


if __name__ == '__main__': main()
