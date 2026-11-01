"""Replay the closed one-card graph pilot; no two-generation denominator."""
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


shared = load('graph_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('graph_archive_engine', ROOT / 'benchmarks/action-revision-pilot-v1/engine.py')
INPUT_MANIFEST = '114abbb009cd87c5f6526270c3d5731a26a6d5954a359cf4566976a0cdcfe28d'
KIND = 'actual_action_revision_graph5_h93_pilot'
DEFAULT = ROOT / 'benchmarks/action-revision-pilot-v1/measured.synthetic.json'


def replay(data):
    for name in ('fresh_generation_stability_test', 'independent_reference_acceptance', 'validates_j16_or_development'):
        shared.require(data[name] is False, 'Unsupported claim: '+name)
    shared.require(type(data['answers_per_case']) is int and data['answers_per_case'] == 4, 'Pilot answer denominator differs')
    shared.require(type(data['generated_cards_planned']) is int and data['generated_cards_planned'] == 1, 'Pilot producer count differs')
    # Shared archive machinery verifies every request/artifact/counter/controller
    # result. Its historical two-generation loss listing is deliberately disabled.
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=(), axis_name='method', record_fields=('method',))
    answers = {r['read_repeat']: shared.parse_answer(r['raw']) for r in data['records']
               if r['kind'] == 'read' and r['state'] == 'completed'}
    losses = []
    for row in engine.plan.inputs()['rows']:
        values = [[answers.get(repeat, {}).get(q) for q in row['query_ids']] for repeat in (0, 1)]
        flat = [v for read in values for v in read]
        if any(v != row['gold'] for v in flat):
            losses.append({'profile': row['person'], 'case': row['case'], 'gold': row['gold'],
                           'missing': any(v is None for v in flat), 'reads_orders': values})
    result.update(failed_or_missing_cases=losses, answers_per_case=4, generated_cards_planned=1,
        fresh_generation_stability_test=False, independent_reference_acceptance=False,
        validates_j16_or_development=False, original_inventory_measured=232,
        original_inventory_remaining=0, new_original_inventory_coverage=0)
    return result


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args(); print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
