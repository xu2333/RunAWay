"""Strict case-level fidelity and failure localization; missing is never U."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


plan = load('direct768_score_plan', HERE / 'plan.py')
prior = load('direct768_strict_counts', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def kind(gold, answers):
    if any(a is None for a in answers): return 'missing'
    if all(a == gold for a in answers): return 'retained'
    if gold == 'U': return 'false_concrete_choice'
    if all(a == 'U' for a in answers): return 'all_unknown_from_known'
    if any(a not in (gold, 'U') for a in answers): return 'different_choice'
    return 'intermittent_unknown_from_known'


def summarize(rows, responses, cards):
    def answers(person, method, generations=(0, 1)):
        return [responses.get((person, method, 768, g, 'card', r), {})
                if (person, method, 768, g) in cards else {} for g in generations for r in (0, 1)]
    def pool(selected, method, generations=(0, 1)):
        total = counts([], [{}])
        for person in plan.PROFILES:
            own = counts([r for r in selected if r['person'] == person], answers(person, method, generations))
            for k in total:
                for v in total[k]: total[k][v] += own[k][v]
        return total
    methods = {}
    for method in plan.METHODS:
        methods[method] = {'768': dict(strict=pool(rows, method),
            per_generation={str(g): pool(rows, method, (g,)) for g in (0, 1)},
            per_person={p: pool([r for r in rows if r['person'] == p], method) for p in plan.PROFILES},
            per_family={f: pool([r for r in rows if r['family'] == f], method) for f in ('strict', 'released')},
            cohorts={c: pool([r for r in rows if r['cohort'] == c], method) for c in plan.corpus.KINDS})}
    cells, transitions = [], {k: 0 for k in ('kept', 'recovered', 'new_observed_loss', 'both_observed_fail',
                                           'baseline_missing', 'candidate_missing', 'both_missing')}
    for row in rows:
        cell = {k: row[k] for k in ('person', 'case', 'gold', 'cohort', 'family')}
        for method in plan.METHODS:
            nested = [[a.get(q) for a in answers(row['person'], method, (g,)) for q in row['query_ids']] for g in (0, 1)]
            values = nested[0] + nested[1]
            cell[method] = dict(correct=all(v == row['gold'] for v in values), missing=any(v is None for v in values),
                                answers_by_generation=nested, loss_kind=kind(row['gold'], values))
        a, b = (cell[m] for m in plan.METHODS)
        transition = ('both_missing' if a['missing'] and b['missing'] else 'baseline_missing' if a['missing'] else
            'candidate_missing' if b['missing'] else 'kept' if a['correct'] and b['correct'] else
            'recovered' if b['correct'] else 'new_observed_loss' if a['correct'] else 'both_observed_fail')
        cell['transition'] = transition; transitions[transition] += 1; cells.append(cell)
    return dict(methods=methods, primary_cases_per_method=384, known=168, unknown=216,
                answers_per_joint_case=8, all_case_transitions=cells, paired_transitions=transitions,
                independent_people=4, independent_semantic_gold=False,
                model_results_established_by_fixture=False, production_default_changed=False)
