"""Export reviewed fictional evidence, excluding local grants and transport data."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


shared = load('budgeted_probe_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('budgeted_probe_export_archive', ROOT / 'scripts/replay_budgeted_table_probe.py')


def export(root):
    root = Path(root)
    reference = replay.engine.plan.read(root / 'reference.consumed-development.private.json')
    return shared.export(root, replay_fn=replay.replay, kind=replay.KIND, record_fields=('method',),
        extra={'legacy_reference_rows': reference['legacy_rows'], 'disputed_reference_rows': reference['disputed_rows'],
               'independent_reference_acceptance': False, 'validates_j16_or_development': False,
               'can_combine_with_older39_into_new79_result': False})


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
