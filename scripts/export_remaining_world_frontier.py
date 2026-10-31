"""Export the closed world40scope through the shared sealed-evidence exporter."""
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


archive = load('export_world_archive', ROOT / 'scripts/replay_remaining_world_frontier.py')
exporter = load('export_world_shared', ROOT / 'scripts/export_compression_stability.py')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=archive.DEFAULT)
    args = parser.parse_args()
    ref = archive.engine.plan.read(args.run / 'reference.consumed-development.private.json')
    text, result = exporter.export(args.run.resolve(), replay_fn=archive.replay,
        kind='actual_remaining_world_frontier40', primary_key='primary_rows',
        extra={'legacy_reference_rows': ref['legacy_rows'], 'disputed_reference_rows': ref['disputed_rows'],
               'w14_reference_accepted': False, 'independent_semantic_acceptance': False})
    args.out.write_text(text, encoding='utf-8')
    args.out.with_suffix('.sha256').write_text(archive.engine.plan.sha(args.out) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
