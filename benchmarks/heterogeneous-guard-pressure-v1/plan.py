"""Prepare an unapproved16attempt pressure study; never contacts a service."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


seed = load('guard_pressure_previous_plan', HERE.parent / 'fresh-direct-768-v1/plan.py')
corpus = load('guard_pressure_corpus', HERE / 'corpus.py')
candidate = seed.candidate
sha, digest, read = seed.sha, seed.digest, seed.read
choice_reader = seed.choice_reader
PROFILES, METHODS = corpus.PROFILES, ('compact768', 'compact1536')
METHOD_BUDGET = dict(zip(METHODS, (768, 1536)))
MODEL, AS_OF, CAP = 'gpt-6.1-sol', '2026-11-08', 16
FILES = {'proposal.json', 'sources.json', 'queries.public.json', 'reference.private.json',
         'author-evidence.private.json', 'slots.json', 'static-requests.json',
         'dynamic-rules.json', 'implementation-sha256.json'}


def inputs(): return corpus.build()


def bank(person):
    person = person[7:] if person.startswith('shared_') else person
    if person not in PROFILES: raise ValueError('Foreign person or bank')
    return person


def parent(slot): return slot['profile'], slot['method'], slot['budget'], slot['generation']


def slots():
    jobs = [('none', 'shared_' + person, None, None, None, None, None) for person in PROFILES]
    jobs += [('full', person, None, None, None, None, None) for person in PROFILES]
    for generation in (0,):
        for pi, person in enumerate(PROFILES):
            for method in METHODS if (pi + generation) % 2 == 0 else tuple(reversed(METHODS)):
                budget = METHOD_BUDGET[method]
                jobs.append(('extract', person, method, budget, generation, None, None))
                jobs.extend(('read', person, method, budget, generation, repeat, 'card') for repeat in (0, 1))
    return [dict(slot=i + 1, kind=k, profile=p, method=m, budget=b, generation=g,
                 read_repeat=r, view=v, key=':'.join(map(str, (k, p, m, b, g, r, v))))
            for i, (k, p, m, b, g, r, v) in enumerate(jobs)]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract': raise ValueError('Foreign extraction')
    return candidate.bind(answer, inputs()['sources'][slot['profile']], slot['budget'])


def request(slot, parents=None):
    if slot not in slots(): raise ValueError('Outside frozen16schedule')
    person, kind = slot['profile'], slot['kind']
    data = inputs()
    common = seed.seed.seed.base.base.old.old
    if kind == 'extract':
        return dict(model=MODEL, system=common.grouped_support.SYSTEM,
                    **candidate.make_request(data['sources'][person], slot['budget']))
    if kind == 'none': material = ''
    elif kind == 'full': material = seed.transcript(data['sources'][person])
    else:
        if parent(slot) not in (parents or {}): return None
        own = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == parent(slot))
        material = bind(own, parents[parent(slot)])['prompt.md']
    req = choice_reader.make_request(material, data['queries'][bank(person)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': common.grouped_support.SYSTEM, **req,
            'prompt': common.COMMON + req['prompt']}


def implementation():
    result = seed.implementation()
    result.update({str(p.relative_to(ROOT)): sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(result.items()))


def values():
    data = inputs()
    evidence = [dict(person=r['person'], case=r['case'], author_navigation_not_semantic_gold=True,
        complete_episode_source_ids=[s['id'] for s in data['sources'][r['person']]['sources']
            if s['episode_id'] == 'project' + r['case'].split('_', 1)[0]]) for r in data['rows']]
    proposal = dict(kind='unapproved_heterogeneous_guard_pressure16', approved=False,
        new_model_calls=0, new_service_authority=False, max_new_local_cli_attempts=CAP,
        model_requested=MODEL, aggregate_token_cap=None, money_cap=None, child_timeout_seconds=180,
        stages=dict(controls=4, independent_extractions=4, card_reads=8),
        fictional_people=2, source_messages=96, messages_per_person=48,
        unique_public_forms=328, forms_per_reader=164, fixed_person_cases_per_budget=164,
        known=72, unknown=92, methods=list(METHODS), whole_budgets=[768, 1536],
        generations=1, reads=2, orders=2, answers_per_joint_case=4,
        generation_stability_tested=False,
        comparison='Same existing source-ID compact encoder and compiler at768vs1536. Each source-only extraction sees its own48messages and budget,not another generation. Budget changes both request and rendering,not a pure-layout intervention.',
        encoder_excludes='Questions,reference,author graph/policy/HAND,calibration,old cards/graphs/responses/scores,other generation,manual repair. No real-person data.',
        reader='Own valid whole card plus164public forms only;no source supplement,graph,author decoder or reference. Both full controls must retain all82cases in bothorders with known gain over their own none bank before any extraction.',
        endpoint='Each budget fixed164cases:72known92unknown. One source-only generation*two reads*two orders must all agree with reference. Invalid parent skips only its own two reads;its82cases remain missing,not U. No best-of selection.',
        fatal='Control,transport,wire/decode,unknown usage,model/runtime/guard failures close scope. No retry,repair,resume,replenishment or closed-scope reuse. Invalid binding/budget is a missing product,not a measured semantic choice error.',
        new_information='Six different action pairs,units,thresholds,gates,guards and local exceptions within each person;threshold-only revisions,guard replacements,narrow guard relaxation,old aliases and copies. Current amendments explicitly restate choices. No withdrawal or correlated cross-project uncertainty claim.',
        prior_offline_observation='An author-complete graph for each person is accepted at1536 and rejected at768 by the unchanged encoder. This is a representation/preflight limitation,not model-generated loss,an information-theoretic lower bound or extraction measurement.',
        reference='Hand table cross-checked with finite policy and exact author graph projection. Same author knew prior failures;not independently adjudicated semantic gold,holdout,real user or cross-provider evidence.',
        execution_condition='New explicit finite16grant bound to final manifest and exact published commit;all three CI jobs and required steps succeed. Prior54is closed and cannot be reused.',
        production_defaults_changed=False, model_results_available=False)
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
        'reference.private.json': data['rows'], 'author-evidence.private.json': evidence, 'slots.json': slots(),
        'static-requests.json': {str(s['slot']): request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': dict(slots=[s for s in slots() if s['kind'] == 'read'],
            builder='benchmarks/heterogeneous-guard-pressure-v1/plan.py:request', only_own_valid_parent=True),
        'implementation-sha256.json': implementation()}


def prepare(destination):
    destination = Path(destination); content = values(); destination.mkdir(parents=True, exist_ok=False)
    for name, value in content.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (destination / 'manifest.json').write_text(json.dumps(dict(files={n: sha(destination / n)
        for n in sorted(content)}, new_model_calls=0), indent=2) + '\n')
    return content['proposal.json']


def verify(root, *, reconstruct=True):
    root = Path(root)
    if root.is_symlink() or (root / 'manifest.json').is_symlink(): raise ValueError('Symlink packet refused')
    manifest = read(root / 'manifest.json')
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Preparation manifest differs')
    if set(manifest['files']) != FILES or {p.name for p in root.iterdir()} != FILES | {'manifest.json'}:
        raise ValueError('Frozen packet set differs')
    for name, fingerprint in manifest['files'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or sha(path) != fingerprint: raise ValueError('Frozen packet drift')
    if read(root / 'implementation-sha256.json') != implementation(): raise ValueError('Implementation drift')
    if reconstruct and any(digest(read(root / n)) != digest(v) for n, v in values().items()):
        raise ValueError('Frozen reconstruction differs')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', required=True, type=Path)
    print(json.dumps(prepare(parser.parse_args().out), ensure_ascii=False, indent=2))
