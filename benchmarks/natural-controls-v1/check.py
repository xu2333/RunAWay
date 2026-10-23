"""Consumed five-call control replay. Never runs a model or a compact extractor."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from runaway.card import canonical, digest
from runaway import choice_reader, support_extract
from runaway.constraint_extract import parse_answer, check as schema_check
from runaway.profile import validate_sources
COMMON='仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'

def counts(rows, answers):
    result = {key: {'planned': 0, 'correct': 0, 'missing': 0}
              for key in ('joint', 'known', 'unknown', 'personal_known')}
    by_person, by_cohort, errors = {}, {}, []
    for row in rows:
        observed = [answers.get(row['person'], {}).get(q) for q in row['query_ids']]
        missing = any(v is None for v in observed)
        correct = all(v == row['gold'] for v in observed)
        for key in ['joint', 'unknown' if row['gold'] == 'U' else 'known'] + (['personal_known'] if row['personal_known'] else []):
            result[key]['planned'] += 1
            result[key]['correct'] += int(correct)
            result[key]['missing'] += int(missing)
        for table, key in [(by_person, row['person']), (by_cohort, row['cohort'])]:
            item = table.setdefault(key, {'planned': 0, 'correct': 0, 'missing': 0})
            item['planned'] += 1; item['correct'] += int(correct); item['missing'] += int(missing)
        if not correct:
            errors.append({'person': row['person'], 'case': row['case'], 'gold': row['gold'],
                           'observed': observed, 'missing': missing})
    return {**result, 'by_person': by_person, 'by_cohort': by_cohort, 'errors': errors}


def summarize(rows, full, empty):
    groups = {'full': counts(rows, full), 'none': counts(rows, empty)}
    complete = groups['full']['joint']['correct'] == len(rows) and groups['full']['joint']['missing'] == 0
    discriminating = groups['full']['personal_known']['correct'] > groups['none']['personal_known']['correct']
    return {'groups': groups, 'full_qualified': complete and discriminating,
            'full_exact_on_all_planned_cells': complete, 'personal_increment_over_none': discriminating,
            'next_stage_authorized': False, 'compression_accuracy_measured': False,
            'human_fidelity_verified': False, 'developer_visible_corpus': True,
            'unit': 'four fictional source profiles; scene/option cells are dependent'}


def usage(provenance):
    values = provenance.get('usage')
    if type(values) is not list or not values:
        raise ValueError('Known usage required')
    result = Counter()
    fields = ['input_tokens','output_tokens','cached_input_tokens','cache_write_input_tokens','reasoning_output_tokens']
    for row in values:
        if type(row) is not dict or any(type(row.get(k)) is not int or row[k] < 0 for k in fields[:2]):
            raise ValueError('Input/output usage differs')
        if any(type(row.get(k,0)) is not int or row.get(k,0) < 0 for k in fields):
            raise ValueError('Invalid usage component')
        if row.get('cached_input_tokens',0) > row['input_tokens'] or row.get('reasoning_output_tokens',0) > row['output_tokens']:
            raise ValueError('Usage subset exceeds total')
        result.update({k:row.get(k,0) for k in fields})
    value = dict(result)
    value['total_tokens'] = value['input_tokens'] + value['output_tokens']
    return value


def replay(data):
    if (data['kind'] != 'consumed_actual_naturalistic_synthetic_controls'
            or data['fresh_holdout'] is not False or data['human_fidelity_verified'] is not False
            or data['developer_visible_corpus'] is not True):
        raise ValueError('Study claim changed')
    if data['requested_model'] != 'gpt-6.1-sol' or data['as_of'] != '2026-10-22':
        raise ValueError('Frozen model/date changed')
    people = list(data['sources'])
    queries = data['queries'];rows = data['reference']['rows']
    if len(people) != 4 or len(queries) != 28 or len(rows) != 56:
        raise ValueError('Planned denominator changed')
    for source in data['sources'].values():
        validate_sources(source)
    if len({(r['person'],r['case']) for r in rows}) != 56:
        raise ValueError('Duplicate reference cell')
    if any(r['person'] not in people or len(r['query_ids']) != 2 for r in rows):
        raise ValueError('Reference owner/rotations changed')
    by_query = {q['id']:q for q in queries}
    for row in rows:
        a,b = [by_query[qid] for qid in row['query_ids']]
        va,vb = list(a['options'].values()),list(b['options'].values())
        if a['scenario'] != b['scenario'] or vb != va[1:]+va[:1]:
            raise ValueError('Option rotation changed')
        if row['gold'] != 'U' and row['gold'] not in va:
            raise ValueError('Known reference not offered')
        index = {s['id']:s for s in data['sources'][row['person']]['sources']}
        for anchor in row['support']:
            s = index[anchor['source_id']]
            if s['role'] != 'user' or anchor['quote'] not in s['text']:
                raise ValueError('Source reference anchor changed')
    records = data['records']
    slots = [('none','shared')] + [('full',p) for p in people]
    if len(records) != 5 or len({r['execution_id'] for r in records}) != 5:
        raise ValueError('Five independent record IDs required')
    answered = {};total = Counter()
    for i,(record,(group,pid)) in enumerate(zip(records,slots),1):
        if (record['slot'],record['group'],record['person']) != (i,group,pid):
            raise ValueError('Slot mapping changed')
        if record['simulated'] is not False or record['state'] != 'completed':
            raise ValueError('Only completed actual observations accepted')
        material = '' if group == 'none' else canonical(data['sources'][pid])
        request = choice_reader.make_request(material,queries,as_of=data['as_of'],answer_format='text',reader_mode='standard')
        expected = dict(request,model=data['requested_model'],system=support_extract.SYSTEM,prompt=COMMON+request['prompt'])
        if record['request'] != expected or digest(canonical(expected)) != record['request_sha256']:
            raise ValueError('Source/query request binding changed')
        response = record['response'];provenance = response['provenance']
        raw_bytes = (json.dumps(response,ensure_ascii=False,indent=2)+'\n').encode()
        if hashlib.sha256(raw_bytes).hexdigest() != record['raw_response_sha256']:
            raise ValueError('Original response fingerprint changed')
        if provenance['backend'] != 'codex' or provenance['model_requested'] != data['requested_model']:
            raise ValueError('Observed backend/model changed')
        value = usage(provenance)
        if value != record['usage']:
            raise ValueError('Observed usage binding changed')
        total.update(value)
        answer = parse_answer(response['raw'])
        schema_check(answer,expected['schema'])
        choice_reader.decode_response(queries,answer,answer_format='text',reader_mode='standard')
        answered[group,pid] = answer
    if dict(total) != data['known_usage']:
        raise ValueError('Observed usage total changed')
    result = summarize(rows,{p:answered['full',p] for p in people},
                       {p:answered['none','shared'] for p in people})
    result.update(attempts=5,missing_usage=0,status='complete')
    if result != data['expected_results']:
        raise ValueError('Frozen scoring result changed')
    return result


def check():
    here = Path(__file__).resolve().parent
    raw = (here/'observed.synthetic.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (here/'observed.sha256').read_text().strip():
        raise ValueError('Recorded fixture changed')
    data = json.loads(raw);result = replay(data)
    return {'status':'consumed_controls_replay_pass','new_model_calls':0,
            'full_correct':result['groups']['full']['joint']['correct'],
            'none_correct':result['groups']['none']['joint']['correct'],
            'planned_cells':56,'known_tokens':data['known_usage']['total_tokens'],
            'compression_accuracy_measured':False,'human_fidelity_verified':False}


if __name__ == '__main__':
    print(json.dumps(check(),ensure_ascii=False))

