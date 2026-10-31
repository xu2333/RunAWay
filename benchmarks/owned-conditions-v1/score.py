"""79 fixed cases per method, nested generations, reads and orders."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('owned_score_plan', HERE / 'plan.py')
prior = load('owned_score_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    profiles, pooled, disputes = {}, {}, []
    for method in plan.METHODS:
        totals = {k: Counter() for k in counts([], [{}])}
        for pid in plan.PROFILES:
            own = [r for r in rows if r['person'] == pid]
            reads = [[responses.get((pid, method, g, r), {}) if (pid, method, g) in cards else {}
                      for r in (0, 1)] for g in (0, 1)]
            generations = {}
            for g in (0, 1):
                card = cards.get((pid, method, g))
                generations[str(g)] = {'valid_artifact': card is not None, 'characters': card['characters'] if card else None,
                    'first': counts(own, [reads[g][0]]), 'second': counts(own, [reads[g][1]]),
                    'strict_both_reads': counts(own, reads[g]),
                    'within_card_read_disagreement': disagreement(own, [reads[g][0]], [reads[g][1]])}
            strict = counts(own, reads[0]+reads[1])
            profiles[pid+':'+method] = {'generations': generations,
                'strict_all_generations_and_reads': strict,
                'between_card_observed_disagreement_not_causal_variance': disagreement(own, reads[0], reads[1])}
            for k, value in strict.items():
                totals[k].update(value)
            for flagged in plan.inputs()['disputed_rows']:
                if flagged['person'] == pid:
                    disputes.append({'profile': pid, 'method': method, 'case': flagged['case'],
                        'legacy_author_annotation_unaccepted': flagged['gold'], 'reference_accepted': False,
                        'included_in_primary_or_gate': False,
                        'generations_reads_orders': [[[a.get(q) for q in flagged['query_ids']] for a in generation] for generation in reads]})
        pooled[method] = {k: dict(v) for k, v in totals.items()}
    paired = {k: 0 for k in ('planned', 'both_correct', 'only_baseline_correct', 'only_candidate_correct',
                              'neither_correct', 'baseline_missing', 'candidate_missing')}
    cases = []
    for row in rows:
        outcomes = {}
        for method in plan.METHODS:
            pid = row['person']
            answers = [responses.get((pid, method, g, r), {}) if (pid, method, g) in cards else {}
                       for g in (0, 1) for r in (0, 1)]
            outcomes[method] = counts([row], answers)['joint']
        a, b = (outcomes[m] for m in plan.METHODS)
        paired['planned'] += 1
        label = 'both_correct' if a['correct'] and b['correct'] else 'only_baseline_correct' if a['correct'] else 'only_candidate_correct' if b['correct'] else 'neither_correct'
        paired[label] += 1
        paired['baseline_missing'] += a['missing']
        paired['candidate_missing'] += b['missing']
        cases.append({'profile': row['person'], 'case': row['case'], 'outcomes': outcomes})
    return {'profiles': profiles, 'per_method_strict': pooled, 'disputed_observations_not_scored': disputes,
        'paired_strict_development_cases': paired, 'case_outcomes': cases,
        'primary_cases_per_method': 79, 'legacy_cases': 80, 'disputed_cases': 1,
        'no_best_of_selection': True, 'independent_semantic_acceptance': False,
        'independent_statistical_units_are_not_rotations_reads_or_cases': True,
        'new_original_inventory_coverage': 0, 'production_default_changed': False}
