"""Replay the new40world scope; keep original w14annotations unaccepted."""
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


shared = load('world_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('world_archive_controller', ROOT / 'benchmarks/remaining-world-frontier-v1/engine.py')
INPUT_MANIFEST = '5efb146ece71a5a43993fd4ea97556f3ec86af90b7b136cee35df18c6bb79bd1'
DEFAULT = ROOT / 'benchmarks/remaining-world-frontier-v1/measured.synthetic.json'


def replay(data):
    inputs = engine.plan.inputs()
    shared.require(data['w14_reference_accepted'] is False, 'New w14 acceptance is unsupported')
    shared.require(data['independent_semantic_acceptance'] is False, 'Independent semantic claim is unsupported')
    shared.require(data['legacy_reference_rows'] == inputs['legacy_rows'], 'Legacy labels changed')
    shared.require(data['disputed_reference_rows'] == inputs['disputed_rows'], 'Predeclared mask changed')
    result = shared.replay(data, controller=engine, kind='actual_remaining_world_frontier40', input_manifest=INPUT_MANIFEST)
    before = {'measured': result.pop('original_inventory_measured'), 'remaining': result.pop('original_inventory_remaining')}
    return {**result, 'primary_cases_per_budget': 69, 'legacy_cases_retained': 72,
            'unscored_disputed_cases': 3, 'w14_reference_accepted': False,
            'inventory_before_study': before, 'current_inventory_computed_by_separate_binding_replay': True}


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
