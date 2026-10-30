"""Fixed-denominator nested compression scores, including missing generations."""
from collections import Counter


def counts(rows, answers):
    if not answers:
        raise ValueError('At least one planned answer dictionary is required')
    out = {k: {'planned': 0, 'correct': 0, 'missing': 0}
           for k in ('joint', 'known', 'unknown', 'personal_known', 'preference', 'execution', 'untyped')}
    for row in rows:
        values = [a.get(q) for a in answers for q in row['query_ids']]
        missing = any(v is None for v in values)
        correct = not missing and all(v == row['gold'] for v in values)
        keys = ['joint', 'unknown' if row['gold'] == 'U' else 'known', row.get('stratum', 'untyped')]
        if row['personal_known']:
            keys.append('personal_known')
        for k in keys:
            out[k]['planned'] += 1
            out[k]['correct'] += int(correct)
            out[k]['missing'] += int(missing)
    return out


def disagreement(rows, first, second):
    out = {'planned': len(rows), 'disagreeing': 0, 'missing': 0}
    for row in rows:
        a = [v.get(q) for v in first for q in row['query_ids']]
        b = [v.get(q) for v in second for q in row['query_ids']]
        missing = any(v is None for v in a+b)
        out['missing'] += int(missing)
        out['disagreeing'] += int(not missing and a != b)
    return out


def summarize(rows, responses, cards):
    profiles, pooled = {}, {}
    for budget in (768, 1024):
        pooled_counts = {k: Counter() for k in counts([], [{}])}
        for pid in ('h68', 'h93', 'dev'):
            own = [r for r in rows if r['person'] == pid]
            reads = [[responses.get((pid, budget, g, r), {}) if (pid, budget, g) in cards else {}
                      for r in (0, 1)] for g in (0, 1)]
            generations = {}
            for g in (0, 1):
                card = cards.get((pid, budget, g))
                generations[str(g)] = {'valid_artifact': card is not None,
                    'characters': card['characters'] if card else None,
                    'first': counts(own, [reads[g][0]]), 'second': counts(own, [reads[g][1]]),
                    'strict_both_reads': counts(own, reads[g]),
                    'within_card_read_disagreement': disagreement(own, [reads[g][0]], [reads[g][1]])}
            strict = counts(own, reads[0]+reads[1])
            profiles[pid, budget] = {'generations': generations, 'strict_all_generations_and_reads': strict,
                'between_card_observed_disagreement_not_causal_variance': disagreement(own, reads[0], reads[1])}
            for k, value in strict.items():
                pooled_counts[k].update(value)
        pooled[str(budget)] = {k: dict(v) for k, v in pooled_counts.items()}
    return {'profiles': {pid + ':' + str(budget): value for (pid, budget), value in profiles.items()},
            'per_budget_strict': pooled, 'no_best_of_selection': True,
            'independent_statistical_units_are_not_rotations_reads_or_cases': True,
            'new_original_inventory_coverage': 0, 'production_default_changed': False}
