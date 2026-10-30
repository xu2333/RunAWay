"""Finite authored development semantics. Does not parse natural language.

Enumerates unknown boolean facts per decision target. Known requires agreement
in every possible covered world; missing coverage, conflicts or absent rules
stay U. User evidence roles and target-local supersession are explicit inputs.
"""
from itertools import product


def active_rules(packet, target):
    source_index = {s['id']: (i, s) for i, s in enumerate(packet['sources']['sources'])}
    byid = {r['id']: r for r in packet['rules']}
    if len(byid) != len(packet['rules']):
        raise ValueError('Duplicate rule ID')
    eligible = []
    for rule in packet['rules']:
        if rule['target'] != target:
            continue
        position, source = source_index[rule['source_id']]
        if not rule['quote'] or rule['quote'] not in source['text']:
            raise ValueError('Nonliteral rule anchor')
        if source['role'] != 'user':
            continue
        if any(type(value) is not bool for value in rule['requires'].values()):
            raise ValueError('Rule facts must be boolean')
        if type(rule['priority']) is not int or not 0 <= rule['priority'] <= 9:
            raise ValueError('Invalid target-local priority')
        for old_id in rule['supersedes']:
            old = byid[old_id]
            old_position, old_source = source_index[old['source_id']]
            if (old['target'] != target or old['requires'] != rule['requires']
                    or old_source['role'] != 'user' or old_position >= position):
                raise ValueError('Supersession must be earlier user evidence in same target')
        eligible.append(rule)
    superseded = {old for rule in eligible for old in rule['supersedes']}
    return [rule for rule in eligible if rule['id'] not in superseded]


def resolve(packet, query):
    rules = active_rules(packet, query['target'])
    facts = query['facts']
    if any(type(value) is not bool for value in facts.values()):
        raise ValueError('Only explicit booleans; omit unknown facts')
    keys = sorted(set().union(*(rule['requires'] for rule in rules)))
    missing = [key for key in keys if key not in facts]
    if len(missing) > 8:
        raise ValueError('Finite development envelope exceeded')
    worlds = []
    for values in product([False, True], repeat=len(missing)):
        world = {**facts, **dict(zip(missing, values))}
        applicable = [r for r in rules if all(world[key] == value for key, value in r['requires'].items())]
        if not applicable:
            worlds.append(None)
            continue
        priority = max(r['priority'] for r in applicable)
        outcomes = {r['value'] for r in applicable if r['priority'] == priority}
        worlds.append(next(iter(outcomes)) if len(outcomes) == 1 else None)
    unique = set(worlds)
    value = next(iter(unique)) if len(unique) == 1 and None not in unique else 'U'
    # A uniquely known action missing from the options is still U; never pick
    # the remaining alternative or reinterpret a permission as a preference.
    if value != 'U' and value not in query['public']['options'].values():
        value = 'U'
    return value


def score(packet):
    groups = {key: {'planned': 0, 'correct': 0} for key in ('joint', 'preference', 'execution', 'unknown')}
    errors = []
    for query in packet['queries']:
        value = resolve(packet, query)
        keys = ['joint', query['stratum']]
        if query['expected'] == 'U':
            keys.append('unknown')
        for key in keys:
            groups[key]['planned'] += 1
            groups[key]['correct'] += int(value == query['expected'])
        if value != query['expected']:
            errors.append({'id': query['public']['id'], 'expected': query['expected'], 'actual': value})
    return {'groups': groups, 'errors': errors, 'model_performance_measured': False}
