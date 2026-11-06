"""Unapproved repeat of single-pass compression; no service backend or grant."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location(
    'single_repeat_seed', ROOT / 'benchmarks/fresh-enum-pipeline-v1/plan.py')
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)
read, sha, digest = seed.read, seed.sha, seed.digest
MODEL, AS_OF, BUDGET, CAP = seed.MODEL, seed.AS_OF, seed.BUDGET, 45
PROFILES, VIEWS = seed.PROFILES, ('card', 'tail')
producer, choice_reader, transcript = seed.producer, seed.choice_reader, seed.transcript


def inputs():
    return seed.inputs()


def slots():
    jobs = []

    def add(kind, profile=None, generation_repeat=None, view=None, read_repeat=None):
        jobs.append(dict(slot=len(jobs) + 1, kind=kind, profile=profile,
                         generation_repeat=generation_repeat, view=view,
                         read_repeat=read_repeat))

    add('none')
    for pid in PROFILES:
        add('full', pid)
    for generation in (0, 1):
        people = PROFILES if generation == 0 else tuple(reversed(PROFILES))
        for pid in people:
            add('extract', pid, generation)
            order = VIEWS if (PROFILES.index(pid) + generation) % 2 == 0 else tuple(reversed(VIEWS))
            for repeat in (0, 1):
                for view in (order if repeat == 0 else tuple(reversed(order))):
                    add('read', pid, generation, view, repeat)
    return jobs


def bind(pid, answer):
    if pid not in PROFILES:
        raise ValueError('Foreign person')
    return producer.bind(answer, inputs()['sources'][pid], BUDGET)


def material(slot, graphs):
    if slot not in slots() or slot['kind'] != 'read':
        raise ValueError('Outside reader schedule')
    key = (slot['profile'], slot['generation_repeat'])
    if key not in graphs:
        return None
    prompt = bind(slot['profile'], graphs[key])['prompt.md']
    if not 0 < len(prompt) <= BUDGET:
        raise ValueError('Whole-public budget differs')
    if slot['view'] == 'card':
        return prompt
    raw = transcript(inputs()['sources'][slot['profile']])
    if len(raw) <= BUDGET:
        raise ValueError('Source must exceed card ceiling')
    return raw[-len(prompt):]


def request(slot, graphs=None):
    if slot not in slots():
        raise ValueError('Outside frozen repeat schedule')
    data = inputs()
    pid = slot['profile']
    if slot['kind'] == 'extract':
        req = producer.make_request(data['sources'][pid], BUDGET)
    else:
        text = '' if slot['kind'] == 'none' else (
            transcript(data['sources'][pid]) if slot['kind'] == 'full'
            else material(slot, {} if graphs is None else graphs))
        if text is None:
            return None
        req = choice_reader.make_request(text, data['queries']['all'], as_of=AS_OF,
                                        answer_format='text', reader_mode='standard')
        req['prompt'] = seed.seed.base.base.old.old.COMMON + req['prompt']
    return {'model': MODEL, 'system': seed.seed.base.base.old.old.grouped_support.SYSTEM, **req}


def implementation():
    # Read the explicit dependency names instead of invoking historical plans'
    # frozen executor checks. This controller never uses the legacy executor.
    files = {}
    for name in read(HERE / 'dependencies.json'):
        relative = Path(name)
        file = ROOT / relative
        if relative.is_absolute() or '..' in relative.parts or file.is_symlink():
            raise ValueError('Unsafe scientific dependency')
        files[name] = sha(file)
    files['benchmarks/single-pass-repeat-v1/dependencies.json'] = sha(HERE / 'dependencies.json')
    files.update({'benchmarks/single-pass-repeat-v1/' + p.name: sha(p)
                  for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = {
        'kind': 'unapproved_single_pass_repeat45', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP,
        'stages': {'controls': 5, 'independent_initial_extractions': 8,
                   'card_readers': 16, 'equal_character_tail_readers': 16},
        'fictional_people': 4, 'source_messages': 88, 'public_question_forms': 32,
        'primary_unique_person_cases_per_view': 64, 'known': 24, 'unknown': 40,
        'derived_known': 8, 'generations_per_person': 2, 'reads_per_card': 2,
        'orders_per_read': 2, 'answers_per_generation_case': 4,
        'joint_answers_per_person_case': 8, 'whole_public_character_cap': BUDGET,
        'views': list(VIEWS), 'review_calls': 0,
        'reference': 'Exactly the consumed fresh45 sources,public forms and source-licensed reference;no old responses in any request or new primary score.',
        'encoder': 'Unchanged coverage/source-order-v3;own source only,not questions,reference,old cards,responses,scores,author parameters or another generation.',
        'controls': 'Five new controls;each full16/16bothorders,no missing,and own-known gain over new shared none,before any extraction.',
        'endpoint': 'Each view keeps64unique person/cases;all2generations x2reads x2orders must match. Also report each generation separately;missing remains in denominator.',
        'invalid': 'Invalid initial product skips only its own4readers;other independent generations continue.No repair or replacement.',
        'fatal': 'Control,transport,shared schema/decode,unknownusage,model,input/runtime or ownedguard failure closes remainder.No retry,resume,repair or replenishment.',
        'scope_claim': 'Output directory must be created before a host claims an exclusive single-use execution intent;claim still precedes backend entry.',
        'source_reused_development': True, 'independent_holdout': False,
        'real_person_fidelity_verified': False, 'population_generation_stability_verified': False,
        'source_reference_semantics_verified': False, 'cross_provider_verified': False,
        'token_matched_tail': False, 'optimal_tail_selection': False,
        'old_scores_replaced': False, 'old_scopes_reopened': False,
        'production_default_changed': False, 'approved': False,
        'new_service_authority': False, 'aggregate_token_cap': None, 'money_cap': None,
        'local_child_timeout_seconds': 180,
        'execution_condition': 'New explicit finite-scope grant and all three CI checks passing at the exact published implementation head.'}
    return {
        'proposal.json': proposal, 'sources.json': data['sources'],
        'queries.public.json': data['queries'], 'reference.private.json': data['rows'],
        'author-evidence.private.json': data['author_evidence'], 'slots.json': slots(),
        'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                               'builder': 'benchmarks/single-pass-repeat-v1/plan.py:request',
                               'only_own_generation_parent': True},
        'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination)
    data = values()
    destination.mkdir(exist_ok=False)
    for name, value in data.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(
        {'files': {n: sha(destination / n) for n in sorted(data)}, 'new_model_calls': 0}, indent=2) + '\n')


def verify(root):
    root = Path(root)
    if root.is_symlink():
        raise ValueError('Symlink input root')
    expected = values()
    manifest_file = root / 'manifest.json'
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise ValueError('Unsafe input manifest')
    manifest = read(manifest_file)
    if (set(manifest) != {'files', 'new_model_calls'} or
            type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0):
        raise ValueError('Foreign manifest')
    if set(manifest['files']) != set(expected):
        raise ValueError('Manifest file set differs')
    if {p.name for p in root.iterdir()} != set(expected) | {'manifest.json'}:
        raise ValueError('Input directory file set differs')
    for name, value in expected.items():
        file = root / name
        if file.is_symlink() or not file.is_file() or sha(file) != manifest['files'][name]:
            raise ValueError('Frozen input drift')
        if read(file) != value:
            raise ValueError('Input reconstruction differs')
    return True
