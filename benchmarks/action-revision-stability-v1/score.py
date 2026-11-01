"""79fixed cases,one method,two new producers; no historical/pilot pooling."""
from collections import Counter
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


plan = load('graph_stability_score_plan', HERE / 'plan.py')
prior = load('graph_stability_count_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    profiles, disputes = {}, []
    totals = {k: Counter() for k in counts([], [{}])}
    for pid in plan.PROFILES:
        own = [r for r in rows if r['person'] == pid]
        reads = [[responses.get((pid, 'graph-v1', g, r), {}) if (pid, 'graph-v1', g) in cards else {}
                  for r in (0, 1)] for g in (0, 1)]
        generations = {}
        for g in (0, 1):
            card = cards.get((pid, 'graph-v1', g))
            generations[str(g)] = {'valid_artifact': card is not None, 'characters': card['characters'] if card else None,
                'first': counts(own, [reads[g][0]]), 'second': counts(own, [reads[g][1]]),
                'strict_both_reads': counts(own, reads[g]),
                'within_card_read_disagreement': disagreement(own, [reads[g][0]], [reads[g][1]])}
        strict = counts(own, reads[0]+reads[1])
        profiles[pid] = {'generations': generations, 'strict_all_generations_and_reads': strict,
            'between_card_observed_disagreement_not_causal_variance': disagreement(own, reads[0], reads[1])}
        for k, value in strict.items(): totals[k].update(value)
        for flagged in plan.inputs()['disputed_rows']:
            if flagged['person'] == pid:
                disputes.append({'profile': pid, 'case': flagged['case'],
                    'legacy_author_annotation_unaccepted': flagged['gold'], 'reference_accepted': False,
                    'included_in_primary_or_gate': False,
                    'generations_reads_orders': [[[a.get(q) for q in flagged['query_ids']] for a in generation] for generation in reads]})
    return {'profiles': profiles, 'strict_all_generations_and_reads': {k: dict(v) for k, v in totals.items()},
        'disputed_observations_not_scored': disputes, 'primary_cases': 79, 'legacy_cases': 80, 'disputed_cases': 1,
        'answers_per_primary_case': 8, 'fresh_generations_planned': 6,
        'no_pilot_pooling_or_best_of_selection': True, 'baseline_arm': False,
        'independent_semantic_acceptance': False, 'independent_holdout': False,
        'independent_statistical_units_are_not_rotations_reads_or_cases': True,
        'new_original_inventory_coverage': 0, 'production_default_changed': False}
