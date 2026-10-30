"""Freeze a finite, unapproved compression/stability study; no backend calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway import choice_reader, grouped_support
from runaway.card import canonical
from runaway.constraint_extract import check
spec = importlib.util.spec_from_file_location('stability_previous_plan', ROOT / 'benchmarks/decision-targets-v1/experiment.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
policy = previous.checks.candidate.base
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-10-30', 41
PROFILES, BUDGETS = ('h68', 'h93', 'dev'), (768, 1024)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    data = previous.inputs()
    return {key: data[key] for key in ('sources', 'queries', 'rows')}


def cells():
    # Reverse budget order and rotate profile order in the second generation.
    result = []
    for generation in (0, 1):
        for index, budget in enumerate(BUDGETS if generation == 0 else reversed(BUDGETS)):
            people = list(PROFILES[index:] + PROFILES[:index])
            if generation:
                people.reverse()
            result += [(pid, budget, generation) for pid in people]
    return result


def slots():
    jobs = [('none', 'shared_h', None, None, None), ('full', 'h68', None, None, None),
            ('full', 'h93', None, None, None), ('none', 'shared_dev', None, None, None),
            ('full', 'dev', None, None, None)]
    jobs += [('extract', pid, budget, generation, None) for pid, budget, generation in cells()]
    for repeat in (0, 1):
        order = cells() if repeat == 0 else list(reversed(cells()))
        jobs += [('read', pid, budget, generation, repeat) for pid, budget, generation in order]
    return [{'slot': i+1, 'kind': kind, 'profile': pid, 'budget': budget,
             'generation': generation, 'read_repeat': repeat,
             'key': ':'.join(str(v) for v in (kind, pid, budget, generation, repeat))}
            for i, (kind, pid, budget, generation, repeat) in enumerate(jobs)]


def parent(slot):
    return slot['profile'], slot['budget'], slot['generation']


def bank(pid):
    return 'dev' if pid in ('dev', 'shared_dev') else 'h'


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen41slot schedule')
    data, kind, pid = inputs(), slot['kind'], slot['profile']
    if kind == 'extract':
        return {'model': MODEL, 'system': grouped_support.SYSTEM,
                **policy.make_request(data['sources'][pid], slot['budget'])}
    if kind == 'none':
        material = ''
    elif kind == 'full':
        material = canonical(data['sources'][pid])
    else:
        key = parent(slot)
        if parents is None or key not in parents:
            return None
        answer = parents[key]
        extraction = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == key)
        check(answer, request(extraction)['schema'])
        material = policy.bind(answer, data['sources'][pid], slot['budget'])['prompt.md']
        if not 0 < len(material) <= slot['budget']:
            raise ValueError('Whole-card budget exceeded')
    req = choice_reader.make_request(material, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped_support.SYSTEM, **req, 'prompt': previous.COMMON + req['prompt']}


def implementation():
    paths = list(HERE.glob('*.py')) + [ROOT / 'benchmarks/decision-targets-v1/experiment.py',
             ROOT / 'benchmarks/decision-targets-v1/check.py', ROOT / 'benchmarks/decision-targets-v1/oracle.py',
             ROOT / 'benchmarks/decision-targets-v1/prototype/decision_targets.py',
             ROOT / 'benchmarks/decision-targets-v1/development.synthetic.json',
             ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py',
             ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json']
    paths += list((ROOT / 'runaway').rglob('*.py'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    proposal = {'kind': 'unapproved_scope_v1_compression_stability41', 'requested_model': MODEL,
                'as_of': AS_OF, 'max_new_local_cli_attempts': CAP,
                'stages': {'controls': 5, 'source_only_extractions': 12, 'bound_reads': 24},
                'budgets_whole_characters': list(BUDGETS), 'generations_per_source_budget': 2,
                'reads_per_artifact': 2, 'option_orders_per_case': 2,
                'source_messages': 110, 'profile_cases': 96, 'known_cases': 54, 'unknown_cases': 42,
                'development_execution_cases': 5, 'distinct_public_questions': 112,
                'independent_people_or_heldout_cases': False, 'new_original_inventory_coverage': 0,
                'old_inventory_measured': 160, 'old_inventory_remaining': 72,
                'method': 'Frozen policy-scope-instructions-v1;no target-v2 delta,cached cards,feedback or default switch',
                'generation_design': 'All12extractions precede every read;each uses own source and budget only. Two generations share exact request text but use fresh contexts. Seeds/upstream sampling and independence are unobservable.',
                'primary_endpoint': 'Perbudget,all2generations*2reads*2orders correct percase;96fixed cases. Report each artifact/read plus known,unknown,personal-known,devpreference,devexecution and untyped old cases. Invalid/missing generations stay missing;no best-of.',
                'controls': 'Check each full immediately:all40h or16dev cases,bothorders,no missing;h personal-known>shared_hnone;devknown>shared_devnone. Any failure closes entire remainder.',
                'invalid_product': 'Skip only the2reads of the exact profile+budget+generation;retain96case denominator at each budget. No repair,replacement,truncation or borrowing another generation.',
                'fatal': 'Transport,wire schema,decode,unknown usage,requested model,runtime,input hash or owned guard failure closes remainder. Attempt intents count even if upstream receipt unknown.',
                'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
                'max_nominal_timeout_sum_seconds': 7380, 'not_spend_or_total_duration_cap': True,
                'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
                'dev_is_short_source_boundary_control_not_guaranteed_binding_compression': True,
                'same_model_consumed_development_not_real_person_fidelity': True,
                'independent_semantic_acceptance': False, 'causal_variance_decomposition': False,
                'approved': False, 'new_service_authority': False, 'production_default_changed': False}
    static = {s['key']: request(s) for s in slots() if s['kind'] != 'read'}
    values = {'proposal.json': proposal, 'slots.json': slots(), 'sources.json': data['sources'],
              'queries.public.json': data['queries'], 'reference.consumed-development.private.json': {'rows': data['rows']},
              'static-requests.json': static, 'implementation-sha256.json': implementation(),
              'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                'builder': 'benchmarks/compression-stability-v1/plan.py:request',
                'parent': 'Only exact profile+budget+generation;original schema/source binder/renderer;both read requests identical'}}
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {name: sha(out / name) for name in sorted(values)},
                                                'new_model_calls': 0}, indent=2) + '\n')
    return proposal


def verify(root, *, reconstruct=True):
    for rel, expected in read(root / 'manifest.json')['files'].items():
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or sha(root / path) != expected:
            raise ValueError('Frozen input differs')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation differs')
    if not reconstruct:
        return True
    data = inputs()
    if (read(root / 'slots.json') != slots() or read(root / 'sources.json') != data['sources']
            or read(root / 'queries.public.json') != data['queries']
            or read(root / 'reference.consumed-development.private.json') != {'rows': data['rows']}):
        raise ValueError('Source/query/reference/slot differs')
    expected = {s['key']: request(s) for s in slots() if s['kind'] != 'read'}
    if read(root / 'static-requests.json') != expected:
        raise ValueError('Static request reconstruction differs')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
