"""Frozen source-accounted comparison preparation; no backend or service authority."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'benchmarks/source-accounted-encoding-v1'
FILES = {'proposal.json', 'sources.json', 'queries.public.json', 'reference.private.json',
         'slots.json', 'static-requests.json', 'dynamic-rules.json', 'implementation-sha256.json'}


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


seed = load('accounted_comparison_seed', ROOT / 'benchmarks/ambiguous-source-repeat-v1/plan.py')
candidate = load('accounted_comparison_candidate', HERE / 'candidate.py')
base, coverage = seed.base, seed.coverage
read, sha, digest, choice_reader, transcript = seed.read, seed.sha, seed.digest, seed.choice_reader, seed.transcript
PROFILES, METHODS = ('c2v', 'f7s'), ('object-coverage-guidance-v1', 'source-accounted-graph-v1')
MODEL, AS_OF, CAP, BUDGET = 'gpt-6.1-sol', '2026-11-02', 27, 1536


def inputs():
    data = base.inputs()
    rows = [r for r in data['rows'] if r['person'] in PROFILES]
    if len(rows) != 30 or sum(r['gold'] != 'U' for r in rows) != 13:
        raise ValueError('Original reference population differs')
    return {'sources': {pid: data['sources'][pid] for pid in PROFILES},
            'queries': data['queries'], 'rows': rows}


def bank(pid):
    if pid not in PROFILES + ('shared_all',):
        raise ValueError('Foreign person/bank')
    return 'all'


def factory(method):
    if method not in METHODS:
        raise ValueError('Foreign encoder')
    return coverage if method == METHODS[0] else candidate


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def slots():
    jobs = [('none', 'shared_all', None, None, None, None)]
    jobs += [('full', pid, None, None, None, None) for pid in PROFILES]
    for generation in (0, 1):
        for index, pid in enumerate(PROFILES):
            for method in METHODS if (index + generation) % 2 == 0 else reversed(METHODS):
                jobs.append(('extract', pid, method, generation, None, None))
                jobs.extend(('read', pid, method, generation, repeat, 'card') for repeat in (0, 1))
    return [{'slot': i + 1, 'kind': k, 'profile': pid, 'method': m, 'generation': g,
             'budget': BUDGET if m else None, 'read_repeat': r, 'view': v,
             'key': ':'.join(map(str, (k, pid, m, g, r, v)))}
            for i, (k, pid, m, g, r, v) in enumerate(jobs)]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract':
        raise ValueError('Only a planned own extraction may bind')
    return factory(slot['method']).bind(answer, inputs()['sources'][slot['profile']], BUDGET)


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen 27-slot schedule')
    data, pid = inputs(), slot['profile']
    system = base.base.old.old.grouped_support.SYSTEM
    if slot['kind'] == 'extract':
        return {'model': MODEL, 'system': system,
                **factory(slot['method']).make_request(data['sources'][pid], BUDGET)}
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
    return {'model': MODEL, 'system': system, **req, 'prompt': base.base.old.old.COMMON + req['prompt']}


def implementation():
    # This new protocol uses current code and never calls the legacy executor.
    # Preserve historical plans' old locks; collect the explicitly reviewed
    # current dependency names here,as the single-pass controller already does.
    files = {}
    for name in read(HERE / 'dependencies.json'):
        relative = Path(name)
        file = ROOT / relative
        if relative.is_absolute() or '..' in relative.parts or file.is_symlink():
            raise ValueError('Unsafe scientific dependency')
        files[name] = sha(file)
    files[PREFIX + '/dependencies.json'] = sha(HERE / 'dependencies.json')
    files.update({PREFIX + '/' + p.name: sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = {
        'kind': 'unapproved_source_accounted_comparison27', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'source_messages': 44, 'profiles': list(PROFILES),
        'public_question_forms': 30, 'methods': list(METHODS), 'whole_public_character_cap': BUDGET,
        'stages': {'controls': 3, 'source_only_extractions': 8, 'card_reads': 16},
        'primary_cases_per_method': 30, 'known': 13, 'unknown': 17,
        'generations_per_person_method': 2, 'reads_per_parent': 2, 'orders_per_read': 2,
        'answers_per_joint_case': 8,
        'control': 'Shared none then two own full15/15bothorders,no missing and personal-known gain before extraction.',
        'intervention': 'Source-accounting schema, per-message observation ownership and literal direct-action witness checks; source-only guidance. Existing graph compiler/reader and budget unchanged. This is a bundled contract candidate,not a single-factor causal ablation.',
        'source_only': 'Own22fictional messages,budget and fixed instructions/schema. No questions,reference,old graph/card,response/score,other generation,manual disposition or author parameters.',
        'endpoint': 'Fixed30person/cases per method;all2generations x2reads x2orders correct. Missing remains in denominator. Separate13known,17unknown,derived-known,withdrawal and each generation;no best-of.',
        'invalid': 'Binding/ownership/witness/budget invalid parent skips only its own2reads,leaving15missing. Shared structural schema failures are fatal,not repaired.',
        'fatal': 'Control,transport,wire/schema/decode,unknownusage,model,input/runtime or ownedguard failure closes all remainder. No retry,repair,resume,replenishment or budget reuse.',
        'selection': 'Two consumed fictional development sources selected because previous bad cards omitted known choices; not fresh people,independent holdout or causal population advantage.',
        'semantic_classification_verified': False, 'source_completeness_verified': False,
        'real_person_fidelity_verified': False, 'cross_provider_verified': False,
        'measured_results_available': False, 'production_default_changed': False,
        'old_observations_replaced': False, 'old_scopes_reopened': False,
        'aggregate_token_cap': None, 'money_cap': None, 'local_child_timeout_seconds': 180,
        'approved': False, 'new_service_authority': False,
        'execution_condition': 'Fresh direct finite27grant and all three exact published implementation CI jobs successful.'}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
            'reference.private.json': data['rows'], 'slots.json': slots(),
            'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
            'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
                                   'builder': PREFIX + '/plan.py:request', 'only_own_valid_parent': True},
            'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination)
    contents = values()
    destination.mkdir(exist_ok=False)
    for name, value in contents.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(
        {'files': {n: sha(destination / n) for n in sorted(contents)}, 'new_model_calls': 0}, indent=2) + '\n')
    return contents['proposal.json']


def verify(root, *, reconstruct=True):
    root = Path(root)
    if root.is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('Prepared symlinks refused')
    manifest = read(root / 'manifest.json')
    expected = values() if reconstruct else None
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Invalid preparation manifest')
    names = set(manifest['files'])
    if names != FILES or {p.name for p in root.iterdir()} != names | {'manifest.json'}:
        raise ValueError('Changed prepared file set')
    for name, fingerprint in manifest['files'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or sha(path) != fingerprint:
            raise ValueError('Frozen prepared input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Implementation drift')
    if expected is not None and any(read(root / name) != value for name, value in expected.items()):
        raise ValueError('Input reconstruction differs')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
