"""Full denominators and budget-paired transitions; missing is not unknown."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


plan = load('domain_revision_score_plan', HERE / 'plan.py')
prior = load('domain_revision_score_counts', HERE.parent / 'compression-stability-v1/score.py')
counts = prior.counts


def summarize(rows, responses, cards):
    def answers(person, method, gens=(0,1)):
        budget = plan.METHOD_BUDGET[method]
        return [responses.get((person, method, budget, g, 'card', r), {})
            if (person, method, budget, g) in cards else {} for g in gens for r in (0, 1)]
    def pool(selected, method, gens=(0,1)):
        total = counts([], [{}])
        for person in plan.PROFILES:
            own = counts([r for r in selected if r['person'] == person], answers(person, method, gens))
            for k in total:
                for v in total[k]: total[k][v] += own[k][v]
        return total
    methods = {m: dict(budget=plan.METHOD_BUDGET[m], strict=pool(rows, m),
        per_generation={str(g): pool(rows, m, (g,)) for g in (0,1)},
        per_person={p: pool([r for r in rows if r['person'] == p], m) for p in plan.PROFILES},
        cohorts={c: pool([r for r in rows if r['cohort'] == c], m) for c in sorted({r['cohort'] for r in rows})}) for m in plan.METHODS}
    cells, transitions = [], {k: 0 for k in ('both_retained', 'candidate_only_retained', 'baseline_only_retained',
        'both_observed_fail', 'baseline_missing', 'candidate_missing', 'both_missing')}
    for row in rows:
        cell = {k: row[k] for k in ('person', 'case', 'gold', 'cohort', 'family')}
        for method in plan.METHODS:
            values = [a.get(q) for a in answers(row['person'], method) for q in row['query_ids']]
            cell[method] = dict(answers=values, correct=all(v == row['gold'] for v in values), missing=any(v is None for v in values))
        low, high = [cell[m] for m in plan.METHODS]
        t = ('both_missing' if low['missing'] and high['missing'] else 'baseline_missing' if low['missing'] else
             'candidate_missing' if high['missing'] else 'both_retained' if low['correct'] and high['correct'] else
             'candidate_only_retained' if high['correct'] else 'baseline_only_retained' if low['correct'] else 'both_observed_fail')
        cell['transition'] = t; transitions[t] += 1; cells.append(cell)
    return dict(methods=methods, paired_transitions=transitions, all_case_transitions=cells,
        fixed_person_cases_per_method=94, known=36, unknown=58, answers_per_joint_case=8,
        independent_people=1, independent_semantic_gold=False, model_results_established_by_fixture=False)
