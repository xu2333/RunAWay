"""Fixed fresh176 endpoint; families, people and missingness remain separate."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan = load('fresh_alias_score_plan', HERE / 'plan.py')
prior = load('fresh_alias_counts', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement
POSITIVE = ('base_old_alias', 'revised_old_alias', 'linked_name')


def summarize(rows, responses, cards):
    def pooled(selected, method, generations=(0, 1)):
        result = {key: Counter() for key in counts([], [{}])}
        for person in plan.PROFILES:
            own = [r for r in selected if r['person'] == person]
            answers = [responses.get((person, method, 1536, generation, 'card', repeat), {})
                       if (person, method, 1536, generation) in cards else {}
                       for generation in generations for repeat in (0, 1)]
            for key, values in counts(own, answers).items():
                result[key].update(values)
        return {key: dict(values) for key, values in result.items()}
    methods = {}
    for method in plan.METHODS:
        methods[method] = {'1536': {
            'strict': pooled(rows, method),
            'per_generation': {str(g): pooled(rows, method, (g,)) for g in (0, 1)},
            'per_family': {family: pooled([r for r in rows if r['family'] == family], method)
                           for family in ('chain', 'qualified')},
            'per_person': {person: pooled([r for r in rows if r['person'] == person], method) for person in plan.PROFILES},
            'cohorts': {kind: pooled([r for r in rows if r['cohort'] == kind], method) for kind in plan.corpus.KINDS},
            'positive_names': pooled([r for r in rows if r['cohort'] in POSITIVE], method),
            'other_cases': pooled([r for r in rows if r['cohort'] not in POSITIVE], method),
        }}
    return dict(methods=methods, primary_person_cases_per_method_budget=176, known_per_cell=112,
                unknown_per_cell=64, answers_per_joint_case=8, people=4,
                same_cases_reused_across_cells=True, independent_holdout=False,
                real_person_fidelity_verified=False, source_reference_semantics_verified=False,
                production_default_changed=False)
