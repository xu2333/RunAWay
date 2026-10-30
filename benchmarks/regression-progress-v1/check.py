"""Portable replay of five closed synthetic studies. No inference or network."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway import grouped_support as grouped, choice_reader
from runaway.card import canonical
from runaway.constraint_extract import parse_answer, check as schema_check
from runaway.profile import validate_sources
spec = importlib.util.spec_from_file_location('regression_policy_scope', HERE / 'prototype/policy_scope.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

COMMON = '仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'
TAIL_NOTE = '原始多角色记录尾部，开头可能被截断；只把完整标明user的决定作为证据。\n'
MODEL = 'gpt-6.1-sol'
MODULES = ('card', 'choice_reader', 'choice_contract', 'constraint_extract', 'portable', 'profile',
           'prompt_codec', 'scope_rows', 'grouped_support', 'support_extract', 'text_integrity')


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def usage(rows):
    if type(rows) is not list or not rows:
        raise ValueError('Usage rows missing')
    fields = ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'reasoning_output_tokens')
    total = Counter()
    for row in rows:
        if type(row) is not dict or any(type(row.get(k)) is not int or row[k] < 0 for k in fields[:2]):
            raise ValueError('Unknown mandatory usage')
        if any(type(row.get(k, 0)) is not int or row.get(k, 0) < 0 for k in fields):
            raise ValueError('Invalid usage')
        if row.get('cached_input_tokens', 0) > row['input_tokens'] or row.get('reasoning_output_tokens', 0) > row['output_tokens']:
            raise ValueError('Subset tokens exceed total')
        total.update({k: row.get(k, 0) for k in fields})
    result = dict(total)
    result['total_tokens'] = result['input_tokens'] + result['output_tokens']
    return result


def counts(rows, answers):
    out = {k: {'planned': 0, 'correct': 0, 'missing': 0} for k in ('joint', 'known', 'unknown', 'personal_known')}
    for row in rows:
        values = [answers.get(row['person'], {}).get(q) for q in row['query_ids']]
        missing = any(v is None for v in values)
        correct = not missing and all(v == row['gold'] for v in values)
        for key in ['joint', 'unknown' if row['gold'] == 'U' else 'known'] + (['personal_known'] if row['personal_known'] else []):
            out[key]['planned'] += 1
            out[key]['correct'] += int(correct)
            out[key]['missing'] += int(missing)
    return out


def expected_slots(kind, people):
    if kind in ('forward', 'new_worlds'):
        pairs = [('none', 'shared')] + [('full', p) for p in people]
        if kind == 'new_worlds':
            pairs += [('extract', p) for p in people]
        for rotation in range(3):
            pairs += [(('own', 'tail', 'wrong')[(rotation + i) % 3], p) for i, p in enumerate(people)]
        if kind == 'new_worlds':
            pairs += [('full_attack', p) for p in people] + [('own_attack', p) for p in people]
    elif kind == 'single_repair':
        pairs = [(g, people[0]) for g in ('none', 'full', 'baseline_first', 'baseline_second', 'extract', 'candidate_first', 'candidate_second')]
    elif kind == 'remaining_h':
        pairs = [('none', 'shared')] + [('full', p) for p in people]
        for group, order in [('baseline_first', people), ('baseline_second', reversed(people)),
                             ('extract', people), ('candidate_first', people), ('candidate_second', reversed(people))]:
            pairs += [(group, p) for p in order]
    else:
        raise ValueError('Unknown finite study')
    return [(i + 1, group, person) for i, (group, person) in enumerate(pairs)]


def request(study, group, person, cards):
    sources, queries = study['sources'], study['queries']
    if group == 'extract':
        make = grouped.make_request if study['kind'] == 'new_worlds' else policy.make_request
        return {'model': MODEL, 'system': grouped.SYSTEM, **make(sources[person], 1536)}
    if group == 'none':
        material = ''
    elif group in ('full', 'full_attack'):
        material = canonical(sources[person])
    else:
        owner = person
        if group == 'wrong':
            people = study['people']
            owner = people[(people.index(person) + 1) % len(people)]
        if group.startswith('baseline') or study['kind'] == 'forward':
            card = study['initial_cards'][owner]
        else:
            card = cards[owner]
        material = card['prompt']
        if group == 'tail':
            raw = '\n'.join(s['role'] + ': ' + s['text'] for s in sources[person]['sources'])
            material = TAIL_NOTE + raw[-(len(material) - len(TAIL_NOTE)):]
    if group in ('full_attack', 'own_attack'):
        material += study['attack_attachment']
    req = choice_reader.make_request(material, queries, as_of=study['as_of'], answer_format='text', reader_mode='standard')
    return {'model': MODEL, 'system': grouped.SYSTEM, **req, 'prompt': COMMON + req['prompt']}


def repeated(rows, first, second):
    result = {'planned': len(rows), 'correct': 0, 'missing': 0, 'disagreeing_cases': 0}
    for row in rows:
        a = [first.get(row['person'], {}).get(q) for q in row['query_ids']]
        b = [second.get(row['person'], {}).get(q) for q in row['query_ids']]
        missing = any(v is None for v in a + b)
        result['missing'] += int(missing)
        result['correct'] += int(not missing and all(v == row['gold'] for v in a + b))
        result['disagreeing_cases'] += int(not missing and a != b)
    return result


def replay_study(study, expected_shape):
    people, sources, queries, rows = [study[k] for k in ('people', 'sources', 'queries', 'reference_rows')]
    if (len(people), len(queries), len(rows), len(study['records'])) != expected_shape:
        raise ValueError('Frozen denominator/call shape differs')
    if study['whole_card_cap'] != 1536 or study['requested_model'] != MODEL or study['new_service_authority'] is not False:
        raise ValueError('Budget/model/authority changed')
    if set(people) != set(sources) or len(people) != len(set(people)):
        raise ValueError('Profile inventory differs')
    for key, value in [('reference', rows), ('sources', sources), ('queries', queries), ('initial_cards', study['initial_cards'])]:
        if digest(value) != study[key + '_sha256']:
            raise ValueError('Frozen ' + key + ' snapshot differs')
    for source in sources.values():
        validate_sources(source)
    qindex = {q['id']: q for q in queries}
    if len(qindex) != len(queries) or len({(r['person'], r['case']) for r in rows}) != len(rows):
        raise ValueError('Duplicate query/case')
    for row in rows:
        a, b = [qindex[q] for q in row['query_ids']]
        if a['scenario'] != b['scenario'] or list(a['options'].values()) != list(reversed(list(b['options'].values()))):
            raise ValueError('Option pair differs')
        if row['gold'] != 'U' and row['gold'] not in a['options'].values():
            raise ValueError('Known action not offered')
        if row['gold'] == 'U' and row['personal_known']:
            raise ValueError('Unknown cannot be personal-known')
        source_index = {s['id']: s for s in sources[row['person']]['sources']}
        for anchor in row['support']:
            s = source_index[anchor['source_id']]
            if s['role'] != 'user' or anchor['quote'] not in s['text']:
                raise ValueError('Reference source quote/role differs')
    for pid, card in study['initial_cards'].items():
        if card['characters'] != len(card['prompt']) or not 0 < card['characters'] <= 1536 or card['source_sha256'] != digest(sources[pid]):
            raise ValueError('Initial card/source binding differs')
    slots = expected_slots(study['kind'], people)
    if [(r['slot'], r['group'], r['person']) for r in study['records']] != slots:
        raise ValueError('Reordered/repeated slot')
    if len({r['execution_id'] for r in study['records']}) != len(slots):
        raise ValueError('Repeated execution ID')
    answers, cards, total = {}, {}, Counter()
    for rec in study['records']:
        group, person = rec['group'], rec['person']
        if rec['state'] != 'completed' or rec['backend'] != 'codex' or rec['requested_model'] != MODEL:
            raise ValueError('Actual completed observation differs')
        if group not in ('none', 'full'):
            full = counts(rows, answers.get('full', {}))
            none = counts(rows, {p: answers.get('none', {}).get('shared', answers.get('none', {}).get(p, {})) for p in people})
            if full['joint']['correct'] != len(rows) or full['personal_known']['correct'] <= none['personal_known']['correct']:
                raise ValueError('Reader/producer admitted without controls')
        req = request(study, group, person, cards)
        if req != rec['request'] or digest(req) != rec['request_sha256']:
            raise ValueError('Request/source/card/query binding differs')
        if hashlib.sha256(rec['raw'].encode()).hexdigest() != rec['raw_text_sha256']:
            raise ValueError('Raw text changed')
        measured_usage = usage(rec['usage_rows'])
        if measured_usage != rec['usage']:
            raise ValueError('Usage counters differ')
        total.update(measured_usage)
        answer = parse_answer(rec['raw'])
        schema_check(answer, req['schema'])
        if group == 'extract':
            files = grouped.bind(answer, sources[person], 1536)
            expected_card = {'prompt': files['prompt.md'], 'characters': len(files['prompt.md']), 'source_sha256': digest(sources[person])}
            if rec.get('card') != expected_card or not 0 < expected_card['characters'] <= 1536:
                raise ValueError('Measured card/binder differs')
            cards[person] = expected_card
        else:
            choice_reader.decode_response(queries, answer, answer_format='text', reader_mode='standard')
            answers.setdefault(group, {})[person] = answer
    status = study['status']
    if status['status'] != 'complete' or not status['scope_closed'] or status['missing_usage'] != 0 or status['unused_slots_expire'] != 0:
        raise ValueError('Closed actual scope differs')
    if dict(total) != status['known_usage']:
        raise ValueError('Study cost ledger differs')
    groups = {}
    for group, values in answers.items():
        by_person = {p: values.get('shared', values.get(p, {})) for p in people}
        groups[group] = counts(rows, by_person)
    if 'wrong' in answers:
        donor = {p: people[(people.index(p) + 1) % len(people)] for p in people}
        groups['wrong_against_actual_donor'] = counts(rows, {donor[p]: a for p, a in answers['wrong'].items()})
    repeats = {prefix: repeated(rows, answers[prefix + '_first'], answers[prefix + '_second'])
               for prefix in ('baseline', 'candidate') if prefix + '_first' in answers}
    return {'groups': groups, 'repeats': repeats, 'calls': len(slots), 'known_usage': dict(total),
            'cards': cards, 'answers': answers, 'old_references_rewritten': False}


def verify_citations(semantics, report, allow_question):
    question = semantics['question']
    roles = Counter()
    if set(report) != set(semantics['episodes']):
        raise ValueError('Neutral profile set differs')
    for pid, value in report.items():
        index = {s['id']: s for s in semantics['episodes'][pid]}
        for anchor in value['source_evidence']:
            source_id, quote = anchor['source_id'], anchor['quote']
            if source_id in index:
                source = index[source_id]
                texts, role = [source['text']], source['role']
            elif allow_question and source_id == question['id']:
                texts, role = [question['scenario'], *question['options']], 'question'
            else:
                raise ValueError('Question domain omitted or unknown ID')
            if not quote or not any(quote in text for text in texts):
                raise ValueError('Nonliteral citation')
            roles[role] += 1
    return dict(roles)


def replay(data, semantics):
    if (data['kind'] != 'consumed_actual_regression_progress' or data['all_sources_fictional'] is not True
            or data['developer_visible'] is not True or data['independent_holdout'] is not False
            or data['real_person_or_cross_vendor_fidelity_verified'] is not False
            or data['production_default_changed'] is not False or data['new_service_authority'] is not False):
        raise ValueError('Evidence claim changed')
    expected_runtime = {'runaway/' + m + '.py' for m in MODULES}
    if set(data['runtime_sha256']) != expected_runtime:
        raise ValueError('Runtime inventory differs')
    for rel, expected in data['runtime_sha256'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
            raise ValueError('Measured module changed: ' + rel)
    shapes = {'forward': (4, 40, 80, 17), 'new_worlds': (4, 48, 96, 29),
              'repair': (1, 48, 24, 7), 'h17': (1, 80, 40, 7), 'remaining_h': (3, 80, 120, 19)}
    if set(data['studies']) != set(shapes):
        raise ValueError('Study inventory differs')
    results = {name: replay_study(data['studies'][name], shape) for name, shape in shapes.items()}
    # Frozen initial cards must be traceable to published or earlier artifacts.
    for pid, card in data['studies']['forward']['initial_cards'].items():
        expected = ROOT / 'benchmarks/source-review-comparison-v1/cards' / ('grouped-v1-' + pid + '.txt')
        if expected.read_text(encoding='utf-8') != card['prompt']:
            raise ValueError('Historical baseline provenance differs')
    if data['studies']['repair']['initial_cards']['j39'] != results['new_worlds']['cards']['j39']:
        raise ValueError('j39 old-card provenance differs')
    for name in ['h17', 'remaining_h']:
        for pid, card in data['studies'][name]['initial_cards'].items():
            if card != data['studies']['forward']['initial_cards'][pid]:
                raise ValueError('h baseline provenance differs')
    if (semantics['independent_semantic_acceptance'] is not False
            or semantics['original_w14_labels_or_93of96_changed'] is not False
            or semantics['same_requested_model'] is not True):
        raise ValueError('Model opinions cannot self-accept references')
    opinions = semantics['opinions']
    if len(opinions) != 2 or [o['original_controller_state'] for o in opinions] != ['failed', 'completed']:
        raise ValueError('Original citation failure reclassified')
    try:
        verify_citations(semantics, opinions[0]['report'], False)
    except ValueError:
        pass
    else:
        raise ValueError('Original omitted-domain failure not reproduced')
    for opinion in opinions:
        if verify_citations(semantics, opinion['report'], True) != {'user': 12, 'question': 4}:
            raise ValueError('Citation evidence differs')
        if any(v['sufficiency'] != 'insufficient' or v['action'] != 'U' for v in opinion['report'].values()):
            raise ValueError('Original opinion categories changed')
        if usage([opinion['usage']]) != opinion['usage']:
            raise ValueError('Neutral token ledger differs')
    new_world = data['studies']['new_worlds']
    question = next(q for q in new_world['queries'] if q['id'] == 'w14_a')
    if semantics['question']['scenario'] != question['scenario'] or semantics['question']['options'] != list(question['options'].values()):
        raise ValueError('Neutral question differs from disputed case')
    for pid, episode in semantics['episodes'].items():
        index = {s['id']: s for s in new_world['sources'][pid]['sources']}
        if any(source != index.get(source['id']) for source in episode):
            raise ValueError('Neutral source differs from original trajectory')
    calls = sum(r['calls'] for r in results.values())
    tokens = sum(r['known_usage']['total_tokens'] for r in results.values())
    neutral_tokens = sum(o['usage']['total_tokens'] for o in opinions)
    h_rows = data['studies']['h17']['reference_rows'] + data['studies']['remaining_h']['reference_rows']
    required = {(r['person'], r['case']) for r in h_rows}
    required.update((r['person'], r['case']) for r in new_world['reference_rows'] if r['person'] != 'j39')
    measured = set()
    for name in ['h17', 'remaining_h']:
        study, result = data['studies'][name], results[name]
        for row in study['reference_rows']:
            if row['person'] in result['cards'] and all(q in result['answers'].get('candidate_first', {}).get(row['person'], {}) for q in row['query_ids']):
                measured.add((row['person'], row['case']))
    if len(required) != 232 or len(measured) != 160 or not measured <= required:
        raise ValueError('Revised coverage accounting differs')
    affected = {r['person'] for r in new_world['reference_rows'] if r['case'] == 'w14'}
    return {'studies': results, 'actual_choice_calls': calls, 'neutral_opinion_calls': 2,
            'known_choice_tokens': tokens, 'known_neutral_tokens': neutral_tokens,
            'revised_required_cases': len(required), 'revised_measured_cases': len(measured), 'revised_remaining_cases': len(required-measured),
            'w14_affected_people': len(affected), 'w14_reference_accepted': False,
            'new_model_calls': 0, 'production_default_changed': False, 'project_goal_complete': False}


def check():
    values = []
    for filename in ['observed.synthetic.json', 'semantic-dispute.synthetic.json']:
        raw = (HERE / filename).read_bytes()
        expected = (HERE / filename.replace('.json', '.sha256')).read_text().strip()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Published fixture changed')
        if re.search(rb'/Users/|Documents/ChatGPT|direct-human-|Bearer\s+[A-Za-z0-9]', raw):
            raise ValueError('Private local/approval metadata in public export')
        values.append(json.loads(raw))
    result = replay(*values)
    expected_cards = {name + '-' + pid + '.txt': card['prompt']
                      for name, study in result['studies'].items() for pid, card in study['cards'].items()}
    actual_cards = {p.name: p.read_text(encoding='utf-8') for p in (HERE / 'cards').glob('*.txt')}
    if expected_cards != actual_cards:
        raise ValueError('Published card text differs')
    return {key: value for key, value in result.items() if key != 'studies'}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False))
