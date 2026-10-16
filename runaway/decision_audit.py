"""Offline, failure-aware readout for synthetic decision-world predictions.

Never changes a frozen report or invokes a model. Missing output is a pipeline
failure, not an observed instruction violation. Choice data has no RIG estimate.
"""
import argparse
import json
from pathlib import Path
from .decision_world import gold


def readout(world, predictions, condition):
    people = world['personas']
    cases = world['test']
    primary = [c for c in cases if c['kind'] == 'heldout']
    lookup = {c['public']['id']: c for c in cases}

    def choice(person, case):
        value = predictions.get(person['id'], {}).get(condition, {}).get(case['public']['id'])
        return 'U' if value == 'unknown' else value

    def counts(items):
        # (available, correct) tuples; unavailable never masquerades as observed error.
        items = list(items)
        available = sum(a for a, _ in items)
        correct = sum(b for a, b in items if a)
        return {'correct': correct, 'planned': len(items), 'available': available,
                'missing': len(items) - available,
                'observed_incorrect': available - correct,
                'end_to_end_rate': correct / len(items) if items and available else None,
                'available_rate': correct / available if available else None}

    def outcome(p, c):
        value = choice(p, c)
        return value in ('A', 'B', 'U'), value == gold(p['policy'], c)

    def order(p, c):
        a, b = choice(p, c), choice(p, lookup[c['original_id']])
        available = a in ('A', 'B', 'U') and b in ('A', 'B', 'U')
        return available, a in ('A', 'B') and b in ('A', 'B') and c['actions'][a] == lookup[c['original_id']]['actions'][b]

    paired = {}
    for c in primary:
        paired.setdefault(c['pair'], []).append(c)
    flips, stable = [], []
    for p in people:
        for group in paired.values():
            if len(group) != 2:
                raise ValueError('Counterfactual groups must have exactly two cases')
            actual = [c['actions'][gold(p['policy'], c)] for c in group]
            outcomes = [outcome(p, c) for c in group]
            (flips if len(set(actual)) > 1 else stable).append((all(a for a, _ in outcomes), all(b for _, b in outcomes)))
    twins = []
    by_id = {p['id']: p for p in people}
    for p in people:
        twin = by_id.get(p['twin'])
        if twin is None or p['id'] >= twin['id']:
            continue
        for c in primary:
            if gold(p['policy'], c) == gold(twin['policy'], c):
                continue
            a, b = outcome(p, c), outcome(twin, c)
            twins.append((a[0] and b[0], a[1] and b[1]))
    constraints = counts(outcome(p, c) for p in people for c in cases if c['kind'] == 'explicit_request')
    constraints['observed_violations'] = constraints.pop('observed_incorrect')
    return {'primary': counts(outcome(p, c) for p in people for c in primary),
            'current_instructions': constraints,
            'counterfactual_required_flip': counts(flips),
            'counterfactual_required_stable': counts(stable),
            'twins': counts(twins),
            'order': counts(order(p, c) for p in people for c in cases if c['kind'] == 'order_swap'),
            'unknown': counts(outcome(p, c) for p in people for c in cases if c['kind'] == 'unobserved')}


def audit_run(directory):
    root = Path(directory)
    plan = json.loads((root / 'snapshot.synthetic.json').read_text())
    if plan.get('origin') != 'fully_synthetic':
        raise ValueError('This readout only accepts synthetic plans')
    predictions = json.loads((root / 'predictions.synthetic.json').read_text())
    memory_path = root / 'memories.synthetic.json'
    memories = json.loads(memory_path.read_text()) if memory_path.exists() else {}
    return {'schema_version': 1, 'snapshot_id': plan['id'], 'origin': 'fully_synthetic',
            'posthoc_readout': True, 'original_reports_unchanged': True,
            'conditions': {c: readout(plan['world'], predictions, c) for c in plan['conditions']},
            'memory_replacement_characters': {pid: {c: text.count('\ufffd') for c, text in values.items() if text is not None and '\ufffd' in text} for pid, values in memories.items()},
            'probability_metrics': None, 'real_person_fidelity_verified': False,
            'interpretation': 'Missing outputs count as end-to-end misses only when the condition ran at least once. Instruction violations count only observed incorrect outputs. No logits, no RIG.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--out', required=True, help='New JSON file; frozen reports are never overwritten')
    a = p.parse_args()
    value = audit_run(a.run)
    with Path(a.out).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
