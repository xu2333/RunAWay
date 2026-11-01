"""Prepare an unapproved14attempt capacity/fidelity probe on consumed h93."""
import argparse
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import importlib.util


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


old = load('table_probe_original', HERE.parent / 'owned-conditions-v1/plan.py')
candidate = load('table_probe_candidate', HERE.parent / 'owned-object-table-v1/candidate.py')
baseline, choice_reader, grouped_support = old.baseline, old.choice_reader, old.grouped_support
read, sha, digest = old.read, old.sha, old.digest
PROFILES, METHODS = ('h93',), ('scope-v1', 'table-v1')
MODEL, AS_OF, CAP, BUDGET = old.MODEL, old.AS_OF, 14, 1536


def inputs():
    data = old.inputs()
    rows = [r for r in data['rows'] if r['person'] == 'h93']
    return {'sources': {'h93': data['sources']['h93']}, 'queries': {'h': data['queries']['h']},
            'rows': rows, 'legacy_rows': rows, 'disputed_rows': []}


def cells():
    return [('h93', m, g) for g in (0, 1) for m in (METHODS if g == 0 else reversed(METHODS))]


def slots():
    jobs = [('none', 'shared_h', None, None, None), ('full', 'h93', None, None, None)]
    jobs += [('extract', p, m, g, None) for p, m, g in cells()]
    for repeat in (0, 1):
        jobs += [('read', p, m, g, repeat) for p, m, g in (cells() if repeat == 0 else reversed(cells()))]
    return [{'slot': i+1, 'kind': k, 'profile': p, 'method': m, 'generation': g, 'read_repeat': r,
             'budget': BUDGET if m else None, 'key': ':'.join(map(str, (k, p, m, g, r)))}
            for i, (k, p, m, g, r) in enumerate(jobs)]


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def bank(pid):
    if pid not in ('h93', 'shared_h'):
        raise ValueError('Foreign source')
    return 'h'


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract':
        raise ValueError('Only own extraction binds')
    old.check(answer, request(slot)['schema'])
    return (baseline if slot['method'] == 'scope-v1' else candidate).bind(answer, inputs()['sources']['h93'], BUDGET)


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside fixed14slot schedule')
    data, kind = inputs(), slot['kind']
    if kind == 'extract':
        req = baseline.make_request(data['sources']['h93'], BUDGET) if slot['method'] == 'scope-v1' else candidate.make_request(data['sources']['h93'])
        return {'model': MODEL, 'system': grouped_support.SYSTEM, **req}
    if kind == 'none':
        material = ''
    elif kind == 'full':
        material = old.canonical(data['sources']['h93'])
    else:
        key = parent(slot)
        if parents is None or key not in parents:
            return None
        extraction = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == key)
        material = bind(extraction, parents[key])['prompt.md']
    req = choice_reader.make_request(material, data['queries']['h'], as_of=AS_OF, answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped_support.SYSTEM, **req, 'prompt': old.COMMON + req['prompt']}


def implementation():
    files = old.implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'owned-object-table-v1/candidate.py', ROOT / 'scripts/finite_method_controller.py']
    files.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    return dict(sorted(files.items()))


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    proposal = {'kind': 'unapproved_object_table14_consumed_h93_probe', 'requested_model': MODEL,
        'as_of': AS_OF, 'max_new_local_cli_attempts': CAP, 'source_messages': 48, 'public_question_forms': 80,
        'primary_cases': 40, 'known_cases': 24, 'unknown_cases': 16, 'personal_known_cases': 14,
        'stages': {'controls': 2, 'source_only_extractions': 4, 'bound_reads': 8},
        'methods': list(METHODS), 'whole_character_budget': BUDGET, 'generations_per_method': 2, 'reads_per_card': 2,
        'control': 'Full immediately all40cases,bothorders,no missing;personal-known>own no-memory. Failure stops before extract3.',
        'primary': 'Per method40fixed cases,each needs2generations*2reads*2orders correct;retain missing,known,unknown,personal-known and paired outcomes. No valid-card-only replacement endpoint.',
        'method': 'Fresh unchanged scope-v1 versus source-only unbudgeted object-table candidate. Same1536public-character cap and reader. Capacity alignment only;does not fix or test j16/w11.',
        'all_extractions_before_any_read': True, 'old_model_outputs_cards_or_feedback_sent': False,
        'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
        'max_nominal_timeout_sum_seconds': 2520, 'not_a_spend_or_total_duration_cap': True,
        'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
        'fatal': 'Control,transport,wire,decode,unknownusage,model,runtime,hash or ownedguard failure closes remainder. Intent counts;unused expire.',
        'invalid_product': 'Skip only own profile+method+generation two readers;no truncation,replacement or borrowing.',
        'consumed_development': True, 'independent_holdout': False, 'new_original_inventory_coverage': 0,
        'real_person_fidelity_verified': False, 'approved': False, 'new_service_authority': False, 'production_default_changed': False}
    values = {'proposal.json': proposal, 'slots.json': slots(), 'sources.json': data['sources'],
        'queries.public.json': data['queries'], 'reference.consumed-development.private.json': {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')},
        'static-requests.json': {s['key']: request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
            'builder': 'benchmarks/object-table-probe-v1/plan.py:request', 'parent': 'Exact source+method+generation;two identical reads of its validated bound prompt'},
        'implementation-sha256.json': implementation()}
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2) + '\n')
    return proposal


def verify(root, *, reconstruct=True):
    for rel, expected in read(root / 'manifest.json')['files'].items():
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or (root / p).is_symlink() or sha(root / p) != expected:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation drift')
    if reconstruct:
        data = inputs()
        for name, expected in [('slots.json', slots()), ('sources.json', data['sources']), ('queries.public.json', data['queries']),
            ('reference.consumed-development.private.json', {k: data[k] for k in ('rows', 'legacy_rows', 'disputed_rows')}),
            ('static-requests.json', {s['key']: request(s) for s in slots() if s['kind'] != 'read'})]:
            if read(root / name) != expected:
                raise ValueError('Reconstructed input drift')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
