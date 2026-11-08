"""Freeze a new54-attempt source-only768comparison. No backend or approval."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
PREFIX = 'benchmarks/fresh-direct-768-v1'
FILES = {'proposal.json', 'sources.json', 'queries.public.json', 'reference.private.json',
         'author-evidence.private.json', 'calibration.private.json', 'slots.json',
         'static-requests.json', 'dynamic-rules.json', 'implementation-sha256.json'}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


seed = load('direct768_shared_reader', HERE.parent / 'source-id-initial-encoding-v1/plan.py')
corpus = load('direct768_new_corpus', HERE / 'corpus.py')
candidate = load('direct768_new_candidate', HERE / 'candidate.py')
read, sha, digest, transcript, choice_reader = seed.read, seed.sha, seed.digest, seed.transcript, seed.choice_reader
PROFILES = corpus.PROFILES
METHODS = ('source-id-flat', 'source-id-factor')
BUDGETS = (768,)
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-11-08', 54


def inputs(): return corpus.build()


def bank(person):
    if person in ('shared_strict', 'shared_released'): return person.removeprefix('shared_')
    if person not in PROFILES: raise ValueError('Foreign person or bank')
    return corpus.FAMILIES[PROFILES.index(person)]


def factory(method):
    if method not in METHODS: raise ValueError('Foreign encoding method')
    return candidate.base if method == METHODS[0] else candidate


def parent(slot): return slot['profile'], slot['method'], slot['budget'], slot['generation']


def slots():
    jobs = [('none', p, None, None, None, None, None) for p in ('shared_strict', 'shared_released')]
    jobs += [('full', p, None, None, None, None, None) for p in PROFILES]
    for generation in (0, 1):
        for pi, person in enumerate(PROFILES):
            methods = METHODS if (pi + generation) % 2 == 0 else tuple(reversed(METHODS))
            for method in methods:
                jobs.append(('extract', person, method, 768, generation, None, None))
                jobs.extend(('read', person, method, 768, generation, repeat, 'card') for repeat in (0, 1))
    return [dict(slot=i + 1, kind=kind, profile=p, method=m, budget=b, generation=g,
                 read_repeat=r, view=v, key=':'.join(map(str, (kind, p, m, b, g, r, v))))
            for i, (kind, p, m, b, g, r, v) in enumerate(jobs)]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract': raise ValueError('Only own frozen extraction can bind')
    return factory(slot['method']).bind(answer, inputs()['sources'][slot['profile']], slot['budget'])


def request(slot, parents=None):
    if slot not in slots(): raise ValueError('Outside frozen54schedule')
    data, pid = inputs(), slot['profile']
    common = seed.seed.base.base.old.old
    if slot['kind'] == 'extract':
        return dict(model=MODEL, system=common.grouped_support.SYSTEM,
                    **factory(slot['method']).make_request(data['sources'][pid], slot['budget']))
    if slot['kind'] == 'none': text = ''
    elif slot['kind'] == 'full': text = transcript(data['sources'][pid])
    else:
        if parent(slot) not in (parents or {}): return None
        own = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == parent(slot))
        text = bind(own, parents[parent(slot)])['prompt.md']
    req = choice_reader.make_request(text, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': common.grouped_support.SYSTEM, **req,
            'prompt': common.COMMON + req['prompt']}


def implementation():
    files = seed.implementation()
    for path in [HERE.parent / 'common-condition-factor-v1/codec.py', *HERE.glob('*.py')]:
        files[str(path.relative_to(ROOT))] = sha(path)
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = dict(kind='unapproved_fresh_direct768_54', requested_model=MODEL, as_of=AS_OF,
        max_new_local_cli_attempts=CAP, stages=dict(controls=6, independent_extractions=16, card_reads=32),
        **data['design'], profiles=list(PROFILES), methods=list(METHODS), whole_public_budgets=[768],
        generations_per_person_method=2, reads_per_parent=2, orders_per_read=2, answers_per_joint_case=8,
        encoder='Own54new fictional messages and whole768budget only. No questions,reference,HAND,author policy/graph,calibration,old card/graph,response/score,another generation or manual binding.',
        reader='Unchanged standard reader and prefix;own valid complete768card plus192public forms only. No original source,raw graph,private accounting,decoder program,flat supplement,reference or old response.',
        controls='Two none banks then four own full histories. Every full96cases correct in both orders,no missing,and known gain over its own bank none. All four must qualify before extraction. Otherwise close scope without calling it compression loss.',
        comparison='Current source-ID flat renderer and new source-only factor-aware request plus reversible composed renderer. Same graph schema,witnesses,roles,aliases,revisions,reader and final768ceiling. Internal16000validation is not delivered memory. New compiler chooses by size only between unchanged dense packing and exact common-prefix-then-dense packing. This is a request-and-renderer intervention,not a pure format causal estimate.',
        endpoint='Fixed384person/cases per method:168known,216unknown. Strict family192cases(72known120unknown);released family192(96known96unknown). Each requires2independent generations*2reads*2ordersallcorrect. Person,family,cohort,per-generation and missing separate. Four fictional people are the person-level units;cases and reads are not independent people.',
        localization='Trace every failure from complete role-labelled source episodes through own raw/resolved graph,source accounting,active rows and full public card to both reads/orders. Inspect omitted second choice,specific material guard retained/relaxed,gate,numeric boundary,local revision,alias/copy ownership and false status. Structural accounting and an author-linked literal are not semantic proof.',
        invalid='Ownership,binding,condition,revision or whole-budget invalid parent skips only its own two reads;96cases remain missing in384denominator. No truncation,manual patch,replacement or best-generation choice.',
        fatal='Control,transport,wire/decode,unknown usage,requested model,input/runtime/guard failure closes remainder. No retry,repair,resume,replenishment or reuse of closed scopes.',
        selection='All four people,216messages and384public forms are new and not used in prior recorded external evaluation calls. The same author knew earlier failures and authored references;not independent semantic gold or an independent holdout. Hand and policy/damage fixtures validate construction only,not model fidelity.',
        approved=False, new_service_authority=False, new_model_calls=0,
        aggregate_token_cap=None, money_cap=None, local_child_timeout_seconds=180,
        measured_results_available=False, real_person_fidelity_verified=False, cross_provider_verified=False,
        population_stability_verified=False, source_reference_semantics_verified=False,
        production_default_changed=False, old_sources_cards_scores_modified=False, old_scopes_reopened=False,
        execution_condition='Fresh explicit finite54grant and exact published implementation all three CI jobs and all required steps successful. Ordinary continuation and GitHub sync grant no experiment budget.')
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
            'reference.private.json': data['rows'], 'author-evidence.private.json': data['author_evidence'],
            'calibration.private.json': corpus.damage_summary(), 'slots.json': slots(),
            'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
            'dynamic-rules.json': dict(slots=[s for s in slots() if s['kind'] == 'read'],
                builder=PREFIX + '/plan.py:request', only_own_valid_person_method_budget_generation=True),
            'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination); contents = values(); destination.mkdir(parents=True, exist_ok=False)
    for name, value in contents.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(dict(
        files={n: sha(destination / n) for n in sorted(contents)}, new_model_calls=0), indent=2) + '\n')
    return contents['proposal.json']


def verify(root, *, reconstruct=True):
    root = Path(root)
    if root.is_symlink() or (root / 'manifest.json').is_symlink(): raise ValueError('Symlink packet refused')
    manifest = read(root / 'manifest.json')
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Preparation manifest differs')
    if set(manifest['files']) != FILES or {p.name for p in root.iterdir()} != FILES | {'manifest.json'}:
        raise ValueError('Prepared file set differs')
    for name, fingerprint in manifest['files'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or sha(path) != fingerprint: raise ValueError('Frozen packet drift')
    if read(root / 'implementation-sha256.json') != implementation(): raise ValueError('Implementation drift')
    if reconstruct and any(digest(read(root / n)) != digest(v) for n, v in values().items()):
        raise ValueError('Frozen reconstruction differs')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().out), ensure_ascii=False, indent=2))
