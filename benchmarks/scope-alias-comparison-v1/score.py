"""Separate64-case endpoints per method/budget; no pooling as independent samples."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('alias_comparison_score_plan', HERE / 'plan.py')
prior = load('binding_counts', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    def pooled(selected, method, budget, generations=(0, 1)):
        result = {k: Counter() for k in counts([], [{}])}
        for person in plan.PROFILES:
            own = [r for r in selected if r['person'] == person]
            answers = [responses.get((person, method, budget, generation, 'card', repeat), {})
                       if (person, method, budget, generation) in cards else {}
                       for generation in generations for repeat in (0, 1)]
            for k, value in counts(own, answers).items():
                result[k].update(value)
        return {k: dict(v) for k, v in result.items()}
    methods = {}
    for method in plan.METHODS:
        methods[method] = {}
        for budget in plan.BUDGETS:
            methods[method][str(budget)] = {
                'strict': pooled(rows, method, budget),
                'per_generation': {str(g): pooled(rows, method, budget, (g,)) for g in (0, 1)},
                'cohorts': {kind: pooled([r for r in rows if r['cohort'] == kind], method, budget)
                            for kind in plan.corpus.KINDS},
                'old_alias': pooled([r for r in rows if r['cohort'] in ('base_old_alias', 'revised_old_alias')], method, budget),
                'late_revision': pooled([r for r in rows if r['cohort'] in ('revised_current', 'revised_old_alias')], method, budget)}
    return {'methods': methods, 'primary_person_cases_per_method_budget': 64,
            'known_per_cell': 40, 'unknown_per_cell': 24, 'answers_per_joint_case': 8,
            'people': 2, 'same_cases_reused_across_cells': True,
            'independent_holdout': False, 'real_person_fidelity_verified': False,
            'source_reference_semantics_verified': False, 'production_default_changed': False}
