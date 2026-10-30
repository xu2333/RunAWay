"""Zero-model calibration of decision-target boundaries and corrupted views."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway import grouped_support as grouped, choice_reader
from runaway.profile import validate_sources
spec = importlib.util.spec_from_file_location('decision_target_oracle', HERE / 'oracle.py')
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
spec = importlib.util.spec_from_file_location('source_only_decision_target_candidate', HERE / 'prototype/decision_targets.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate(packet):
    if (packet['kind'] != 'authored_decision_target_development_not_holdout'
            or packet['facts_and_targets_are_author_annotations_not_NLU'] is not True
            or packet['real_model_performance_measured'] is not False
            or packet['independent_semantic_acceptance'] is not False):
        raise ValueError('Development truth/claim differs')
    validate_sources(packet['sources'])
    if len(packet['sources']['sources']) != 14 or len(packet['queries']) != 16:
        raise ValueError('Frozen development envelope differs')
    ids = [q['public']['id'] for q in packet['queries']]
    if len(set(ids)) != 16:
        raise ValueError('Duplicate query')
    for query in packet['queries']:
        if query['stratum'] not in ('preference', 'execution'):
            raise ValueError('Unknown decision stratum')
        if query['expected'] != 'U' and query['expected'] not in query['public']['options'].values():
            raise ValueError('Expected action not offered')
    for target in {r['target'] for r in packet['rules']}:
        oracle.active_rules(packet, target)
    return packet


def public_queries(packet):
    return copy.deepcopy([query['public'] for query in packet['queries']])


def reader_request(material, packet):
    return choice_reader.make_request(material, public_queries(packet), as_of='2026-10-30', answer_format='text', reader_mode='standard')


def calibrate(packet):
    validate(packet)
    variants = {'intact_typed_view': copy.deepcopy(packet)}
    erased = copy.deepcopy(packet)
    erased['rules'] = [r for r in erased['rules'] if not r['target'].endswith('_execution')]
    variants['erase_execution_boundaries'] = erased
    merged = copy.deepcopy(packet)
    for rule in merged['rules']:
        rule['target'] = 'all_questions'
    for query in merged['queries']:
        query['target'] = 'all_questions'
    variants['merge_unrelated_targets'] = merged
    loosened = copy.deepcopy(packet)
    next(r for r in loosened['rules'] if r['id'] == 'poster')['requires'] = {}
    variants['remove_real_choice_prerequisite'] = loosened
    conflict = copy.deepcopy(packet)
    conflict['rules'] = [r for r in conflict['rules'] if r['id'] != 'lamp_cold']
    variants['drop_one_real_conflict'] = conflict
    roles = copy.deepcopy(packet)
    for source in roles['sources']['sources']:
        if source['role'] in ('assistant', 'tool'):
            source['role'] = 'user'
    variants['launder_nonuser_roles'] = roles
    false = copy.deepcopy(packet)
    for query in false['queries']:
        keys = {key for rule in false['rules'] if rule['target'] == query['target'] for key in rule['requires']}
        for key in keys:
            query['facts'].setdefault(key, False)
    variants['missing_condition_as_false'] = false
    branch = copy.deepcopy(packet)
    branch['rules'] = [r for r in branch['rules'] if r['id'] != 'discussion_no_room']
    variants['drop_covered_consensus_branch'] = branch
    return {name: oracle.score(value) for name, value in variants.items()}


def check():
    raw = (HERE / 'development.synthetic.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != (HERE / 'development.synthetic.sha256').read_text().strip():
        raise ValueError('Development packet changed')
    packet = validate(json.loads(raw))
    results = calibrate(packet)
    if results['intact_typed_view']['groups']['joint'] != {'planned': 16, 'correct': 16}:
        raise ValueError('Authored logical truth differs')
    if any(v['groups']['joint']['correct'] == 16 for name, v in results.items() if name != 'intact_typed_view'):
        raise ValueError('Damaged view escaped calibration')
    req = candidate.make_request(packet['sources'], 1536)
    original = candidate.base.make_request(packet['sources'], 1536)
    if req['schema'] != original['schema']:
        raise ValueError('Candidate changes schema')
    marker = '\nEXTRACTION_INPUT_JSON:\n'
    if req['prompt'].split(marker, 1)[1] != original['prompt'].split(marker, 1)[1]:
        raise ValueError('Candidate changes source envelope')
    answer = read(HERE / 'examples/partial-answer.synthetic.json')
    actual = candidate.bind(answer, packet['sources'], 1536)['prompt.md']
    baseline_render = grouped.bind(answer, packet['sources'], 1536)['prompt.md']
    if actual != baseline_render or actual != (HERE / 'examples/partial-card.txt').read_text(encoding='utf-8'):
        raise ValueError('Worked example changes renderer or source binding')
    compact_answer = read(HERE / 'examples/partial-answer-compact.synthetic.json')
    compact = candidate.bind(compact_answer, packet['sources'], 1536)['prompt.md']
    if compact != grouped.bind(compact_answer, packet['sources'], 1536)['prompt.md'] or compact != (HERE / 'examples/partial-card-compact.txt').read_text(encoding='utf-8'):
        raise ValueError('Compact example changes renderer or source binding')
    body = json.loads(reader_request(actual, packet)['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
    if set(body) != {'material', 'queries'} or body['queries'] != public_queries(packet):
        raise ValueError('Private target/facts leaked to reader')
    return {'new_model_calls': 0, 'candidate_model_effect_measured': False,
            'production_default_changed': False, 'partial_manual_example_characters': len(actual),
            'compact_manual_example_characters': len(compact),
            'logical_calibration': {name: value['groups'] for name, value in results.items()},
            'independent_semantic_or_holdout_claim': False}


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False))
