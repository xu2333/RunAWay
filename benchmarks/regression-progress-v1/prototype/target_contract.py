"""Manually annotated development logic, not a parser or model repair."""


def resolve(rules, target, facts):
    eligible = []
    uncovered = False
    for rule in rules:
        if rule['target'] != target or rule['role'] != 'user':
            continue
        values = [facts.get(key) == value if key in facts else None for key, value in rule['requires'].items()]
        if any(value is False for value in values):
            continue
        if any(value is None for value in values):
            uncovered = True
            continue
        eligible.append(rule)
    if uncovered or not eligible:
        return 'U'
    top = max(rule['priority'] for rule in eligible)
    values = {rule['value'] for rule in eligible if rule['priority'] == top}
    return next(iter(values)) if len(values) == 1 else 'U'


def annotated_rules(choice):
    return [
        {'target': 'plan_choice', 'role': 'user', 'source_id': 'm29',
         'requires': {'public_interface_conditions': True}, 'priority': 0, 'value': choice},
        {'target': 'publication_permission', 'role': 'user', 'source_id': 'm45',
         'requires': {'client_list_pending': True}, 'priority': 0, 'value': 'do_not_publish'},
    ]
