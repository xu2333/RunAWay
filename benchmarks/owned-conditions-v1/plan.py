"""Prepare a source-only ledger versus scope-v1 comparison; no backend."""
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


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


candidate = load('owned_plan_candidate', HERE / 'candidate.py')
baseline = load('owned_plan_baseline', ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py')
old_inputs = load('owned_plan_source_builder', ROOT / 'benchmarks/decision-targets-v1/experiment.py')
PROFILES, METHODS = ('h93', 'j16', 'dev'), ('scope-v1', 'owned-v1')
MODEL, AS_OF, CAP, BUDGET = 'gpt-6.1-sol', '2026-10-30', 42, 1536
COMMON = old_inputs.COMMON


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def inputs():
    h = old_inputs.inputs()
    j = read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']['new_worlds']
    legacy = [r for r in h['rows'] if r['person'] in ('h93', 'dev')]
    legacy += [r for r in j['reference_rows'] if r['person'] == 'j16']
    return {'sources': {'h93': h['sources']['h93'], 'j16': j['sources']['j16'], 'dev': h['sources']['dev']},
            'queries': {'h': h['queries']['h'], 'j': j['queries'], 'dev': h['queries']['dev']},
            'rows': [r for r in legacy if not (r['person'] == 'j16' and r['case'] == 'w14')],
            'disputed_rows': [r for r in legacy if r['person'] == 'j16' and r['case'] == 'w14'],
            'legacy_rows': legacy}


def cells():
    result = []
    for generation in (0, 1):
        for i, method in enumerate(METHODS if generation == 0 else reversed(METHODS)):
            people = list(PROFILES[i:] + PROFILES[:i])
            if generation:
                people.reverse()
            result += [(pid, method, generation) for pid in people]
    return result


def slots():
    jobs = []
    for pid in PROFILES:
        jobs += [('none', 'shared_' + bank(pid), None, None, None), ('full', pid, None, None, None)]
    jobs += [('extract', pid, method, generation, None) for pid, method, generation in cells()]
    for repeat in (0, 1):
        order = cells() if repeat == 0 else list(reversed(cells()))
        jobs += [('read', pid, method, generation, repeat) for pid, method, generation in order]
    return [{'slot': i+1, 'kind': kind, 'profile': pid, 'method': method, 'budget': BUDGET if method else None,
             'generation': generation, 'read_repeat': repeat,
             'key': ':'.join(str(v) for v in (kind, pid, method, generation, repeat))}
            for i, (kind, pid, method, generation, repeat) in enumerate(jobs)]


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def bank(pid):
    mapping = {'h93': 'h', 'j16': 'j', 'dev': 'dev', 'shared_h': 'h', 'shared_j': 'j', 'shared_dev': 'dev'}
    if pid not in mapping:
        raise ValueError('Foreign profile')
    return mapping[pid]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract':
        raise ValueError('Only own extraction may bind a card')
    check(answer, request(slot)['schema'])
    binder = baseline.bind if slot['method'] == 'scope-v1' else candidate.bind
    return binder(answer, inputs()['sources'][slot['profile']], slot['budget'])


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen42slot schedule')
    data, pid, kind = inputs(), slot['profile'], slot['kind']
    if kind == 'extract':
        req = baseline.make_request(data['sources'][pid], BUDGET) if slot['method'] == 'scope-v1' else candidate.make_request(data['sources'][pid])
        return {'model': MODEL, 'system': grouped_support.SYSTEM, **req}
    if kind == 'none':
        material = ''
    elif kind == 'full':
        material = canonical(data['sources'][pid])
    else:
        key = parent(slot)
        if parents is None or key not in parents:
            return None
        extraction = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == key)
        material = bind(extraction, parents[key])['prompt.md']
        if not 0 < len(material) <= BUDGET:
            raise ValueError('Whole-card cap exceeded')
    req = choice_reader.make_request(material, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped_support.SYSTEM, **req, 'prompt': COMMON + req['prompt']}


def implementation():
    files = list(HERE.glob('*.py')) + list((ROOT / 'runaway').rglob('*.py'))
    files += [ROOT / p for p in ('benchmarks/regression-progress-v1/prototype/policy_scope.py',
        'benchmarks/regression-progress-v1/observed.synthetic.json', 'benchmarks/compression-stability-v1/score.py',
        'benchmarks/decision-targets-v1/experiment.py', 'benchmarks/decision-targets-v1/check.py',
        'benchmarks/decision-targets-v1/oracle.py', 'benchmarks/decision-targets-v1/development.synthetic.json',
        'benchmarks/decision-targets-v1/prototype/decision_targets.py')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(files))}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    proposal = {'kind': 'unapproved_owned_conditions42_consumed_development', 'requested_model': MODEL,
        'as_of': AS_OF, 'max_new_local_cli_attempts': CAP,
        'stages': {'controls': 6, 'source_only_extractions': 12, 'bound_reads': 24},
        'whole_character_budget': BUDGET, 'methods': list(METHODS), 'generations_per_source_method': 2, 'reads_per_card': 2,
        'source_messages': 96, 'distinct_public_question_forms': 160,
        'legacy_cases': 80, 'primary_unflagged_author_cases': 79, 'unscored_disputed_cases': 1,
        'controls': 'Each full immediately:all40h93/23j16/16dev primary cases,bothorders,no missing. H/J personal-known>own-banknone;devknown>devnone. All3fulls must qualify before any extraction;w14unscored.',
        'primary': 'Per method,all79fixed cases;each needs both generations*both reads*both orders correct. Missing invalid generations cannot be credited by other successful reads. Report known/unknown/personal-known/preference/execution.',
        'methods_are_bundled': 'Fresh unchanged scope-v1 versus source-only unbudgeted owned-condition ledger plus conservative factoring compiler. Shared original renderer,codec,1536public-character cap and reader;no component-specific causal claim.',
        'ownership_proof_limit': 'Factoring preserves explicit predicate sets only. Source entailment,completeness and annotation truth are unverified.',
        'invalid_product': 'Skip only its own profile+method+generation two readers;no replacement,repair,truncation,retry or feedback. Wire/schema/decode failures are fatal,not invalid-product skips.',
        'fatal': 'Any failed control,transport,wire,decode,unknownusage,model,runtime,inputhash or ownedguard closes remainder;intent counts even if upstream receipt unknown;unused expire.',
        'disputed_policy': 'Keep original j16/w14annotation and question;freeze exclusion before outputs;record vectors only,no new gold acceptance or pass/fail.',
        'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
        'max_nominal_timeout_sum_seconds': 7560, 'not_a_spend_or_total_duration_cap': True,
        'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
        'all_extractions_before_any_read': True, 'old_cards_responses_or_feedback_sent': False,
        'independent_holdout': False, 'new_original_inventory_coverage': 0,
        'real_person_fidelity_verified': False, 'approved': False, 'new_service_authority': False,
        'production_default_changed': False}
    values = {'proposal.json': proposal, 'slots.json': slots(), 'sources.json': data['sources'],
        'queries.public.json': data['queries'],
        'reference.consumed-development.private.json': {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')},
        'static-requests.json': {s['key']: request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
            'builder': 'benchmarks/owned-conditions-v1/plan.py:request',
            'parent': 'Exact profile+method+generation;slot-specific schema,source quotes and binder validated;two identical reads'},
        'implementation-sha256.json': implementation()}
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {name: sha(out / name) for name in sorted(values)}, 'new_model_calls': 0}, indent=2) + '\n')
    return proposal


def verify(root, *, reconstruct=True):
    for rel, expected in read(root / 'manifest.json')['files'].items():
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or sha(root / path) != expected:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation drift')
    if reconstruct:
        data = inputs()
        for name, expected in [('sources.json', data['sources']), ('queries.public.json', data['queries']),
            ('slots.json', slots()), ('reference.consumed-development.private.json', {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')}),
            ('static-requests.json', {s['key']: request(s) for s in slots() if s['kind'] != 'read'})]:
            if read(root / name) != expected:
                raise ValueError('Reconstructed input drift')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
