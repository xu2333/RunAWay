"""Export reviewed graph-pilot synthetic evidence; no local grant/envelopes."""
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


shared = load('graph_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('graph_export_replay', ROOT / 'scripts/replay_action_revision_pilot.py')


def export(root):
    return shared.export(Path(root), replay_fn=replay.replay, kind=replay.KIND, record_fields=('method',),
        extra={'answers_per_case': 4, 'generated_cards_planned': 1, 'fresh_generation_stability_test': False,
               'independent_reference_acceptance': False, 'validates_j16_or_development': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT); args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream: stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream: stream.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
