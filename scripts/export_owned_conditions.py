"""Export only reviewed fictional evidence from the closed new42 scope."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


shared = load('owned_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('owned_export_replay', ROOT / 'scripts/replay_owned_conditions.py')


def export(root):
    root = Path(root)
    reference = replay.engine.plan.read(root / 'reference.consumed-development.private.json')
    return shared.export(root, replay_fn=replay.replay, kind=replay.KIND, record_fields=('method',),
        extra={'legacy_reference_rows': reference['legacy_rows'], 'disputed_reference_rows': reference['disputed_rows'],
               'disputed_reference_accepted': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT)
    args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream:
        stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream:
        stream.write(replay.engine.plan.sha(args.out) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
