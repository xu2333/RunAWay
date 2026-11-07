"""Unapproved fresh-scenario repeat; unchanged encoder/compiler/reader/controller."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


repeat = load('fresh_decision_repeat', ROOT / 'benchmarks/single-pass-repeat-v1/plan.py')
corpus = load('fresh_decision_corpus', HERE / 'corpus.py')
seed, producer, choice_reader, transcript = repeat.seed, repeat.producer, repeat.choice_reader, repeat.transcript
read, sha, digest = repeat.read, repeat.sha, repeat.digest
MODEL, AS_OF, BUDGET, CAP = repeat.MODEL, repeat.AS_OF, repeat.BUDGET, repeat.CAP
PROFILES, VIEWS = corpus.PROFILES, repeat.VIEWS


def inputs():
    return corpus.build()


def slots():
    # Same counterbalanced schedule, with only the person IDs remapped.
    remap = dict(zip(repeat.PROFILES, PROFILES))
    return [{**slot, 'profile': remap.get(slot['profile'])} for slot in repeat.slots()]


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
    raw = transcript(inputs()['sources'][slot['profile']])
    if not 0 < len(prompt) <= BUDGET or len(raw) <= BUDGET:
        raise ValueError('Card or source budget differs')
    return prompt if slot['view'] == 'card' else raw[-len(prompt):]


def request(slot, graphs=None):
    if slot not in slots():
        raise ValueError('Outside frozen schedule')
    data, pid = inputs(), slot['profile']
    if slot['kind'] == 'extract':
        req = producer.make_request(data['sources'][pid], BUDGET)
    else:
        text = '' if slot['kind'] == 'none' else transcript(data['sources'][pid]) if slot['kind'] == 'full' else material(slot, graphs or {})
        if text is None:
            return None
        req = choice_reader.make_request(text, data['queries']['all'], as_of=AS_OF,
                                        answer_format='text', reader_mode='standard')
        req['prompt'] = repeat.seed.seed.base.base.old.old.COMMON + req['prompt']
    return {'model': MODEL, 'system': repeat.seed.seed.base.base.old.old.grouped_support.SYSTEM, **req}


def implementation():
    files = repeat.implementation()
    files.update({'benchmarks/fresh-decision-v1/' + p.name: sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    if min(sum(len(s['text']) for s in src['sources']) for src in data['sources'].values()) <= BUDGET:
        raise ValueError('Text-only source must exceed card ceiling')
    proposal = {
        'kind': 'unapproved_fresh_decision45', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP,
        'stages': {'controls': 5, 'independent_initial_extractions': 8, 'card_readers': 16,
                   'equal_character_tail_readers': 16},
        **data['design'], 'whole_public_character_cap': BUDGET,
        'generations_per_person': 2, 'reads_per_card': 2, 'orders_per_read': 2,
        'joint_answers_per_person_case': 8,
        'controls': 'Each full16/16bothorders,no missing,and own-known gain over new shared none before extraction.',
        'endpoint': '64unique person/cases per view;all2generations x2reads x2orders correct;missing remains in denominator;report generation and cohort slices separately.',
        'encoder': 'Unchanged coverage/source-order-v3 and whole1536 compiler;source only,no questions,reference,author settings,old cards/responses/scores or other generation.',
        'reader': 'Unchanged standard reader;only own card or exact-character role-labelled source suffix plus same32public forms;no external decoder.',
        'controller': 'Reuse single-pass-repeat-v1 run function unchanged;replace plan module and add cohort reporting only;four people and16cases/person remain compatible.',
        'invalid': 'Binding/budget invalid product skips only its own4reads;other independent generations continue;all64cases remain.',
        'fatal': 'Control,transport,wire/schema/decode,unknownusage,model,input/runtime/guard failure closes remainder;no retry,repair,resume or replenishment.',
        'scope_claim': 'Successful output-directory creation precedes exclusive one-use intent;intent precedes backend entry.',
        'fresh_after_method_freeze': True, 'source_reused_development': False,
        'author_knows_previous_failures': True, 'independent_holdout': False,
        'reference_is_author_design_not_independent_judgment': True,
        'population_generation_stability_verified': False, 'cross_provider_verified': False,
        'semantic_reference_acceptance_verified': False,
        'token_matched_tail': False, 'optimal_tail_selection': False,
        'approved': False, 'new_service_authority': False, 'measured_results_available': False,
        'old_scopes_reopened': False, 'old_scores_replaced': False, 'production_default_changed': False,
        'aggregate_token_cap': None, 'money_cap': None, 'local_child_timeout_seconds': 180,
        'execution_condition': 'New direct human finite45grant and all three exact-head CI checks passing.'}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
            'reference.private.json': data['rows'], 'author-evidence.private.json': data['author_evidence'],
            'slots.json': slots(),
            'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
            'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                                   'builder': 'benchmarks/fresh-decision-v1/plan.py:request',
                                   'only_own_generation_parent': True},
            'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination)
    data = values()
    destination.mkdir(exist_ok=False)
    for name, value in data.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(
        {'files': {name: sha(destination / name) for name in sorted(data)}, 'new_model_calls': 0}, indent=2) + '\n')


def verify(root):
    root = Path(root)
    expected = values()
    if root.is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('Symlink input refused')
    manifest = read(root / 'manifest.json')
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Foreign manifest')
    if set(manifest['files']) != set(expected) or {p.name for p in root.iterdir()} != set(expected) | {'manifest.json'}:
        raise ValueError('Input set differs')
    for name, value in expected.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or sha(path) != manifest['files'][name] or read(path) != value:
            raise ValueError('Input drift')
    return True
