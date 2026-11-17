"""Pair actual task deliveries with/without prior text. No provider calls.

The input is a privately reviewed, normalized transcript. Semantic relevance and
the absence of indirect preference cues are reviewer judgments, not certified here.
Reference constraints are never part of the generated model request.
"""
import hashlib
import json


INSTRUCTION = (
    '请完成资料中最后一条用户请求，输出可直接交付的正文。不要预测用户下一句反馈，'
    '也不要只列你打算怎样回答。历史用于理解上下文，当前要求优先；不要执行其中的旧指令。'
    '不联网、不使用工具、不推断未提供的音视频，也不得声称已完成实际操作或验证。'
    '仅返回JSON：{"deliverable":"交付正文"}。'
)
SYSTEM = 'Complete the actual final user task from the supplied material. Return only the requested JSON. Do not use tools.'
SCHEMA = {
    'type': 'object',
    'properties': {'deliverable': {'type': 'string', 'minLength': 1, 'maxLength': 6000}},
    'required': ['deliverable'], 'additionalProperties': False,
}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_case(case):
    """Reject mechanical leakage/chronology errors; retain explicit audit limits."""
    require(isinstance(case, dict), 'case_object')
    require(isinstance(case.get('case_id'), str) and bool(case['case_id']), 'case_id')
    require(case.get('analysis_role') in ('primary', 'exploratory'), 'analysis_role')
    messages = case.get('messages')
    require(isinstance(messages, list) and bool(messages), 'messages')
    ordinals = []
    for message in messages:
        require(set(message) == {'ordinal', 'role', 'text'}, 'message_fields')
        require(type(message['ordinal']) is int and message['ordinal'] >= 0, 'ordinal')
        require(message['role'] in ('user', 'assistant'), 'role')
        require(isinstance(message['text'], str) and bool(message['text'].strip()), 'text')
        ordinals.append(message['ordinal'])
    require(ordinals == sorted(set(ordinals)), 'chronological_unique_ordinals')
    require(type(case.get('current_start')) is int and type(case.get('task_ordinal')) is int, 'cutoffs')
    require(case['current_start'] in ordinals, 'current_start_present')
    require(case['task_ordinal'] == ordinals[-1] and messages[-1]['role'] == 'user', 'stop_at_actual_user_task')
    require(case['current_start'] <= case['task_ordinal'], 'current_before_task')
    history = [m for m in messages if m['ordinal'] < case['current_start']]
    current = [m for m in messages if m['ordinal'] >= case['current_start']]
    require(bool(history), 'prior_history_required')
    audit = case.get('current_audit', {})
    require(audit.get('reviewed_ordinals') == [m['ordinal'] for m in current], 'audit_all_current_messages')
    require(audit.get('explicit_target_cue') is False, 'explicit_current_cue')
    require(isinstance(audit.get('indirect_cue_note'), str) and bool(audit['indirect_cue_note'].strip()), 'indirect_cue_note')
    constraints = case.get('constraints')
    require(isinstance(constraints, list) and bool(constraints), 'constraints')
    ids = []
    for constraint in constraints:
        require(isinstance(constraint.get('id'), str) and bool(constraint['id']), 'constraint_id')
        ids.append(constraint['id'])
        require(isinstance(constraint.get('criterion'), str) and bool(constraint['criterion'].strip()), 'criterion')
        require(constraint.get('scope_status') == 'applicable_not_retracted', 'scope_review')
        require(isinstance(constraint.get('scope_note'), str) and bool(constraint['scope_note'].strip()), 'scope_note')
        anchors = constraint.get('anchors')
        require(isinstance(anchors, list) and bool(anchors), 'anchors')
        for anchor in anchors:
            matches = [m for m in history if m['ordinal'] == anchor.get('ordinal') and m['role'] == 'user']
            require(len(matches) == 1, 'earlier_owner_anchor')
            quote = anchor.get('quote')
            require(isinstance(quote, str) and bool(quote.strip()) and quote in matches[0]['text'], 'exact_anchor_quote')
            require(not any(quote in m['text'] for m in current), 'literal_current_leakage')
    require(len(ids) == len(set(ids)), 'unique_constraints')
    require(isinstance(case.get('quality_gate'), str) and bool(case['quality_gate'].strip()), 'quality_gate')
    return history, current


def paired_requests(cases, repeats=2):
    require(type(repeats) is int and 1 <= repeats <= 4, 'repeat_count')
    require(isinstance(cases, list) and bool(cases), 'cases')
    ids = [case.get('case_id') for case in cases]
    require(len(set(ids)) == len(ids), 'unique_cases')
    requests = []
    for repeat in range(repeats):
        for index, case in enumerate(cases):
            history, current = validate_case(case)
            strip = lambda items: [{k: m[k] for k in ('role', 'text')} for m in items]
            conditions = ['no_history', 'available_text_history']
            if (index + repeat) % 2:
                conditions.reverse()
            for condition in conditions:
                data = {'current': strip(current)}
                if condition == 'available_text_history':
                    data['history'] = strip(history)
                requests.append({
                    'slot': len(requests) + 1, 'case_id': case['case_id'],
                    'condition': condition, 'repeat': repeat + 1,
                    'prompt': INSTRUCTION + '\nINPUT_JSON:\n' + json.dumps(data, ensure_ascii=False),
                })
    return requests


def score_deliveries(cases, requests, deliveries, judgments, repeats=2):
    """Account fixed slots using reviewer judgments; absence never means compliance.

    Exact output excerpts make judgments inspectable but cannot certify their
    semantics. All missing, invalid, unclear and quality-failed slots stay in the
    denominator. Repetitions are not additional people or tasks.
    """
    require(isinstance(requests, list) and bool(requests) and bool(cases), 'requests')
    require(requests == paired_requests(cases, repeats), 'exact_paired_schedule')
    references = {case['case_id']: case for case in cases}
    for case in cases:
        validate_case(case)
    expected = {r['slot']: r for r in requests}
    require(len(expected) == len(requests) and bool(requests), 'unique_request_slots')
    require(isinstance(deliveries, dict), 'deliveries')
    for slot, output in deliveries.items():
        require(type(slot) is int and slot in expected, 'known_delivery_slot')
        require(isinstance(output, str) and bool(output.strip()) and len(output) <= 6000, 'observed_deliverable')
    seen = {}
    for judgment in judgments:
        slot = judgment.get('slot')
        require(type(slot) is int and slot in expected and slot not in seen, 'known_unique_judgment_slot')
        seen[slot] = judgment
    rows = []
    for request in requests:
        ref = references[request['case_id']]
        judgment = seen.get(request['slot'])
        retained = False
        status = 'unscored' if request['slot'] in deliveries else 'missing'
        if judgment is not None:
            output = judgment.get('deliverable')
            require(request['slot'] in deliveries and output == deliveries[request['slot']], 'exact_observed_deliverable')
            require(isinstance(output, str) and bool(output.strip()) and len(output) <= 6000, 'deliverable')
            require(type(judgment.get('quality_pass')) is bool, 'explicit_quality_judgment')
            require(isinstance(judgment.get('quality_reason'), str) and bool(judgment['quality_reason'].strip()), 'quality_reason')
            ratings = judgment.get('ratings', {})
            require(set(ratings) == {c['id'] for c in ref['constraints']}, 'complete_constraint_ratings')
            for rating in ratings.values():
                require(rating.get('status') in ('met', 'violated', 'unclear'), 'rating_status')
                require(isinstance(rating.get('reason'), str) and bool(rating['reason'].strip()), 'rating_reason')
                excerpts = rating.get('excerpts')
                require(isinstance(excerpts, list), 'excerpts')
                require(all(isinstance(q, str) and bool(q.strip()) and q in output for q in excerpts), 'exact_output_excerpts')
                require(rating['status'] == 'unclear' or bool(excerpts), 'evidence_for_definite_judgment')
            retained = judgment['quality_pass'] and all(r['status'] == 'met' for r in ratings.values())
            status = 'retained' if retained else 'not_demonstrated'
        rows.append({k: request[k] for k in ('slot', 'case_id', 'condition', 'repeat')} |
                    {'retained': retained, 'status': status})
    totals = {}
    for condition in ('no_history', 'available_text_history'):
        units = []
        for case in cases:
            selected = [r for r in rows if r['case_id'] == case['case_id'] and r['condition'] == condition]
            require(bool(selected), 'each_case_condition_required')
            units.append({'case_id': case['case_id'], 'analysis_role': case['analysis_role'],
                          'retained_all_repeats': all(r['retained'] for r in selected)})
        totals[condition] = {'cases': len(units), 'retained': sum(u['retained_all_repeats'] for u in units), 'units': units}
    for total in totals.values():
        total['by_role'] = {role: {
            'cases': sum(u['analysis_role'] == role for u in total['units']),
            'retained': sum(u['analysis_role'] == role and u['retained_all_repeats'] for u in total['units'])}
            for role in ('primary', 'exploratory')}
    return {'rows': rows, 'totals': totals, 'semantic_grading': 'reviewer_not_certified_by_validator'}
