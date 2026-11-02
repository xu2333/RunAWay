"""Prepare a finite, unapproved 52-attempt length-stress protocol; no backend."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load('long_task_prior_plan', HERE.parent / 'fresh-source-contrast-v1/plan.py')
corpus = load('long_task_corpus', HERE / 'corpus.py')
read, sha, digest, choice_reader = old.read, old.sha, old.digest, old.choice_reader
candidate = old.candidate
PROFILES, METHODS = corpus.PROFILES, ('source-order-v3',)
MODEL, AS_OF, CAP, BUDGET = 'gpt-6.1-sol', '2026-11-02', 52, 1536


def inputs():
    return corpus.build()


def bank(pid):
    if pid in PROFILES:
        return corpus.FAMILY[pid]
    if type(pid) is str and pid.startswith('shared_') and pid[7:] in {corpus.FAMILY[p] for p in PROFILES}:
        return pid[7:]
    raise ValueError('Foreign question bank')


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def cells():
    return [(p, METHODS[0], 0) for p in PROFILES]


def slots():
    jobs = []
    for domain in corpus.short.DOMAINS:
        family = domain[0]
        jobs += [('none', 'shared_' + family, None, None, None, None)]
        jobs += [('full', family + str(side), None, None, None, None) for side in (0, 1)]
    jobs += [('extract', p, m, g, None, None) for p, m, g in cells()]
    order = [(p, m, g, v) for i, (p, m, g) in enumerate(cells())
             for v in (('card', 'tail') if i % 2 == 0 else ('tail', 'card'))]
    for repeat in (0, 1):
        jobs += [('read', p, m, g, repeat, v) for p, m, g, v in (order if repeat == 0 else reversed(order))]
    return [{'slot': i + 1, 'kind': k, 'profile': p, 'method': m, 'generation': g,
             'budget': BUDGET if m else None, 'read_repeat': r, 'view': v,
             'key': ':'.join(map(str, (k, p, m, g, r, v)))}
            for i, (k, p, m, g, r, v) in enumerate(jobs)]


def bind(slot, answer):
    if slot not in slots() or slot['kind'] != 'extract':
        raise ValueError('Only own planned extraction may bind')
    return candidate.bind(answer, inputs()['sources'][slot['profile']], BUDGET)


def transcript(sources):
    """Keep every message and role in order; remove JSON/key/id wrapper overhead."""
    return '\n'.join(s['role'] + ': ' + s['text'] for s in sources['sources'])


def material(pid, prompt, view):
    if pid not in PROFILES or type(prompt) is not str or not 0 < len(prompt) <= BUDGET:
        raise ValueError('Person/card budget differs')
    if view == 'card':
        return prompt
    if view != 'tail':
        raise ValueError('Foreign material view')
    raw = transcript(inputs()['sources'][pid])
    if len(raw) <= BUDGET:
        raise ValueError('Source is not longer than the whole-card ceiling')
    return raw[-len(prompt):]


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen 52-slot schedule')
    data = inputs()
    pid = slot['profile']
    if slot['kind'] == 'extract':
        return {'model': MODEL, 'system': old.old.grouped_support.SYSTEM,
                **candidate.make_request(data['sources'][pid], BUDGET)}
    if slot['kind'] == 'none':
        text = ''
    elif slot['kind'] == 'full':
        text = transcript(data['sources'][pid])
    else:
        if parent(slot) not in (parents or {}):
            return None
        own = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == parent(slot))
        prompt = bind(own, parents[parent(slot)])['prompt.md']
        text = material(pid, prompt, slot['view'])
    req = choice_reader.make_request(text, data['queries'][bank(pid)], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': old.old.grouped_support.SYSTEM, **req,
            'prompt': old.old.COMMON + req['prompt']}


def implementation():
    files = list(HERE.glob('*.py')) + [
        ROOT / 'benchmarks/task-scenarios-v1/corpus.py',
        ROOT / 'benchmarks/task-contract-v1/authoring.py']
    return dict(sorted({**old.implementation(), **{str(p.relative_to(ROOT)): sha(p) for p in files}}.items()))


def values():
    data = inputs()
    lengths = {p: len(transcript(s)) for p, s in data['sources'].items()}
    contents = {p: sum(len(entry['text']) for entry in s['sources']) for p, s in data['sources'].items()}
    if min(contents.values()) <= BUDGET:
        raise ValueError('No guaranteed character bottleneck')
    proposal = {'kind': 'unapproved_long_task_length_stress52', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 12, 'source_only_extractions': 8,
            'card_reads': 16, 'own_equal_character_tail_reads': 16},
        'source_messages': 192, 'source_characters': lengths, 'primary_cases_per_view': 40,
        'source_json_characters': {p: len(old.old.canonical(s)) for p, s in data['sources'].items()},
        'source_content_characters': contents,
        'full_and_tail_share_same_role_labelled_transcript_layout': True,
        'known': 28, 'unknown': 12, 'unique_public_forms': 40, 'person_form_combinations': 80,
        'whole_public_character_cap': BUDGET, 'generations_per_profile': 1,
        'reads_per_view': 2, 'option_orders_per_read': 2, 'answers_per_primary_case_per_view': 4,
        'control': 'Own complete role-labelled transcript5/5 both orders,no missing,known gain over own family shared none.All8 fulls before extraction13.Any failure closes scope.',
        'endpoint': 'Per view40 fixed cases,one newly generated card/person,two reads and two orders all correct.Missing/invalid parents remain in denominator.No generation stability claim.',
        'tail': 'Exact suffix of own complete role-labelled transcript,matched to own entire compiled card character count.JSON keys/ids/episode metadata removed from both full and tail;all message text/roles/order retained.May begin mid-message.No repair,optimal span selection or token match.',
        'pair_rescoring': 'Reuse the same card responses against paired-person references only on32 divergent person/cases.No new wrong-card calls;dependent/algebraic diagnostic.',
        'invalid_product': 'Skip only own four card/tail reads;do not repair,replace,truncate or move slots.',
        'fatal': 'Control,transport,wire,decode,unknownusage,model,runtime,inputhash or guard failure closes remaining scope.Intent counts if receipt unknown.',
        'source_only': 'Own raw source,budget,fixed header/guide/guidance/schema only.No questions,reference,old cards/responses/scores or manual binding.',
        'all_extractions_before_any_read': True, 'aggregate_token_cap': None, 'money_cap': None,
        'timeout_per_local_child_seconds': 180, 'max_nominal_timeout_sum_seconds': 9360,
        'not_aggregate_duration_or_spend_cap': True, 'retry': False, 'repair': False, 'resume': False,
        'replenishment': False, 'unused_slots_expire': True, 'independent_holdout': False,
        'independent_semantic_acceptance': False, 'new_question_or_reference_labels': False,
        'new_scene_generalization_claim': False, 'generation_stability_verified': False,
        'real_person_fidelity_verified': False, 'approved': False, 'new_service_authority': False,
        'production_default_changed': False}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'queries.public.json': data['queries'],
        'author-reference.private.json': data['rows'], 'design.json': data['design'],
        'slots.json': slots(), 'static-requests.json': {s['key']: request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
            'builder': 'benchmarks/long-task-probe-v1/plan.py:request', 'own_valid_parent_only': True},
        'implementation-sha256.json': implementation()}


def prepare(destination):
    values_to_write = values()
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in values_to_write.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'manifest.json').write_text(json.dumps({
        'files': {n: sha(destination / n) for n in sorted(values_to_write)}, 'new_model_calls': 0}, indent=2) + '\n', encoding='utf-8')
    return values_to_write['proposal.json']


def verify(root, *, reconstruct=True):
    for name, expected in read(root / 'manifest.json')['files'].items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or (root / p).is_symlink() or sha(root / p) != expected:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Frozen implementation drift')
    if reconstruct and any(read(root / n) != v for n, v in values().items()):
        raise ValueError('Reconstructed input drift')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
