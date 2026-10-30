"""Prepare an unapproved finite model comparison; never invoke a backend."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway.card import canonical
from runaway import choice_reader, grouped_support as grouped
spec = importlib.util.spec_from_file_location('target_experiment_check', HERE / 'check.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)

MODEL = 'gpt-6.1-sol'
AS_OF = '2026-10-30'
CAP = 21
BUDGET = 1536
COMMON = '仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def inputs():
    old = checks.read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']['remaining_h']
    packet = checks.validate(checks.read(HERE / 'development.synthetic.json'))
    sources = {pid: old['sources'][pid] for pid in ['h68', 'h93']}
    sources['dev'] = packet['sources']
    cached = {rec['person']: rec['card'] for rec in old['records'] if rec['group'] == 'extract' and rec['person'] in ['h68', 'h93']}
    toy_queries, toy_rows = [], []
    for query in packet['queries']:
        a = copy.deepcopy(query['public'])
        a['id'] += '_a'
        b = copy.deepcopy(a)
        b['id'] = b['id'][:-1] + 'b'
        values = list(a['options'].values())
        b['options'] = dict(zip(['A', 'B'], reversed(values)))
        toy_queries += [a, b]
        toy_rows.append({'person': 'dev', 'case': query['public']['id'], 'query_ids': [a['id'], b['id']],
                         'gold': query['expected'], 'stratum': query['stratum'], 'personal_known': False})
    rows = [row for row in old['reference_rows'] if row['person'] in ['h68', 'h93']] + toy_rows
    return {'sources': sources, 'queries': {'h': old['queries'], 'dev': toy_queries},
            'rows': rows, 'cached_v1': cached}


def slots():
    entries = [('none', 'shared_h', None, None), ('full', 'h68', None, None),
               ('full', 'h93', None, None), ('none', 'shared_dev', None, None), ('full', 'dev', None, None)]
    for repeat, order in [(0, ['h68', 'h93']), (1, ['h93', 'h68'])]:
        entries += [('cached_read', pid, 'v1', repeat) for pid in order]
    entries += [('extract', 'h68', 'v2', None), ('extract', 'h93', 'v2', None),
                ('extract', 'dev', 'v1', None), ('extract', 'dev', 'v2', None)]
    entries += [('read', 'h68', 'v2', 0), ('read', 'h93', 'v2', 0),
                ('read', 'dev', 'v1', 0), ('read', 'dev', 'v2', 0),
                ('read', 'dev', 'v2', 1), ('read', 'dev', 'v1', 1),
                ('read', 'h93', 'v2', 1), ('read', 'h68', 'v2', 1)]
    return [{'slot': i + 1, 'kind': kind, 'profile': pid, 'method': method, 'repeat': repeat,
             'key': ':'.join(str(v) for v in (kind, pid, method, repeat))}
            for i, (kind, pid, method, repeat) in enumerate(entries)]


def request(slot, answers=None):
    if slot not in slots():
        raise ValueError('Outside fixed21slot proposal')
    data = inputs()
    kind, pid, method = slot['kind'], slot['profile'], slot['method']
    if kind == 'extract':
        make = checks.candidate.make_request if method == 'v2' else checks.candidate.base.make_request
        return {'model': MODEL, 'system': grouped.SYSTEM, **make(data['sources'][pid], BUDGET)}
    queries = data['queries']['dev' if pid in ['dev', 'shared_dev'] else 'h']
    if kind == 'none':
        material = ''
    elif kind == 'full':
        material = canonical(data['sources'][pid])
    elif kind == 'cached_read':
        card = data['cached_v1'][pid]
        if card['source_sha256'] != digest(data['sources'][pid]) or card['characters'] != len(card['prompt']):
            raise ValueError('Cached v1 card/source mismatch')
        material = card['prompt']
    else:
        if answers is None or (pid, method) not in answers:
            return None
        extract_answer = answers[pid, method]
        extract_slot = next(s for s in slots() if s['kind'] == 'extract' and s['profile'] == pid and s['method'] == method)
        from runaway.constraint_extract import check
        check(extract_answer, request(extract_slot)['schema'])
        files = checks.candidate.bind(extract_answer, data['sources'][pid], BUDGET)
        material = files['prompt.md']
        if not 0 < len(material) <= BUDGET:
            raise ValueError('Whole card over1536cap')
    req = choice_reader.make_request(material, queries, as_of=AS_OF, answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped.SYSTEM, **req, 'prompt': COMMON + req['prompt']}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    data = inputs()
    static = {s['key']: request(s) for s in slots() if s['kind'] != 'read'}
    assert len(static) == 13 and len(slots()) == 21
    proposal = {
        'kind': 'unapproved_decision_target21_consumed_development_comparison',
        'max_new_local_cli_attempts': 21, 'requested_model': MODEL, 'as_of': AS_OF,
        'categories': {'none': 2, 'full': 3, 'extractions': 4, 'cached_v1_reads': 4, 'generated_reads': 8},
        'source_messages': 110, 'cases': 96, 'old_cases_repeated_not_new_coverage': 80,
        'new_authored_development_cases': 16, 'public_questions': {'h': 80, 'dev': 32},
        'known_private_truth_not_sent': True, 'whole_character_cap': BUDGET,
        'aggregate_token_cap': None, 'money_cap': None, 'timeout_per_local_child_seconds': 180,
        'max_nominal_timeout_sum_seconds': 3780, 'not_a_spend_or_total_duration_cap': True,
        'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
        'controls': 'Check each full immediately:all40oldor16dev cases,bothorders,no missing;h personal-known>shared_hnone;devknown>shared_devnone. Any failure closes remainder before any card read/extraction.',
        'invalid_product': 'Skip only the2readers bound to that profile/method;retain all96case denominators and missing repeats;no replacement,truncation or repair.',
        'fatal': 'Transport/schema/decode/unknownusage/requestedmodel/runtime/inputhash/ownedguard failure closes remaining scope;unused expire;no retry/resume.',
        'binding': 'Fixed13exactrequests;dynamic8mustderive only from their own one bound extraction answer. Bothreads identical per artifact. Preserve request/raw/usage/artifact hashes and source/method linkage.',
        'claims': 'Developer-visible repair diagnosis,not holdout,human fidelity,generation variance,causal improvement or new192/72coverage. H v1 cards are selected cached outputs;dev v1andv2 generated once each.',
        'upstream_rpc_retries_model_identity_or_cancellation_independently_observable': False,
        'approved': False, 'new_service_authority': False, 'production_default_changed': False,
    }
    implementation = [HERE / 'experiment.py', HERE / 'check.py', HERE / 'oracle.py', HERE / 'prototype/decision_targets.py',
                      ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py',
                      ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json', HERE / 'development.synthetic.json']
    implementation += sorted((ROOT / 'runaway').rglob('*.py'))
    values = {'proposal.json': proposal, 'slots.json': slots(), 'static-requests.json': static,
              'sources.json': data['sources'], 'queries.public.json': data['queries'],
              'reference.consumed-development.private.json': {'rows': data['rows']},
              'cached-v1-cards.json': data['cached_v1'],
              'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                                     'builder': 'benchmarks/decision-targets-v1/experiment.py:request',
                                     'card_parent': 'Only ownprofile+method extraction;unchanged schema/source binder/renderer;no reader feedback'},
              'implementation-sha256.json': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in implementation}}
    for filename, value in values.items():
        (out / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}
    (out / 'manifest.json').write_text(json.dumps({'files': manifest, 'new_model_calls': 0}, indent=2) + '\n')
    return proposal


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False))
