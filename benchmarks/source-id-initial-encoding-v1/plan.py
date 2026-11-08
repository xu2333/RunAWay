"""Unapproved28-attempt initial source-ID comparison; no service backend."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'benchmarks/source-id-initial-encoding-v1'
FILES = {'proposal.json', 'sources.json', 'queries.public.json', 'reference.private.json',
         'author-evidence.private.json', 'calibration.private.json', 'slots.json',
         'static-requests.json', 'dynamic-rules.json', 'implementation-sha256.json'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


seed = load('binding_seed', HERE.parent / 'source-accounted-encoding-v1/plan.py')
corpus = load('initial_id_consumed_corpus', HERE.parent / 'fresh-alias-generalization-v1/corpus.py')
read, sha, digest, transcript, choice_reader = seed.read, seed.sha, seed.digest, seed.transcript, seed.choice_reader
PROFILES, METHODS, BUDGETS = ('otter','tansy'), ('scope-alias-encoding-v1','source-id-initial-encoding-v1'), (1536,)
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-11-07', 28
alias_candidate = load('initial_id_original_alias', HERE.parent / 'scope-alias-encoding-v1/candidate.py')
id_candidate = load('initial_id_candidate', HERE / 'candidate.py')


def factory(method):
    if method not in METHODS:
        raise ValueError('Foreign comparison method')
    return alias_candidate if method == METHODS[0] else id_candidate


def inputs():
    data=corpus.build()
    data['sources']={p:v for p,v in data['sources'].items()if p in PROFILES}
    data['rows']=[r for r in data['rows']if r['person']in PROFILES]
    data['author_evidence']=[r for r in data['author_evidence']if r['person']in PROFILES]
    data['design'].update(fictional_people=2,source_messages=96,person_cases_per_method_budget=88,known=56,unknown=32,positive_name_cases=24,other_cases=64,denied_identity_cases=8,same_choice_uncertainty_cases=8,new_fictional_sources=False,consumed_development_sources=True)
    return data


def bank(pid):
    if pid in ('shared_chain', 'shared_qualified'):
        return pid.removeprefix('shared_')
    if pid not in PROFILES:
        raise ValueError('Foreign person/bank')
    return corpus.FAMILIES[corpus.PROFILES.index(pid)]


def parent(slot):
    return slot['profile'], slot['method'], slot['budget'], slot['generation']


def slots():
    jobs = [('none', pid, None, None, None, None, None) for pid in ('shared_chain', 'shared_qualified')]
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
        raise ValueError('Outside frozen28schedule')
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
    req = choice_reader.make_request(text, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': system, **req,
            'prompt': seed.base.base.old.old.COMMON + req['prompt']}


def implementation():
    files = seed.implementation()
    files['benchmarks/scope-alias-encoding-v1/candidate.py'] = sha(HERE.parent / 'scope-alias-encoding-v1/candidate.py')
    files['benchmarks/fresh-alias-generalization-v1/corpus.py'] = sha(HERE.parent / 'fresh-alias-generalization-v1/corpus.py')
    files.update({PREFIX + '/' + p.name: sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = {
        'kind': 'unapproved_initial_source_id28', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 4, 'independent_extractions': 8, 'card_reads': 16},
        **data['design'], 'profiles': list(PROFILES), 'methods': list(METHODS), 'whole_public_budgets': list(BUDGETS),
        'generations_per_person_method_budget': 2, 'reads_per_parent': 2, 'orders_per_read': 2,
        'answers_per_joint_case': 8,
        'encoder': 'Own48existing fictional messages and budget;current alias uses original guidance/schema,source-ID uses new generic reference guidance/schema. No queries,reference,author maps,HAND,case evidence,old cards/graphs,responses/scores,manual relation annotation,diagnostic output or other generation.',
        'reader': 'Unchanged standard reader/prefix;own complete public card and own88public forms only. No source supplement,external name decoder,reference or private accounting.',
        'control': 'Fresh none per each of2banks then2own full44/44bothorders,no missing and personal-known gain. Both must qualify before extraction. Any failure closes scope and is not compression loss.',
        'endpoint': 'Fixed88person/cases per method:56known,32unknown;all2generations x2reads x2orders correct. Two people and families44each,11cohorts8each,24positive names/64other,8denied and8same-choice uncertainty. Missing stays in denominator. Same cases across methods,not176independent observations.',
        'intervention': 'Existing scope-alias versus source-ID initial extraction. New wire forbids model-written quote and enumerates own source IDs;program reconstructs full original messages then runs original alias/accounting/binder/compiler. Standard reader,whole1536budget and one-child180s transport unchanged. No claim this fixes child timeouts or semantic classification.',
        'invalid': 'Binding/ownership/witness/budget-invalid parent skips only own2reads;its44cases stay missing in88endpoint. No truncation or replacement.',
        'fatal': 'Control,transport,structural schema/decode,unknownusage,model,input/runtime or ownedguard failure closes remainder. No retry,repair,resume,replenishment or budget reuse.',
        'selection': 'Two consumed adversarial development sources selected after a14-call closed run. Chain otter and qualified tansy;not holdout or independent semantic gold. The source-ID prototype is motivated by one literal-quote availability failure. A separate timeout had a turn.completed event,which does not prove a usable final card or establish its cause.',
        'loss_localization': 'Separate copying-related invalidity,unknown/wrong choices,namespaces/alias mapping,conditions,read/order disagreement and generation missingness. Do not replace missing byU. Full source anchors are private and not extra reader memory. ID existence does not prove semantics.',
        'new_fictional_sources': False, 'methods_unchanged': False, 'compiler_reader_transport_unchanged': True,
        'measured_results_available': False, 'real_person_fidelity_verified': False,
        'source_reference_semantics_verified': False, 'cross_provider_verified': False,
        'population_stability_verified': False, 'production_default_changed': False,
        'old_observations_replaced': False, 'old_scopes_reopened': False,
        'aggregate_token_cap': None, 'money_cap': None, 'local_child_timeout_seconds': 180,
        'approved': False, 'new_service_authority': False,
        'execution_condition': 'Fresh direct finite28grant and all three exact published implementation CI jobs successful.'}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
            'reference.private.json': data['rows'], 'author-evidence.private.json': data['author_evidence'],
            'calibration.private.json': {key:dict(value,losses=[r for r in value['losses']if r['person']in PROFILES],planned=88,correct=88-sum(r['person']in PROFILES for r in value['losses']))for key,value in corpus.damage_summary().items()}, 'slots.json': slots(),
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
