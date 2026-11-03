"""Replay closed source-licensed49 evidence; no service backend or new authority."""
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


shared = load('epistemic_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('epistemic_archive_engine', ROOT / 'benchmarks/epistemic-transfer-v1/engine.py')
INPUT_MANIFEST = '933dc6da2b3fc1f99331166d43206271c5f27ba2755e794e1db8c55dafd9affb'
KIND = 'actual_epistemic_transfer49'
DEFAULT = ROOT / 'benchmarks/epistemic-transfer-v1/measured.synthetic.json'


def replay(data):
    for key in ('independent_reference_acceptance', 'independent_generalization',
                'generation_stability_verified', 'new_scene_generalization_claim',
                'external_reader_decoder', 'hidden_generating_truth_resolves_unknown', 'token_matched_tail', 'optimal_tail_selection',
                'encoder_changed_for_new_sources', 'tail_has_json_metadata'):
        shared.require(data[key] is False, 'Unsupported claim: ' + key)
    for key in ('source_licensed_finite_inference', 'source_only_model_generated_annotation',
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
                               'cohort': row['cohort'], 'derived_known': row['derived_known'],
                               'withdrawal_sensitive': row['guarantee_withdrawal_sensitive'], 'gold': row['gold'],
                               'missing': any(v is None for v in flat), 'reads_orders': values})
    result.update(failed_or_missing_cases=losses, primary_cases_per_view=120,
                  answers_per_primary_case=4, planned_new_producers=8,
                  independent_generalization=False, independent_reference_acceptance=False,
                  generation_stability_verified=False, new_scene_generalization_claim=False,
                  external_reader_decoder=False, hidden_generating_truth_resolves_unknown=False,
                  source_licensed_finite_inference=True,
                  new_original_inventory_coverage=0, finite_transfer_person_cases=120)
    controls = []
    rows = engine.plan.inputs()['rows']
    for record in data['records']:
        if record['kind'] != 'full' or record['state'] != 'completed':
            continue
        answer = parse(record['raw'])
        for row in rows:
            if row['person'] != record['profile']:
                continue
            values = [answer.get(q) for q in row['query_ids']]
            if any(v != row['gold'] for v in values):
                controls.append({'profile': row['person'], 'case': row['case'],
                    'cohort': row['cohort'], 'gold': row['gold'], 'both_orders': values,
                    'derived_known': row['derived_known'],
                    'withdrawal_sensitive': row['guarantee_withdrawal_sensitive']})
    result['full_control_failed_or_missing_cases'] = controls
    for kind, label in (('full', 'full_control_strict'), ('none', 'no_memory_strict_reused')):
        answers = {r['profile']: parse(r['raw']) for r in data['records']
                   if r['kind'] == kind and r['state'] == 'completed'}
        totals = {k: Counter() for k in ('joint', 'known', 'unknown', 'personal_known', 'derived_known')}
        for pid in engine.plan.PROFILES:
            own = [r for r in rows if r['person'] == pid]
            answer = answers.get(pid if kind == 'full' else 'shared_all', {})
            counted = engine.score.counts(own, [answer])
            for key in ('joint', 'known', 'unknown', 'personal_known'):
                totals[key].update(counted[key])
            totals['derived_known'].update(engine.score.counts(
                [r for r in own if r['derived_known']], [answer])['joint'])
        result[label] = {k: dict(v) for k, v in totals.items()}
    result['control_answers_per_case'] = 2
    result['no_memory_reuse_is_independent'] = False
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
