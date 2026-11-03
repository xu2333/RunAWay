"""Replay the closed ambiguous-source27 repeat; no model service or new authority."""
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
engine = load('epistemic_archive_engine', ROOT / 'benchmarks/ambiguous-source-repeat-v1/engine.py')
INPUT_MANIFEST = '2d7cdd05e84e6601d152a427f71f552eb2b94450f2c41ce1a25a6a76d8874557'
KIND = 'actual_ambiguous_source_repeat27'
DEFAULT = ROOT / 'benchmarks/ambiguous-source-repeat-v1/measured.synthetic.json'


def replay(data):
    for key in ('independent_reference_acceptance', 'independent_generalization',
                'generation_stability_verified', 'new_scene_generalization_claim',
                'external_reader_decoder', 'hidden_generating_truth_resolves_unknown', 'token_matched_tail', 'optimal_tail_selection',
                'tail_has_json_metadata'):
        shared.require(data[key] is False, 'Unsupported claim: ' + key)
    for key in ('source_licensed_finite_inference', 'source_only_model_generated_annotation',
                'full_and_tail_transcript_layout_identical'):
        shared.require(data[key] is True, 'Missing boundary: ' + key)
    shared.require(data['design'] == engine.plan.inputs()['design'], 'Design drift')
    shared.require(type(data['answers_per_primary_case']) is int and data['answers_per_primary_case'] == 8,
                   'Eight-answer endpoint differs')
    shared.require(type(data['fresh_generations_planned']) is int and data['fresh_generations_planned'] == 8,
                   'Eight profile/method/generation producers differ')
    result = shared.replay(data, controller=engine, kind=KIND, input_manifest=INPUT_MANIFEST,
                           axes=(), record_fields=('method', 'view'))
    # The shared helper's old inventory progress is unrelated to this derivative.
    result.pop('original_inventory_measured', None)
    result.pop('original_inventory_remaining', None)
    parse = shared.parse_answer
    result.update(primary_cases_per_method_view=30, answers_per_primary_case=8,
                  planned_new_producers=8, generation_stability_verified=False,
                  fidelity_measured=any(r['kind']=='read' for r in data['records']),
                  new_original_inventory_coverage=0)
    result['returned_cards']=[{'profile':r['profile'],'method':r['method'],
        'generation':r['generation'],'characters':len(r['card']['prompt'])}
        for r in data['records'] if 'card' in r]
    decoded={(r['profile'],r['method'],r['generation'],r['view'],r['read_repeat']):parse(r['raw'])
             for r in data['records'] if r['kind']=='read' and r['state']=='completed'}
    losses=[]
    for method in engine.plan.METHODS:
        for view in ('card',):
            for row in engine.plan.inputs()['rows']:
                values=[[[decoded.get((row['person'],method,g,view,repeat),{}).get(q)
                          for q in row['query_ids']] for repeat in (0,1)] for g in (0,1)]
                flat=[v for generation in values for read in generation for v in read]
                if any(v!=row['gold'] for v in flat):
                    losses.append({'profile':row['person'],'method':method,'view':view,'case':row['case'],
                        'gold':row['gold'],'withdrawal_sensitive':row['guarantee_withdrawal_sensitive'],'derived_known':row['derived_known'],'missing':any(v is None for v in flat),'generations_reads_orders':values,'all_unknown_instead_of_known':row['gold']!='U' and all(v=='U'for v in flat),'observed_known_to_unknown_answers':sum(v=='U'for v in flat)if row['gold']!='U'else 0,'observed_false_certainty_answers':sum(v not in(None,'U')for v in flat)if row['gold']=='U'else 0})
    result['failed_or_missing_cases']=losses
    # Derived strata use the same frozen labels; they add no inference or independent samples.
    strata={}
    all_rows=engine.plan.inputs()['rows']
    subsets={'derived_known':[r for r in all_rows if r['derived_known']],
             'withdrawal_sensitive':[r for r in all_rows if r['guarantee_withdrawal_sensitive']],
             **{name:[r for r in all_rows if r['case'].startswith(name+'_')]for name in ('notes','signup','outside')}}
    for method in engine.plan.METHODS:
        strata[method]={}
        for label,subset in subsets.items():
            total={k:Counter()for k in engine.score.counts([], [{}])}
            for pid in engine.plan.PROFILES:
                own=[r for r in subset if r['person']==pid]
                answers=[decoded.get((pid,method,g,'card',repeat),{})for g in(0,1)for repeat in(0,1)]
                for k,value in engine.score.counts(own,answers).items():total[k].update(value)
            strata[method][label]={k:dict(v)for k,v in total.items()}
    result['derived_strata']=strata
    result['observed_error_decomposition']={method:{
        'known_cases_with_U':sum(v['method']==method and v['gold']!='U' and v['observed_known_to_unknown_answers']>0 for v in losses),
        'known_to_U_answers':sum(v['observed_known_to_unknown_answers']for v in losses if v['method']==method),
        'unknown_cases_with_choice':sum(v['method']==method and v['gold']=='U' and v['observed_false_certainty_answers']>0 for v in losses),
        'unknown_to_choice_answers':sum(v['observed_false_certainty_answers']for v in losses if v['method']==method)}
        for method in engine.plan.METHODS}
    baseline=[r for r in data['records']if r['kind']=='extract'and r['profile']=='c2v'and r['method']=='source-order-v3'and 'card'in r]
    result['c2v_baseline_generation_diagnostic']={
        'same_exact_request':len(baseline)==2 and baseline[0]['request']==baseline[1]['request'],
        'graph_sizes':[{'generation':r['generation'],'whole_characters':r['card']['characters'],
                        'objects':len(parse(r['raw'])['objects']),'nodes':len(parse(r['raw'])['nodes'])}for r in baseline],
        'metadata_incidence_is_not_a_semantic_coverage_certificate':True,
        'diagnostic_did_not_modify_card_or_reference':True}
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
