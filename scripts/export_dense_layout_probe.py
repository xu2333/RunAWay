"""Export reviewed fixed-view synthetic evidence without local grants/envelopes."""
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


shared = load('dense_read_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('dense_read_export_replay', ROOT / 'scripts/replay_dense_layout_probe.py')


def export(root):
    root = Path(root)
    return shared.export(root, replay_fn=replay.replay, kind=replay.KIND, record_fields=('method', 'view_sha256'),
        extra={'fixed_views': replay.engine.plan.read(root / 'views.public.json'),
            'source_derivation_sha256': replay.engine.plan.sha(replay.engine.plan.derived.DEFAULT),
            'expanded_is_uncapped_diagnostic_not_memory_candidate': True,
            'fresh_generation_stability_test': False, 'independent_reference_acceptance': False,
            'validates_j16_or_development': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT)
    args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream:
        stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream:
        stream.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
