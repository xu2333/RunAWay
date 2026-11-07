"""Unapproved51-attempt binding/late-revision stress design; no service backend."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'benchmarks/scope-binding-stress-v1'
FILES = {'proposal.json', 'sources.json', 'queries.public.json', 'reference.private.json',
         'author-evidence.private.json', 'calibration.private.json', 'slots.json',
         'static-requests.json', 'dynamic-rules.json', 'implementation-sha256.json'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


seed = load('binding_seed', HERE.parent / 'source-accounted-encoding-v1/plan.py')
corpus = load('binding_corpus', HERE / 'corpus.py')
read, sha, digest, transcript, choice_reader = seed.read, seed.sha, seed.digest, seed.transcript, seed.choice_reader
PROFILES, METHODS, BUDGETS = corpus.PROFILES, seed.METHODS, (768, 1536)
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-11-07', 51
factory = seed.factory


def inputs():
    return corpus.build()


def bank(pid):
    if pid not in PROFILES + ('shared_all',):
        raise ValueError('Foreign person/bank')
    return 'all'


def parent(slot):
    return slot['profile'], slot['method'], slot['budget'], slot['generation']


def slots():
    jobs = [('none', 'shared_all', None, None, None, None, None)]
    jobs += [('full', person, None, None, None, None, None) for person in PROFILES]
    for generation in (0, 1):
        budgets = tuple(reversed(BUDGETS)) if generation == 0 else BUDGETS
        for bi, budget in enumerate(budgets):
            for pi, person in enumerate(PROFILES):
                methods = METHODS if (pi + generation + bi) % 2 == 0 else tuple(reversed(METHODS))
                for method in methods:
                    jobs.append(('extract', person, method, budget, generation, None, None))
                    jobs.extend(('read', person, method, budget, generation, repeat, 'card') for repeat in (0, 1))
    return [dict(slot=i + 1, kind=kind, profile=person, method=method, budget=budget,
                 generation=generation, read_repeat=repeat, view=view,
                 key=':'.join(map(str, (kind, person, method, budget, generation, repeat, view))))
            for i, (kind, person, method, budget, generation, repeat, view) in enumerate(jobs)]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract':
        raise ValueError('Only planned own extraction may bind')
    return factory(slot['method']).bind(answer, inputs()['sources'][slot['profile']], slot['budget'])


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen51schedule')
    data, pid = inputs(), slot['profile']
    system = seed.base.base.old.old.grouped_support.SYSTEM
    if slot['kind'] == 'extract':
        return {'model': MODEL, 'system': system,
                **factory(slot['method']).make_request(data['sources'][pid], slot['budget'])}
    if slot['kind'] == 'none':
        text = ''
    elif slot['kind'] == 'full':
        text = transcript(data['sources'][pid])
    else:
        if parent(slot) not in (parents or {}):
            return None
        source_slot = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == parent(slot))
        text = bind(source_slot, parents[parent(slot)])['prompt.md']
    req = choice_reader.make_request(text, data['queries']['all'], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': system, **req,
            'prompt': seed.base.base.old.old.COMMON + req['prompt']}


def implementation():
    files = seed.implementation()
    files.update({PREFIX + '/' + p.name: sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = {
        'kind': 'unapproved_scope_binding_stress51', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 3, 'independent_extractions': 16, 'card_reads': 32},
        **data['design'], 'methods': list(METHODS), 'whole_public_budgets': list(BUDGETS),
        'generations_per_person_method_budget': 2, 'reads_per_parent': 2, 'orders_per_read': 2,
        'answers_per_joint_case': 8,
        'encoder': 'Unmodified current coverage and source-accounted methods from PR79. Own48messages,budget,fixed instructions/schema only. No questions,reference,author bits/mappings/HAND table,case evidence,old card/graph,response/score,manual classification or another generation.',
        'reader': 'Original standard reader/prefix;own complete public card and common64public forms only. No source supplement,alias decoder,reference or bookkeeping.',
        'control': 'Shared none then both own full32/32bothorders,no missing and personal-known gain,before any extraction. Failure closes all remaining slots,not compression loss.',
        'endpoint': 'Every method/budget retains64person/cases:40known,24unknown. All2generations x2reads x2orders correct. Report8cohorts,old-alias16,late-revision16 and execution8 separately. Same cases across budgets/methods,not256independent cases.',
        'invalid': 'Binding/ownership/witness/budget invalid product skips only own2reads;its32cases remain missing in64case method/budget denominator. No truncation,repair or replacement.',
        'fatal': 'Any control,transport,structural schema/decode,unknownusage,model,input/runtime or ownedguard failure closes all remainder. No retry,repair,resume,replenishment or closed-budget reuse.',
        'loss_localization': 'For valid failed cards,inspect original source links,raw graph and public text for alias binding,latest local revision,global prerequisite and actual-fact separation. Repeated-read disagreement is distinguished from omitted information. Do not change this frozen round after seeing failures.',
        'calibration': 'Six deliberately damaged author calculators verify task sensitivity;their reference-aware outputs are fixture evidence,not model results or independent semantics.',
        'new_fictional_sources': True, 'methods_unchanged': True,
        'measured_results_available': False, 'real_person_fidelity_verified': False,
        'source_reference_semantics_verified': False, 'cross_provider_verified': False,
        'population_stability_verified': False, 'production_default_changed': False,
        'old_observations_replaced': False, 'old_scopes_reopened': False,
        'aggregate_token_cap': None, 'money_cap': None, 'local_child_timeout_seconds': 180,
        'approved': False, 'new_service_authority': False,
        'execution_condition': 'Fresh direct finite51grant and all three exact published implementation CI jobs successful.'}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
            'reference.private.json': data['rows'], 'author-evidence.private.json': data['author_evidence'],
            'calibration.private.json': corpus.damage_summary(), 'slots.json': slots(),
            'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
            'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                                   'builder': PREFIX + '/plan.py:request', 'only_own_valid_person_method_budget_generation': True},
            'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination)
    contents = values()
    destination.mkdir(exist_ok=False)
    for name, value in contents.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(
        {'files': {name: sha(destination / name) for name in sorted(contents)}, 'new_model_calls': 0}, indent=2) + '\n')
    return contents['proposal.json']


def verify(root, *, reconstruct=True):
    root = Path(root)
    if root.is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('Prepared symlinks refused')
    manifest = read(root / 'manifest.json')
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Invalid preparation manifest')
    if set(manifest['files']) != FILES or {p.name for p in root.iterdir()} != FILES | {'manifest.json'}:
        raise ValueError('Changed prepared file set')
    for name, fingerprint in manifest['files'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or sha(path) != fingerprint:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Implementation drift')
    if reconstruct:
        expected = values()
        if any(digest(read(root / name)) != digest(value) for name, value in expected.items()):
            raise ValueError('Reconstruction differs')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
