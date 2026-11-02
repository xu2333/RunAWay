"""Replay closed long-task52 evidence; no service backend or new authority."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


shared = load('long_task_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('long_task_archive_engine', ROOT / 'benchmarks/long-task-probe-v1/engine.py')
INPUT_MANIFEST = 'ef4330f1eba4098383099e1b3a25e34b6effba2e194db55e2926890da07482b2'
KIND = 'actual_long_task_length_stress52'
DEFAULT = ROOT / 'benchmarks/long-task-probe-v1/measured.synthetic.json'


def replay(data):
    for key in ('independent_reference_acceptance', 'independent_generalization',
                'generation_stability_verified', 'new_scene_generalization_claim',
                'pair_rescoring_independent', 'token_matched_tail', 'optimal_tail_selection',
                'encoder_changed_for_new_sources', 'tail_has_json_metadata'):
        shared.require(data[key] is False, 'Unsupported claim: ' + key)
    for key in ('controlled_length_derivative', 'source_only_model_generated_annotation',
                'full_and_tail_transcript_layout_identical'):
        shared.require(data[key] is True, 'Missing boundary: ' + key)
    shared.require(data['design'] == engine.plan.inputs()['design'], 'Design drift')
    shared.require(type(data['answers_per_primary_case']) is int and data['answers_per_primary_case'] == 4,
                   'Four-answer endpoint differs')
    shared.require(type(data['fresh_generations_planned']) is int and data['fresh_generations_planned'] == 8,
                   'One producer per each of eight people differs')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=(), record_fields=('method', 'view'))
    # The shared helper's old inventory progress is unrelated to this derivative.
    result.pop('original_inventory_measured', None)
    result.pop('original_inventory_remaining', None)
    parse = shared.parse_answer
    decoded = {(r['profile'], r['view'], r['read_repeat']): parse(r['raw'])
               for r in data['records'] if r['kind'] == 'read' and r['state'] == 'completed'}
    losses = []
    for view in ('card', 'tail'):
        for row in engine.plan.inputs()['rows']:
            values = [[decoded.get((row['person'], view, repeat), {}).get(q)
                       for q in row['query_ids']] for repeat in (0, 1)]
            flat = [v for read in values for v in read]
            if any(v != row['gold'] for v in flat):
                losses.append({'profile': row['person'], 'view': view, 'case': row['case'],
                               'task': row['task'], 'gold': row['gold'],
                               'missing': any(v is None for v in flat), 'reads_orders': values})
    result.update(failed_or_missing_cases=losses, primary_cases_per_view=40,
                  answers_per_primary_case=4, planned_new_producers=8,
                  independent_generalization=False, independent_reference_acceptance=False,
                  generation_stability_verified=False, new_scene_generalization_claim=False,
                  pair_rescoring_independent=False, source_is_controlled_length_derivative=True,
                  new_original_inventory_coverage=0, length_stress_person_cases=40)
    stages = {}
    for record in data['records']:
        key = record['kind'] if record['kind'] != 'read' else record['view'] + '_read'
        stage = stages.setdefault(key, Counter())
        stage['attempts'] += 1
        stage['missing_usage_records'] += record['usage'] is None
        if record['usage'] is not None:
            stage.update(record['usage'])
    result['reported_usage_by_stage'] = {k: dict(v) for k, v in stages.items()}
    return result


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(),
                   'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
