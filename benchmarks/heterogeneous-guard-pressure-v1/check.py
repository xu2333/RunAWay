"""Offline author-projection, budget and damage checks; never model scores."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
spec = importlib.util.spec_from_file_location('pressure_check_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def expanded_rules(value, obj):
    group = value['groups'][obj]
    scope = group['scope'].split('；', 1)
    common = []
    if len(scope) == 2:
        common = re.findall('（([^（）]+)）', scope[1])
        if '且'.join('（' + s + '）' for s in common) != scope[1]:
            raise ValueError('Author evaluator does not interpret arbitrary scope prose')
    return [dict(row, requires=common + row['requires']) for row in group['rules']]


def choose(value, obj, state, damage=None):
    gate, amount, guard, reviewer, old_guard = state
    spec = p.corpus.SPECS[obj]; mode = spec[11]
    unit, before, threshold, gate_label, old_label, guard_label, review_label = spec[2:9]
    eligible = []
    for original in expanded_rules(value, obj):
        row = copy.deepcopy(original)
        if row['question'] != '方案': raise ValueError('Foreign author question')
        conditions = row['requires']
        if damage == 'drop_gate': conditions = [c for c in conditions if c != gate_label]
        if damage == 'drop_guard': conditions = [c for c in conditions if c != guard_label]
        if damage == 'old_guard' and mode == 'guard': conditions = [old_label if c == guard_label else c for c in conditions]
        if damage == 'reinstate_guard' and mode == 'release' and row['priority']:
            conditions = conditions + [guard_label]
        if damage == 'stale_threshold' and mode == 'threshold':
            conditions = [c.replace(str(threshold) + unit, str(before) + unit) for c in conditions]
        labels = {gate_label: gate, guard_label: guard, review_label: reviewer,
                  '余量≥%s%s' % (threshold, unit): amount >= threshold,
                  '余量<%s%s' % (threshold, unit): amount < threshold}
        if old_label != guard_label: labels[old_label] = old_guard
        if before != threshold:
            labels['余量≥%s%s' % (before, unit)] = amount >= before
            labels['余量<%s%s' % (before, unit)] = amount < before
        if any(c not in labels for c in conditions): raise ValueError('Foreign author predicate')
        if all(labels[c] for c in conditions): eligible.append(row)
    if not eligible: return 'U'
    priority = max(r['priority'] for r in eligible)
    choices = {r['choose'] for r in eligible if r['priority'] == priority}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def public_target(value, row, damage=None):
    if row['cohort'] in ('status', 'copy'): return 'U'
    obj = int(row['case'].split('_', 1)[0])
    choices = {choose(value, obj, state, damage) for state in p.corpus.states(obj, row['cohort'])}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def check():
    data = p.inputs()
    assert len(data['rows']) == 164 and sum(r['personal_known'] for r in data['rows']) == 72
    assert sum(len(s['sources']) for s in data['sources'].values()) == 96
    assert len({p.digest(q) for qs in data['queries'].values() for q in qs}) == 328
    # Count actual scenario/options text as well, not just different question IDs.
    assert len({p.digest({k: q[k] for k in ('scenario', 'options')}) for qs in data['queries'].values() for q in qs}) == 328
    assert len(p.slots()) == 16
    assert [sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')] == [2, 2, 4, 8]
    calibration = {kind: [] for kind in ('stale_threshold', 'old_guard', 'reinstate_guard', 'drop_gate', 'drop_guard')}
    parents = []
    for pi, person in enumerate(p.PROFILES):
        sources, graph = data['sources'][person], p.corpus.graph(person)
        original = p.candidate.base.bind(graph, sources, 16000)['prompt.md']
        accepted = p.candidate.bind(graph, sources, 1536)
        value = p.candidate.dense.parse(p.candidate.restore(accepted['prompt.md']))
        assert len(value['groups']) == 6 and sum(len(g['rules']) for g in value['groups']) == 18
        assert all(public_target(value, row) == row['gold'] for row in data['rows'] if row['person'] == person)
        caps = []
        for cap in (512, 768, 832, 896, 960, 1024, 1536):
            try:
                rendered = p.candidate.render(original, cap)
                assert p.candidate.dense.parse(p.candidate.restore(rendered['prompt'])) == value
                caps.append(dict(budget=cap, fits=True, characters=rendered['characters'], scheme=rendered['scheme']))
            except ValueError as exc:
                if str(exc) != 'Neither complete reversible layout fits whole budget; no truncation':
                    raise
                caps.append(dict(budget=cap, fits=False, error=str(exc)))
        assert next(c for c in caps if c['budget'] == 768)['fits'] is False
        parents.append(dict(person=person, expanded_characters=len(original), caps=caps,
            author_fixture_not_model_output=True, not_an_information_theoretic_lower_bound=True))
        for kind, changed in calibration.items():
            for row in data['rows']:
                if row['person'] != person: continue
                got = public_target(value, row, kind)
                expected = p.corpus.target(pi, int(row['case'].split('_', 1)[0]), row['cohort'], kind)
                assert got == expected
                if got != row['gold']: changed.append(dict(person=person, case=row['case'], gold=row['gold'], damaged=got))
    assert all(calibration.values())
    return dict(new_model_calls=0, approved=False, model_results_available=False,
        person_cases_per_budget=164, known=72, unknown=92, source_messages=96,
        author_fixture_capacity=parents, public_projection_damage_case_counts={k: len(v) for k, v in calibration.items()},
        damage_is_constructed_not_observed_model_loss=True, independent_semantic_gold=False,
        arbitrary_model_prose_evaluator=False, production_defaults_changed=False)


if __name__ == '__main__': print(json.dumps(check(), ensure_ascii=False, indent=2))
