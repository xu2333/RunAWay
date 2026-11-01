"""Export reviewed synthetic action-policy comparison evidence,excluding local grants."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('action_policy_export_shared', ROOT / 'scripts/export_compression_stability.py')
replay = load('action_policy_export_replay', ROOT / 'scripts/replay_action_policy_comparison.py')


def export(root):
    inputs = replay.engine.plan.inputs()
    return shared.export(Path(root), replay_fn=replay.replay, kind=replay.KIND, record_fields=('method',),
        extra={'answers_per_primary_case': 8, 'fresh_generations_planned': 4,
               'disputed_rows': inputs['disputed_rows'], 'legacy_rows': inputs['legacy_rows'],
               'independent_reference_acceptance': False, 'independent_generalization': False,
               'baseline_arm': True, 'changes_compiler_or_reader': False,
               'validates_h93_or_development': False,
               'guidance_informed_by_prior_consumed_development_failures': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=replay.DEFAULT); args = parser.parse_args()
    text, result = export(args.run.resolve())
    with args.out.open('x', encoding='utf-8') as stream: stream.write(text)
    with args.out.with_suffix('.sha256').open('x') as stream: stream.write(replay.engine.plan.sha(args.out)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
