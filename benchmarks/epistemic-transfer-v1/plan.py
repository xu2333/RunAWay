"""Prepare unapproved49 source-licensed transfer attempts, with no external decoder."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


base = load('epistemic_prior_plan', HERE.parent / 'long-task-probe-v1/plan.py')
corpus = load('epistemic_corpus', HERE / 'corpus.py')
read, sha, digest, choice_reader = base.read, base.sha, base.digest, base.choice_reader
candidate = base.candidate
PROFILES, METHODS = corpus.PROFILES, ('source-order-v3',)
MODEL, AS_OF, CAP, BUDGET = 'gpt-6.1-sol', '2026-11-02', 49, 1536


def inputs():
    return corpus.build()


def bank(pid):
    if pid in PROFILES or pid == 'shared_all':
        return 'all'
    raise ValueError('Foreign bank')


def parent(slot):
    return slot['profile'], slot['method'], slot['generation']


def cells():
    return [(p, METHODS[0], 0) for p in PROFILES]


def slots():
    jobs = [('none', 'shared_all', None, None, None, None)]
    jobs += [('full', p, None, None, None, None) for p in PROFILES]
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


transcript = base.transcript


def material(pid, prompt, view):
    if pid not in PROFILES or type(prompt) is not str or not 0 < len(prompt) <= BUDGET:
        raise ValueError('Person/card budget differs')
    if view == 'card':
        return prompt
    if view != 'tail':
        raise ValueError('Foreign view')
    raw = transcript(inputs()['sources'][pid])
    if len(raw) <= BUDGET:
        raise ValueError('Full history must exceed memory ceiling')
    return raw[-len(prompt):]


def request(slot, parents=None):
    if slot not in slots():
        raise ValueError('Outside frozen49schedule')
    data = inputs()
    pid = slot['profile']
    if slot['kind'] == 'extract':
        return {'model': MODEL, 'system': base.old.old.grouped_support.SYSTEM,
                **candidate.make_request(data['sources'][pid], BUDGET)}
    if slot['kind'] == 'none':
        text = ''
    elif slot['kind'] == 'full':
        text = transcript(data['sources'][pid])
    else:
        if parent(slot) not in (parents or {}):
            return None
        own = next(s for s in slots() if s['kind'] == 'extract' and parent(s) == parent(slot))
        text = material(pid, bind(own, parents[parent(slot)])['prompt.md'], slot['view'])
    # No appended rule family, hidden policy, reference or external decoder.
    req = choice_reader.make_request(text, data['queries']['all'], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': base.old.old.grouped_support.SYSTEM, **req,
            'prompt': base.old.old.COMMON + req['prompt']}


def implementation():
    return dict(sorted({**base.implementation(), **{str(p.relative_to(ROOT)): sha(p)
                        for p in HERE.glob('*.py')}}.items()))


def values():
    data = inputs()
    text_chars = {p: sum(len(s['text']) for s in src['sources']) for p, src in data['sources'].items()}
    if min(text_chars.values()) <= BUDGET:
        raise ValueError('Text alone must exceed whole-card ceiling')
    proposal = {'kind': 'unapproved_epistemic_transfer49', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 9, 'source_only_extractions': 8,
            'card_reads': 16, 'own_equal_character_tail_reads': 16},
        'source_messages': 176, 'source_text_characters': text_chars,
        'full_transcript_characters': {p: len(transcript(src)) for p, src in data['sources'].items()},
        'primary_cases_per_view': 120, 'known': 58, 'unknown': 62, 'personal_known': 48,
        'structural_known': 10, 'derived_known': 31, 'guarantee_withdrawal_sensitive': 20,
        'unique_public_forms': 30, 'person_form_combinations': 240,
        'whole_public_character_cap': BUDGET, 'generations_per_profile': 1,
        'reads_per_view': 2, 'option_orders_per_read': 2, 'answers_per_case_per_view': 4,
        'control': 'Shared none once;each own full15/15bothorders,no missing,personal-known gain over shared none.All8fulls before extract10.Any failure closes scope.',
        'reference': 'Consensus over every source-compatible policy and missing-feature completion.For active finite-family guarantee use4listed tables;after withdrawal use all16binary policies.Hidden generating truth never resolves unidentifiable choices.Out-of-scope U.',
        'source_only': 'Own sources,budget,fixed header/guide/guidance/schema only.No questions,reference,hidden tables,author parameters,old cards/responses/scores or manual bindings.',
        'reader': 'Own complete card or exact own-card-length suffix of the role-labelled transcript,plus common30public forms.No externally appended decoder or family definitions.Full source carries its own definitions.',
        'endpoint': 'Each view120fixed cases:one producer/person,two reads/two orders all correct.Slice direct/derived/structural/personal,cohort and withdrawal-sensitive cases;do not hide known losses behind62unknowns.',
        'invalid_product': 'Skip only own4card/tailreads;own15cases staymissing in both120case denominators.No repair/replacement/truncation.',
        'fatal': 'Control,transport,wire/schema,decode,unknownusage,model,runtime,inputhash or ownedguard closes remainder.Intent counts if receipt unknown.',
        'all_extractions_before_reads': True, 'aggregate_token_cap': None, 'money_cap': None,
        'timeout_per_local_child_seconds': 180, 'max_nominal_timeout_sum_seconds': 8820,
        'not_aggregate_duration_spend_or_upstream_cancellation_cap': True,
        'retry': False, 'repair': False, 'resume': False, 'replenishment': False,
        'unused_slots_expire': True, 'external_reader_decoder': False,
        'hidden_policy_is_reference_truth': False, 'independent_holdout': False,
        'independent_semantic_acceptance': False, 'generation_stability_verified': False,
        'real_person_fidelity_verified': False, 'approved': False,
        'new_service_authority': False, 'production_default_changed': False}
    return {'proposal.json': proposal, 'sources.json': data['sources'],
        'queries.public.json': data['queries'], 'author-reference.private.json': data['rows'],
        'author-parameters.private.json': data['author_parameters'], 'design.json': data['design'],
        'slots.json': slots(), 'static-requests.json': {s['key']: request(s) for s in slots() if s['kind'] != 'read'},
        'dynamic-rules.json': {'slots': [s for s in slots() if s['kind'] == 'read'],
            'builder': 'benchmarks/epistemic-transfer-v1/plan.py:request', 'own_valid_parent_only': True},
        'implementation-sha256.json': implementation()}


def prepare(destination):
    contents = values()
    destination.mkdir(parents=True, exist_ok=False)
    for name, value in contents.items():
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'manifest.json').write_text(json.dumps({'files': {n: sha(destination / n)
        for n in sorted(contents)}, 'new_model_calls': 0}, indent=2) + '\n', encoding='utf-8')
    return contents['proposal.json']


def verify(root, *, reconstruct=True):
    for name, expected in read(root / 'manifest.json')['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or (root / path).is_symlink() or sha(root / path) != expected:
            raise ValueError('Frozen input drift')
    if read(root / 'implementation-sha256.json') != implementation():
        raise ValueError('Implementation drift')
    if reconstruct and any(read(root / n) != v for n, v in values().items()):
        raise ValueError('Reconstructed input drift')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
