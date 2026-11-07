"""Unapproved fixed-card conditional-uncertainty diagnostic; no service backend."""
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


seed = load('partial_information_seed', ROOT / 'benchmarks/fresh-decision-v1/plan.py')
read, sha, digest = seed.read, seed.sha, seed.digest
choice_reader, transcript = seed.choice_reader, seed.transcript
MODEL, AS_OF, BUDGET, CAP = seed.MODEL, seed.AS_OF, seed.BUDGET, 37
PROFILES, VIEWS = seed.PROFILES, ('card', 'tail')
PARENT = ROOT / 'benchmarks/fresh-decision-v1/measured.synthetic.json'
PARENT_SHA = 'c54bd485cdb7002dafc825679116fb64fd5aa5741aef1975e52891c940007781'
SPECS = (('context_missing', (0, 1), True), ('override_missing', (1, 2), True),
         ('choice_agrees', (0, 2), True), ('complete_anchor', (2,), False))


def common_choice(values):
    if not values or any(value == 'U' or not isinstance(value, str) or not value for value in values):
        raise ValueError('Every candidate needs a previously licensed complete choice')
    return values[0] if len(set(values)) == 1 else 'U'


def _build_inputs():
    if PARENT.is_symlink() or sha(PARENT) != PARENT_SHA:
        raise ValueError('Original measured parent changed')
    data = read(PARENT)
    if data['kind'] != 'actual_fresh_decision45' or data['status']['scope_closed'] is not True:
        raise ValueError('Wrong parent study')
    original = data['prepared_files']
    sources = original['sources.json']
    reference = {(r['person'], r['case']): r for r in original['reference.private.json']}
    parents = {}
    for record in data['records']:
        if record['kind'] == 'extract' and record['artifact'] is not None:
            key = '%s/g%d' % (record['profile'], record['generation_repeat'])
            if key in parents:
                raise ValueError('Duplicate parent')
            artifact = record['artifact']
            if (artifact['profile'] != record['profile'] or
                    artifact['generation_repeat'] != record['generation_repeat'] or
                    artifact['characters'] != len(artifact['prompt']) or
                    artifact['source_sha256'] != digest(sources[record['profile']]) or
                    not 0 < len(artifact['prompt']) <= BUDGET):
                raise ValueError('Original parent inconsistent')
            parents[key] = {'profile': record['profile'], 'parent_generation': record['generation_repeat'],
                            'prompt': artifact['prompt'], 'characters': artifact['characters'],
                            'source_sha256': artifact['source_sha256'], 'prompt_sha256': digest(artifact['prompt'])}
    if set(parents) != {'%s/g%d' % (pid, g) for pid in PROFILES for g in (0, 1)}:
        raise ValueError('All eight original parents required; no selection')
    queries, rows, evidence = [], [], []
    for di, domain in enumerate(seed.corpus.DOMAINS):
        facts = (domain['base'] + '；例外条件与后来补充的完整约定均未发生。',
                 domain['exception'] + '；明确未满足后来补充的完整约定。',
                 domain['exception'] + '；同时，' + domain['override'] + '；这些条件均完整成立。')
        for ci, (cohort, candidates, primary) in enumerate(SPECS):
            if len(set(candidates)) != len(candidates):
                raise ValueError('Repeated possibility')
            index = di * 4 + ci
            opaque_id = 'q%02d' % ((index * 7 + 3) % 16 + 1)
            task = (domain['name'] + '。以下列出全部可能的完整情境，实际恰好是其中一种，暂不知是哪一种。'
                    '只问在目前信息下，本人是否已有唯一能确定的完整方案选择。'
                    '只有每个可能情境的来源依据都指向同一选项时才返回该选项，否则返回U。'
                    '不要猜实际是哪种情境，也不要替本人在可能情境之间作选择。\n' +
                    '\n'.join('候选情境%d：%s' % (i + 1, facts[s]) for i, s in enumerate(candidates)))
            for order in (0, 1):
                queries.append({'id': opaque_id + ('_ab' if order == 0 else '_ba'), 'scenario': task,
                                'options': dict(zip(('A', 'B'), domain['actions'] if order == 0 else reversed(domain['actions'])))})
            for pid in PROFILES:
                originals = [reference[pid, domain['id'] + '_' + str(s)] for s in candidates]
                values = [r['gold'] for r in originals]
                gold = common_choice(values)
                case = domain['id'] + '_' + cohort
                rows.append({'person': pid, 'case': case, 'query_ids': [opaque_id + '_ab', opaque_id + '_ba'],
                             'gold': gold, 'personal_known': gold != 'U', 'derived_known': primary and gold != 'U',
                             'stratum': 'preference', 'cohort': cohort, 'primary': primary})
                evidence.append({'person': pid, 'case': case, 'original_cases': [r['case'] for r in originals],
                                 'previous_licensed_choices': values, 'common_choice': gold,
                                 'rule': 'singleton consequence only; disagreement U; no unknown constituent permitted'})
    # Reorder opaque query pairs without using their reference labels.
    pairs = [queries[i:i + 2] for i in range(0, len(queries), 2)]
    queries = [q for i in range(16) for q in pairs[(i * 5 + 7) % 16]]
    return {'sources': sources, 'parents': parents, 'queries': {'all': queries},
            'rows': rows, 'reference_derivation': evidence}


@lru_cache(maxsize=1)
def _serialized_inputs(fingerprint):
    if fingerprint != PARENT_SHA:
        raise ValueError('Foreign parent fingerprint')
    return json.dumps(_build_inputs(), ensure_ascii=False)


def inputs():
    # Recheck bytes on every use;copy cached derived values,never mutable state.
    if PARENT.is_symlink() or sha(PARENT) != PARENT_SHA:
        raise ValueError('Original measured parent changed')
    return json.loads(_serialized_inputs(PARENT_SHA))


def slots():
    selected = [s for s in seed.slots() if s['kind'] != 'extract']
    return [{**s, 'slot': i + 1} for i, s in enumerate(selected)]


def material(slot):
    if slot not in slots() or slot['kind'] != 'read':
        raise ValueError('Outside fixed-reader schedule')
    data = inputs()
    prompt = data['parents']['%s/g%d' % (slot['profile'], slot['generation_repeat'])]['prompt']
    raw = transcript(data['sources'][slot['profile']])
    if len(raw) <= BUDGET:
        raise ValueError('Source shorter than ceiling')
    return prompt if slot['view'] == 'card' else raw[-len(prompt):]


def request(slot):
    if slot not in slots():
        raise ValueError('Outside frozen37schedule')
    data = inputs()
    text = '' if slot['kind'] == 'none' else transcript(data['sources'][slot['profile']]) if slot['kind'] == 'full' else material(slot)
    req = choice_reader.make_request(text, data['queries']['all'], as_of=AS_OF,
                                     answer_format='text', reader_mode='standard')
    req['prompt'] = seed.repeat.seed.seed.base.base.old.old.COMMON + req['prompt']
    return {'model': MODEL, 'system': seed.repeat.seed.seed.base.base.old.old.grouped_support.SYSTEM, **req}


def implementation():
    files = seed.implementation()
    files['benchmarks/fresh-decision-v1/measured.synthetic.json'] = sha(PARENT)
    files.update({'benchmarks/partial-information-v1/' + p.name: sha(p) for p in HERE.glob('*.py')})
    return dict(sorted(files.items()))


def values():
    data = inputs()
    proposal = {
        'kind': 'unapproved_partial_information37', 'model': MODEL, 'as_of': AS_OF,
        'max_new_local_cli_attempts': CAP, 'stages': {'controls': 5, 'fixed_card_reads': 16, 'equal_character_tail_reads': 16},
        'fictional_people': 4, 'source_messages': 64, 'fixed_existing_cards': 8,
        'new_extractions': 0, 'public_question_forms': 32,
        'all_person_cases_per_view': 64, 'known_all': 32, 'unknown_all': 32,
        'primary_partial_person_cases_per_view': 48, 'primary_known': 16, 'primary_unknown': 32,
        'anchor_cases_per_view': 16, 'all_anchors_known': True,
        'answers_per_case': 8, 'whole_public_character_cap': BUDGET,
        'reference': 'Join only previously licensed complete cases0,1,2 from the frozen prior reference;all equal gives choice,disagreement U;no unknown constituent or hidden author parameter.',
        'primary': '48partial-information person/cases;report16same-choice knowns and32conflicting-branch unknowns separately;do not count16complete anchors as new partial cases.',
        'controls': 'All16own cases in both orders correct,no missing,and primary-known gain over fresh shared none before any fixed-view read.',
        'reader': 'Same standard prefix/schema;new task explicitly enumerates all possible complete contexts and asks for their unique common choice;no action-to-condition decoder is supplied.',
        'parents': 'All8previous public cards verbatim,no bad-card selection,no raw graphs,old reader outputs/scores or manual repair in requests.',
        'stop': 'Any control,transport,schema/decode,unknownusage,model,input/runtime/guard failure closes remainder;no retry,repair,resume or replenishment.',
        'scope_claim': 'Successful output directory before exclusive single-use intent;intent before backend entry.',
        'fixed_posthoc_diagnostic': True, 'sources_and_cards_consumed': True,
        'new_initial_generation_stability_verified': False, 'independent_holdout': False,
        'independent_semantic_gold_verified': False, 'real_person_fidelity_verified': False,
        'cross_provider_verified': False, 'token_matched_tail': False,
        'production_default_changed': False, 'old_scores_replaced': False, 'old_scopes_reopened': False,
        'approved': False, 'new_service_authority': False, 'measured_results_available': False,
        'aggregate_token_cap': None, 'money_cap': None, 'local_child_timeout_seconds': 180,
        'execution_condition': 'New direct finite37grant and exact published head three-platform CI success.'}
    return {'proposal.json': proposal, 'sources.json': data['sources'], 'parents.public.json': data['parents'],
            'queries.public.json': data['queries'], 'reference.private.json': data['rows'],
            'reference-derivation.private.json': data['reference_derivation'], 'slots.json': slots(),
            'static-requests.json': {str(s['slot']): request(s) for s in slots()},
            'implementation-sha256.json': implementation()}


def prepare(root):
    root = Path(root)
    data = values()
    root.mkdir(exist_ok=False)
    for name, value in data.items():
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (root / 'manifest.json').write_text(json.dumps(
        {'files': {n: sha(root / n) for n in sorted(data)}, 'new_model_calls': 0}, indent=2) + '\n')


def verify(root):
    root = Path(root)
    if root.is_symlink() or (root / 'manifest.json').is_symlink():
        raise ValueError('Input symlink')
    expected, manifest = values(), read(root / 'manifest.json')
    if set(manifest) != {'files', 'new_model_calls'} or type(manifest['new_model_calls']) is not int or manifest['new_model_calls'] != 0:
        raise ValueError('Manifest type differs')
    if set(manifest['files']) != set(expected) or {p.name for p in root.iterdir()} != set(expected) | {'manifest.json'}:
        raise ValueError('Input set differs')
    for name, value in expected.items():
        p = root / name
        if p.is_symlink() or not p.is_file() or sha(p) != manifest['files'][name] or read(p) != value:
            raise ValueError('Input reconstruction differs')
    return True
