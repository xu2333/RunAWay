"""Opt-in offline diagnostics; strict unknown and completion-invariant action differ.

Uses the existing authored world and fidelity scorer. This does not change the
production resolver, sealed scores, or infer a model's internal state.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from . import fidelity_stress as fs, temporal_stress as stress, temporal_concise as codec
from .pipeline import write_once
from .synthetic_metric import file_hash

CONTROLS = ('dual_program', 'invariant_action_loses_unknown', 'assume_missing_false',
            'erase_conflict', 'wrong_person', 'delete_hard', 'missing_snapshot',
            'drop_completion_branch')
TASKS = ('current_choice', 'historical_reconstruction', 'joint')


def unique_outcomes(rows):
    return [dict(status=s, action=a) for s, a in sorted({(r['status'], r['action']) for r in rows})]


def completion_action(outcomes):
    return outcomes[0]['action'] if len(outcomes) == 1 and outcomes[0]['status'] == 'chosen' else None


def completion_view(policy, domain, context, max_missing=8):
    """Exhaustive program diagnostic, never a new production decision policy.

    Fail closed beyond the bound. Unknown predicates are enumerated, never
    sampled or silently replaced by false. Only a unique chosen action counts.
    """
    strict = codec.resolve(policy, domain, context)  # Also validates bool context.
    if type(max_missing) is not int or not 0 <= max_missing <= 8:
        raise ValueError('Completion bound must be an integer from0to8')
    row = next((d for d in policy['domains'] if d['domain'] == domain), None)
    names = sorted({k for tier in ('exception', 'constraint') for e in row[tier] for k, _ in e['when']}) if row else []
    missing = [k for k in names if k not in context]
    if len(missing) > max_missing:
        raise ValueError('Too many absent predicates; no sampling or truncation')
    outcomes = unique_outcomes(codec.resolve(policy, domain, {**context, **dict(zip(missing, values))})
                               for values in itertools.product((False, True), repeat=len(missing)))
    return dict(strict=strict, possible_outcomes=outcomes, completion_action=completion_action(outcomes),
                enumerated_completions=2**len(missing))


def authored_expected(person, case):
    """Gold only from the pre-existing authored table, never either resolver."""
    context = case['context']; missing = [k for k in ('c0', 'c1') if k not in context]
    outcomes = []
    for values in itertools.product((False, True), repeat=len(missing)):
        full = {**context, **dict(zip(missing, values))}
        action, status, _ = stress.gold(case['at'], full['c0'], full['c1'], person['member'])
        outcomes.append(dict(status=status, action=stress.ACTIONS[int(action)] if action != 'U' else None))
    outcomes = unique_outcomes(outcomes); action = completion_action(outcomes)
    label = str(stress.ACTIONS.index(action)) if action is not None else 'U'
    return dict(strict_answer=case['gold'], reported_status=case['expected_status'],
                completion_answer=next(k for k, v in case['options'].items() if v == label),
                completion_action=label, possible_outcomes=outcomes)


def completion_world(world, expected_records=None):
    """Separate, explicit task projection; original world and gold stay intact."""
    result = copy.deepcopy(world)
    for p in result['people']:
        for c in p['cases']:
            expected = authored_expected(p, c) if expected_records is None else expected_records[p['id']][c['public']['id']]
            c['gold'] = expected['completion_answer']; c['action'] = expected['completion_action']
    result['purpose'] = 'offline_completion_action_task_not_original_strict_task'
    return result


def program_records(world, condition, snaps):
    output = {}
    for p in world['people']:
        source = snaps[p['twin'] if condition == 'wrong_person' else p['id']]
        data = json.loads(stress.memory(source, condition))
        decoded = {day: codec.decode(text) for day, text in data['snapshots'].items()}
        output[p['id']] = {}
        for c in p['cases']:
            policy = decoded.get(str(c['at']))
            if policy is None: continue  # Missing is not an unknown answer.
            context = {name: c['context'][key] for key, name in [('c0', stress.P), ('c1', stress.Q)] if key in c['context']}
            if condition == 'assume_missing_false':
                context = {stress.P: context.get(stress.P, False), stress.Q: context.get(stress.Q, False)}
            view = completion_view(policy, stress.DOMAIN, context)
            strict = view['strict']; outcomes = view['possible_outcomes']
            if condition == 'invariant_action_loses_unknown' and strict['status'] == 'context_unknown' and view['completion_action'] is not None:
                strict = dict(status='chosen', action=view['completion_action'])
            if condition == 'drop_completion_branch' and len(outcomes) > 1:
                outcomes = outcomes[:1]  # Deliberate diagnostic corruption.
            def letter(action):
                label = str(stress.ACTIONS.index(action)) if action is not None else 'U'
                return next(k for k, v in c['options'].items() if v == label)
            output[p['id']][c['public']['id']] = dict(
                strict_answer=letter(strict['action']), reported_status=strict['status'],
                completion_answer=letter(completion_action(outcomes)), possible_outcomes=outcomes)
    return output


def score_records(world, records, expected_records=None, tasks=TASKS):
    if not tasks or any(task not in TASKS for task in tasks) or len(set(tasks)) != len(tasks):
        raise ValueError('Unique supported tasks required')
    if expected_records is not None:
        if set(expected_records) != {p['id'] for p in world['people']}: raise ValueError('Gold person coverage changed')
        for p in world['people']:
            if set(expected_records[p['id']]) != {c['public']['id'] for c in p['cases']}: raise ValueError('Gold query coverage changed')
            for c in p['cases']:
                e = expected_records[p['id']][c['public']['id']]
                if e['strict_answer'] != c['gold'] or e['reported_status'] != c['expected_status'] or c['options'].get(e['completion_answer']) != e['completion_action']:
                    raise ValueError('Supplied gold disagrees with task binding')
    if not isinstance(records, dict): raise ValueError('Records must be a person-keyed object')
    allowed = {p['id']: {c['public']['id'] for c in p['cases']} for p in world['people']}
    if set(records) - set(allowed): raise ValueError('Unexpected person in records')
    fields = {'strict_answer', 'reported_status', 'completion_answer', 'possible_outcomes'}
    for pid, rows in records.items():
        if not isinstance(rows, dict) or set(rows) - allowed[pid]: raise ValueError('Unexpected query in records')
        for row in rows.values():
            if not isinstance(row, dict) or set(row) - fields: raise ValueError('Unexpected structured fields')
            for key in ('strict_answer', 'completion_answer', 'reported_status'):
                if row.get(key) is not None and not isinstance(row[key], str): raise ValueError('String or missing value required')
            if 'possible_outcomes' in row:
                outcomes = row['possible_outcomes']
                if not isinstance(outcomes, list) or not 1 <= len(outcomes) <= 256: raise ValueError('Bounded nonempty outcome list required')
                for outcome in outcomes:
                    if not isinstance(outcome, dict) or set(outcome) != {'status', 'action'}: raise ValueError('Invalid outcome fields')
                    if outcome['status'] not in ('chosen', 'conflict', 'unobserved'): raise ValueError('Invalid complete-context status')
                    if outcome['status'] == 'chosen':
                        if not isinstance(outcome['action'], str) or not outcome['action']: raise ValueError('Chosen action required')
                    elif outcome['action'] is not None: raise ValueError('Unknown outcome cannot claim action')
                if unique_outcomes(outcomes) != outcomes: raise ValueError('Canonical unique outcome set required')
    strict = {}; robust = {}; states = {}; outcomes = {}
    witnesses = []
    for p in world['people']:
        pid = p['id']; strict[pid] = {}; robust[pid] = {}; states[pid] = {}
        for c in p['cases']:
            key = c['public']['id']; row = records.get(pid, {}).get(key)
            expected = authored_expected(p, c) if expected_records is None else expected_records[pid][key]
            if row is not None:
                strict[pid][key] = row.get('strict_answer'); robust[pid][key] = row.get('completion_answer')
                states[pid][key] = row.get('reported_status')
            for task in tasks:
                if task != 'joint' and c['public']['task'] != task: continue
                score = outcomes.setdefault(task, dict(correct=0, planned=0, missing=0))
                score['planned'] += 1
                score['missing'] += row is None or 'possible_outcomes' not in row
                score['correct'] += row is not None and row.get('possible_outcomes') == expected['possible_outcomes']
            if row != {k: expected[k] for k in ('strict_answer', 'reported_status', 'completion_answer', 'possible_outcomes')} and len(witnesses) < 2:
                witnesses.append(dict(person_id=pid, day=c['at'], question=c['public'],
                                      expected=expected, actual=row, scenario=c['scenario']))
    projected = completion_world(world, expected_records)
    return dict(strict_choice={task: fs.score(world, strict, task) for task in tasks},
                reported_rule_status={task: stress.state_score(world, states, task) for task in tasks},
                completion_choice={task: fs.score(projected, robust, task) for task in tasks},
                possible_outcomes=outcomes, counterexamples=witnesses)


def calibrate():
    world = stress.build_world(); snaps = {p['id']: stress.snapshots(p['artifact']) for p in world['people']}
    expected = {p['id']: {c['public']['id']: authored_expected(p, c) for c in p['cases']} for p in world['people']}
    outputs = {name: program_records(world, name, snaps) for name in CONTROLS}
    controls = {name: score_records(world, rows) for name, rows in outputs.items()}
    base = controls['dual_program']; lost = controls['invariant_action_loses_unknown']; erased = controls['erase_conflict']
    slices = {}
    for p in world['people']:
        for c in p['cases']:
            e = expected[p['id']][c['public']['id']]
            kind = ('unknown_but_determinate' if e['completion_action'] != 'U' else 'unknown_and_indeterminate') if e['reported_status'] == 'context_unknown' else e['reported_status']
            for task in ('joint', c['public']['task']):
                rows = slices.setdefault(task, {}); rows[kind] = rows.get(kind, 0) + 1
    checks = dict(
        dual_program_all_four_fields_pass=all(base[k]['joint']['correct'] == 432 for k in ('strict_choice', 'reported_rule_status', 'completion_choice', 'possible_outcomes')),
        invariant_action_can_hide_lost_unknown=lost['completion_choice']['joint']['correct'] == 432 and lost['reported_rule_status']['joint']['correct'] < 432 and lost['strict_choice']['joint']['correct'] < 432,
        conflict_erasure_hides_behind_both_choice_scores=erased['strict_choice']['joint']['correct'] == erased['completion_choice']['joint']['correct'] == 432 and erased['reported_rule_status']['joint']['correct'] < 432 and erased['possible_outcomes']['joint']['correct'] < 432,
        missing_false_and_branch_loss_detected=all(controls[k]['possible_outcomes']['joint']['correct'] < 432 for k in ('assume_missing_false', 'drop_completion_branch')),
        wrong_person_loses_contrast=controls['wrong_person']['completion_choice']['current_choice']['matched_domain_contrasts']['correct'] == 0,
        missing_keeps_all_denominators=all(controls['missing_snapshot'][k]['joint']['planned'] == 432 and controls['missing_snapshot'][k]['joint']['missing'] == 36 for k in ('strict_choice', 'reported_rule_status', 'completion_choice', 'possible_outcomes')))
    report = dict(kind='offline_program_state_and_completion_diagnostic', origin='fully_synthetic',
        passed=all(checks.values()), checks=checks, world_id=world['id'], people=2, paired_statistical_units=1,
        denominators=dict(current=36, historical=396, joint=432), authored_slices=slices, controls=controls,
        external_model_calls=0, experimental_service_tokens=0, actual_tokens=None,
        interpretation='New opt-in structured diagnostic on one consumed authored pair, not a new model score. Strict scores retain the old contract; completion-choice uses a separately labelled task projection. Reported rule status and outcome sets are checkable outputs, not evidence of hidden model state. No product default changes or D0031 rescoring.',
        limits=['All432queries, option orders, dates and people belong to one authored mirrored pair; no population CI or real-person/generalization claim.',
                'Authored complete-context table supplies independent gold; program controls use production snapshots and decoder. This does not measure extraction, natural prose or LLM behavior.',
                'Gold contains future completion possibilities and stays evaluation-side. It must never enter a reader payload.',
                'No compression-rate or service-cost improvement measured. Native development-chat usage is separate and not zero.'])
    return report, dict(expected=expected, program_records=outputs)


def save(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=False); report, records = calibrate()
    for name, data in [('report.synthetic.json', report), ('records.synthetic.json', records)]: write_once(out/name, data)
    root = Path(__file__).resolve().parents[1]
    write_once(out/'source-hashes.json', {str(p.relative_to(root)): file_hash(p) for p in sorted((root/'runaway').glob('*.py'))})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', required=True); args = parser.parse_args()
    result = save(args.out)
    print(json.dumps(dict(passed=result['passed'], checks=result['checks'], external_model_calls=0)))
