"""Recount public delivery judgments. This cannot reassess private semantics."""
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'docs/results/real-task-history-v1.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def check(value):
    require(value['study'] == 'real-task-history-v1', 'study')
    require(value['status'] == 'closed_completed', 'closure')
    require(value['max_attempts'] == value['attempted'] == value['completed'] == 8, 'attempt counts')
    require(value['remaining'] == value['retries'] == 0, 'closed scope')
    require(value['independent_people'] == 1 and value['projects'] == 2, 'people and projects')
    require(value['primary_cases'] == value['exploratory_cases'] == 1, 'strata')
    require(value['repeats_per_case_condition'] == 2, 'repeats are not people')
    rows = value['rows']
    require(len(rows) == 8 and sorted(r['slot'] for r in rows) == list(range(1, 9)), 'fixed slots')
    arms = ('no_history', 'available_text_history')
    expected = {(case, arm, rep) for case in ('T1', 'T2') for arm in arms for rep in (1, 2)}
    require({(r['case_id'], r['condition'], r['repeat']) for r in rows} == expected, 'fixed case grid')
    for row in rows:
        require(row['quality_status'] in ('met', 'violated', 'unclear'), 'quality status')
        require(type(row['quality_pass']) is bool and row['quality_pass'] == (row['quality_status'] == 'met'), 'quality uncertainty')
        require(row['target_constraint'] in ('met', 'violated', 'unclear'), 'constraint status')
        retained = row['quality_pass'] and row['target_constraint'] == 'met'
        require(type(row['retained']) is bool and row['retained'] == retained, 'joint endpoint')
        for key in ('input_tokens', 'output_tokens', 'cached_input_tokens'):
            require(type(row[key]) is int and row[key] >= 0, 'reported usage')
        require(row['cached_input_tokens'] <= row['input_tokens'], 'cache subset')
    for arm in arms:
        passed = {}
        for case, role in (('T1', 'exploratory'), ('T2', 'primary')):
            selected = [r for r in rows if r['case_id'] == case and r['condition'] == arm]
            passed[case] = all(r['retained'] for r in selected)
            target = {'met': sum(r['target_constraint'] == 'met' for r in selected), 'deliveries': 2}
            require(value['target_constraint_only'][case][arm] == target, 'constraint-only endpoint')
            require(value['totals'][arm]['by_role'][role] == {'cases': 1, 'retained': int(passed[case])}, 'separate strata')
        total = value['totals'][arm]
        require(total['cases'] == 2 and total['retained'] == sum(passed.values()), 'case denominator')
        require(total['units'] == [{'case_id': c, 'analysis_role': role, 'retained_all_repeats': passed[c]}
                                  for c, role in (('T1', 'exploratory'), ('T2', 'primary'))], 'case units')
    usage = {name: sum(r[key] for r in rows) for name, key in
             (('input', 'input_tokens'), ('output', 'output_tokens'), ('cached_input', 'cached_input_tokens'))}
    usage['total'] = usage['input'] + usage['output']
    require(value['reported_tokens'] == usage, 'token totals')
    require(value['compression_comparison'] is False and value['device_execution'] is False, 'claim boundary')
    return {'primary': {arm: value['totals'][arm]['by_role']['primary'] for arm in arms},
            'target_constraint_only': value['target_constraint_only'], 'reported_tokens': usage,
            'new_model_calls': 0, 'semantic_reassessment': False}


if __name__ == '__main__':
    print(json.dumps(check(json.loads(DEFAULT.read_text(encoding='utf-8'))), indent=2))
