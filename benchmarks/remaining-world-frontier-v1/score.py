"""69planned primary cases;3preflagged w14cases are observations, not scores."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('remaining_score_plan', HERE / 'plan.py')
prior = load('remaining_score_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    profiles, pooled, disputes = {}, {}, []
    for budget in plan.BUDGETS:
        totals = {k: Counter() for k in counts([], [{}])}
        for pid in plan.PROFILES:
            own = [r for r in rows if r['person'] == pid]
            reads = [[responses.get((pid, budget, g, r), {}) if (pid, budget, g) in cards else {}
                      for r in (0, 1)] for g in (0, 1)]
            generations = {}
            for g in (0, 1):
                card = cards.get((pid, budget, g))
                generations[str(g)] = {'valid_artifact': card is not None, 'characters': card['characters'] if card else None,
                    'first': counts(own, [reads[g][0]]), 'second': counts(own, [reads[g][1]]),
                    'strict_both_reads': counts(own, reads[g]),
                    'within_card_read_disagreement': disagreement(own, [reads[g][0]], [reads[g][1]])}
            strict = counts(own, reads[0]+reads[1])
            profiles[pid+':'+str(budget)] = {'generations': generations,
                'strict_all_generations_and_reads': strict,
                'between_card_observed_disagreement_not_causal_variance': disagreement(own, reads[0], reads[1])}
            for k, value in strict.items():
                totals[k].update(value)
            flagged = next(r for r in plan.inputs()['disputed_rows'] if r['person'] == pid)
            disputes.append({'profile': pid, 'budget': budget, 'case': 'w14',
                'legacy_author_annotation_unaccepted': flagged['gold'], 'reference_accepted': False,
                'included_in_primary_or_gate': False,
                'generations_reads_orders': [[[a.get(q) for q in flagged['query_ids']] for a in generation] for generation in reads]})
        pooled[str(budget)] = {k: dict(v) for k, v in totals.items()}
    return {'profiles': profiles, 'per_budget_strict': pooled, 'disputed_observations_not_scored': disputes,
            'primary_cases_per_budget': 69, 'disputed_cases': 3, 'legacy_cases': 72,
            'no_best_of_selection': True, 'independent_semantic_acceptance': False,
            'new_original_inventory_coverage_before_binding_audit': 0, 'production_default_changed': False}
