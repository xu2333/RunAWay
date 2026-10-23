"""Replay consumed actual compression observations. No inference or answer repair."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runaway import choice_reader, support_extract
from runaway.card import canonical, digest
from runaway.constraint_extract import parse_answer, check as schema_check
from runaway.prompt_codec import unpack

spec = importlib.util.spec_from_file_location('compression_prior_controls', ROOT / 'benchmarks/natural-controls-v1/check.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
PRIOR_SHA = 'a03b91ad85896922b123bef752ee55c030850891a729d646eff1edfc35e3b286'
TAIL_NOTE = '原始多角色记录尾部，开头可能被截断；只把完整标明user的决定作为证据。\n'


def object_digest(value):
    return digest(canonical(value))


def plan(people):
    if len(people) != 4 or len(set(people)) != 4:
        raise ValueError('Four unique source profiles required')
    pairs = [('extract_v1', p) for p in people]
    for r in range(3):
        pairs += [(('own', 'tail', 'wrong')[(r+i) % 3], p) for i,p in enumerate(people)]
    return [{'slot': i+1, 'group': group, 'person': pid} for i,(group,pid) in enumerate(pairs)]


def donor_map(people):
    return {p: people[(i+1) % len(people)] for i,p in enumerate(people)}


def request(slot, sources, queries, products, people):
    group, pid = slot['group'], slot['person']
    if group == 'extract_v1':
        return dict(support_extract.make_request(sources[pid], 768),
                    model='gpt-6.1-sol', system=support_extract.SYSTEM)
    owner = donor_map(people)[pid] if group == 'wrong' else pid
    if owner not in products:
        return None
    material = products[owner]['prompt']
    if group == 'tail':
        size = len(material)
        raw = '\n'.join(s['role'] + ': ' + s['text'] for s in sources[pid]['sources'])
        if size <= len(TAIL_NOTE) or len(raw) < size-len(TAIL_NOTE):
            raise ValueError('Whole-character-matched tail cannot fit')
        material = TAIL_NOTE + raw[-(size-len(TAIL_NOTE)):]
    result = choice_reader.make_request(material, queries, as_of='2026-10-22',
                                       answer_format='text', reader_mode='standard')
    return dict(result, model='gpt-6.1-sol', system=support_extract.SYSTEM,
                prompt=prior.COMMON+result['prompt'])


def bind(answer, source):
    files = support_extract.bind(answer, source, 768, layout='paragraph')
    return {'prompt': files['prompt.md'], 'characters': len(files['prompt.md']),
            'source_sha256': object_digest(source), 'answer_sha256': object_digest(answer), 'files': files}


def summarize(rows, answers, people, baseline, valid):
    groups = {g: prior.counts(rows, answers.get(g, {})) for g in ('own', 'tail', 'wrong')}
    donors = donor_map(people)
    groups['wrong_against_donor'] = prior.counts(rows, {donors[p]: a for p,a in answers.get('wrong', {}).items()})
    groups['prior_full'] = baseline['groups']['full']
    groups['prior_none'] = baseline['groups']['none']
    perfect = lambda g: groups[g]['joint']['correct'] == len(rows) and groups[g]['joint']['missing'] == 0
    denominator = groups['prior_full']['joint']['correct']-groups['prior_none']['joint']['correct']
    numerator = groups['own']['joint']['correct']-groups['prior_none']['joint']['correct']
    losses = [{**{k:e[k] for k in ('person','case','gold','observed','missing')},
               'type': 'unknown_not_preserved' if e['gold']=='U' else 'known_choice_lost'} for e in groups['own']['errors']]
    return {'groups': groups, 'valid_products': valid, 'planned_products': len(people),
            'strict_retention': baseline['full_qualified'] and valid == len(people) and perfect('own') and perfect('wrong_against_donor'),
            'identity_specificity': perfect('own') and perfect('wrong_against_donor') and groups['wrong']['personal_known']['correct'] < groups['own']['personal_known']['correct'],
            'normalized_accuracy_gain': {'numerator': numerator, 'denominator': denominator,
                'value': numerator/denominator if denominator > 0 else None, 'is_likelihood_RIG': False,
                'definition': '(own_joint - historical_none_joint)/(historical_full_joint - historical_none_joint); always report known and unknown separately'},
            'own_losses': losses, 'uses_historical_qualified_controls': True, 'fresh_holdout': False,
            'human_fidelity_verified': False, 'next_stage_authorized': False,
            'sampling_variability_measured': False, 'developer_visible_corpus': True}


def replay(data, controls):
    if (data['kind'] != 'consumed_actual_naturalistic_synthetic_compression'
            or data['fresh_holdout'] is not False or data['human_fidelity_verified'] is not False
            or data['developer_visible_corpus'] is not True or data['prior_controls_rerun'] is not False):
        raise ValueError('Study claim changed')
    if data['requested_model'] != 'gpt-6.1-sol' or data['as_of'] != '2026-10-22' or data['budget_characters'] != 768:
        raise ValueError('Frozen protocol changed')
    raw_prior = (json.dumps(controls, ensure_ascii=False, indent=2)+'\n').encode()
    if hashlib.sha256(raw_prior).hexdigest() != data['prior_controls_sha256'] or data['prior_controls_sha256'] != PRIOR_SHA:
        raise ValueError('Historical controls changed')
    baseline = prior.replay(controls)
    if not baseline['full_qualified']:
        raise ValueError('Unqualified full-history control')
    expected_paths = {'runaway/'+name+'.py' for name in ('card','choice_reader','constraint_extract','portable','profile','prompt_codec','scope_rows','support_extract','text_integrity')}
    if set(data['runtime_sha256']) != expected_paths:
        raise ValueError('Frozen production runtime inventory changed')
    for path, expected in data['runtime_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen production runtime changed: '+path)
    sources, queries, rows = controls['sources'], controls['queries'], controls['reference']['rows']
    people = list(sources)
    records = data['records']
    slots = plan(people)
    if len(records) != 16 or len({r['execution_id'] for r in records}) != 16:
        raise ValueError('Sixteen independent completed records required')
    products, answers, total = {}, {g:{} for g in ('own','tail','wrong')}, Counter()
    for record,slot in zip(records, slots):
        if {k:record[k] for k in ('slot','group','person')} != slot:
            raise ValueError('Slot order changed')
        if record['simulated'] is not False or record['state'] != 'completed':
            raise ValueError('Only actual completed observations accepted')
        expected = request(slot, sources, queries, products, people)
        if expected is None or expected != record['request'] or object_digest(expected) != record['request_sha256']:
            raise ValueError('Source/product/query request binding changed')
        response = record['response']
        original = (json.dumps(response, ensure_ascii=False, indent=2)+'\n').encode()
        if hashlib.sha256(original).hexdigest() != record['raw_response_sha256']:
            raise ValueError('Original response fingerprint changed')
        provenance = response['provenance']
        if provenance['backend'] != 'codex' or provenance['model_requested'] != data['requested_model']:
            raise ValueError('Backend/model changed')
        actual_usage = prior.usage(provenance)
        if actual_usage != record['usage']:
            raise ValueError('Usage binding changed')
        total.update(actual_usage)
        answer = parse_answer(response['raw']); schema_check(answer, expected['schema'])
        if slot['group'] == 'extract_v1':
            product = bind(answer, sources[slot['person']])
            if product != data['products'][slot['person']]:
                raise ValueError('Actual one-shot product changed')
            files = product['files']
            if (product['characters'] != len(product['prompt']) or product['characters'] > 768
                    or product['prompt'] != files['portable.json']['text']
                    or unpack(product['prompt'], files['encoding.private.json']) != files['expanded.private.md']):
                raise ValueError('Whole public budget or expansion changed')
            products[slot['person']] = product
        else:
            choice_reader.decode_response(queries, answer, answer_format='text', reader_mode='standard')
            answers[slot['group']][slot['person']] = answer
    if set(products) != set(people) or dict(total) != data['known_usage']:
        raise ValueError('Products or total usage changed')
    result = summarize(rows, answers, people, baseline, len(products))
    result.update(attempts=16, status='complete', missing_usage=0)
    if result != data['expected_results']:
        raise ValueError('Frozen scoring result changed')
    return result


def check():
    here = Path(__file__).resolve().parent
    raw = (here/'observed.synthetic.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (here/'observed.sha256').read_text().strip():
        raise ValueError('Recorded fixture changed')
    data = json.loads(raw)
    controls = json.loads((here.parent/'natural-controls-v1/observed.synthetic.json').read_text(encoding='utf-8'))
    result = replay(data, controls)
    return {'status': 'consumed_compression_replay_pass', 'new_model_calls': 0,
            'own_correct': result['groups']['own']['joint']['correct'],
            'tail_correct': result['groups']['tail']['joint']['correct'],
            'wrong_target_correct': result['groups']['wrong']['joint']['correct'],
            'wrong_donor_correct': result['groups']['wrong_against_donor']['joint']['correct'],
            'planned_cells': 56, 'known_tokens': data['known_usage']['total_tokens'],
            'whole_card_characters': {p:v['characters'] for p,v in data['products'].items()},
            'human_fidelity_verified': False, 'fresh_holdout': False}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False))
