"""Replay the actual j16encoding-guidance comparison; no service capability."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('action_policy_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('action_policy_archive_engine', ROOT / 'benchmarks/action-policy-comparison-v1/engine.py')
INPUT_MANIFEST = '3c267e326608c9c217691768cfd967d2c3a4e53b249dea066c689f9fdd5cee19'
KIND = 'actual_action_policy14_j16_comparison'
DEFAULT = ROOT / 'benchmarks/action-policy-comparison-v1/measured.synthetic.json'


def replay(data):
    for key in ('independent_reference_acceptance', 'independent_generalization', 'validates_h93_or_development',
                'changes_compiler_or_reader'):
        shared.require(data[key] is False, 'Unsupported claim: '+key)
    shared.require(type(data['answers_per_primary_case']) is int and data['answers_per_primary_case'] == 8,
                   'Eight-answer endpoint differs')
    shared.require(type(data['fresh_generations_planned']) is int and data['fresh_generations_planned'] == 4,
                   'Producer count differs')
    shared.require(data['baseline_arm'] is True, 'Fresh baseline arm differs')
    shared.require(data['guidance_informed_by_prior_consumed_development_failures'] is True, 'Development adaptation disclosure differs')
    shared.require(data['disputed_rows'] == engine.plan.inputs()['disputed_rows'], 'Disputed mask or old annotation differs')
    shared.require(data['legacy_rows'] == engine.plan.inputs()['legacy_rows'], 'Legacy endpoint differs')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=engine.plan.METHODS, axis_name='method', record_fields=('method',))
    result.update(answers_per_primary_case=8, fresh_generations_planned=4,
        original_inventory_measured=232, original_inventory_remaining=0, new_original_inventory_coverage=0,
        independent_reference_acceptance=False, independent_generalization=False, baseline_arm=True, validates_h93_or_development=False)
    return result


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args(); print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
