"""Offline public-contract and damage calibration. Zero model calls."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


fixtures = load('direct768_check_fixtures', HERE / 'fixtures.py')
p = fixtures.p


def public_decide(value, obj, state):
    labels = {'仅离线演练': state[0], '剩余≥20分钟': state[1],
              '剩余<20分钟': not state[1], '材料齐备': state[2], '复核员在场': state[3]}
    eligible = []
    for row in value['groups'][obj]['rules']:
        if row['question'] != '准备办法' or any(c not in labels for c in row['requires']):
            raise ValueError('Author fixture evaluator cannot interpret arbitrary model prose')
        if all(labels[c] for c in row['requires']): eligible.append(row)
    if not eligible: return 'U'
    priority = max(r['priority'] for r in eligible)
    choices = {r['choose'] for r in eligible if r['priority'] == priority}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def public_target(value, row):
    obj = int(row['case'].split('_', 1)[0]); kind = row['cohort']
    if kind in ('actual_status', 'lookalike'): return 'U'
    if kind == 'ambiguous_owner':
        choices = {public_decide(value, j, (True, True, True, False)) for j in (obj, obj ^ 1)}
    else:
        choices = {public_decide(value, obj, state) for state in p.corpus.states(kind)}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def damage(value, kind, pi):
    value = copy.deepcopy(value)
    for obj, group in enumerate(value['groups']):
        if kind == 'omit_second_choice':
            group['rules'] = [r for r in group['rules'] if r['priority'] or '剩余<20分钟' not in r['requires']]
        for row in group['rules']:
            if kind in ('drop_gate', 'drop_material'):
                erased = '仅离线演练' if kind == 'drop_gate' else '材料齐备'
                row['requires'] = [c for c in row['requires'] if c != erased]
            if kind == 'inherit_material' and row['priority'] and '材料齐备' not in row['requires']:
                row['requires'].insert(1, '材料齐备')
            if kind == 'stale_revision' and row['priority']:
                row['choose'] = p.corpus.ACTIONS[1 - p.corpus.BITS[pi][obj]]
    return value


def check():
    data = p.inputs()
    assert len(data['rows']) == 384 and sum(r['gold'] != 'U' for r in data['rows']) == 168
    assert sum(len(s['sources']) for s in data['sources'].values()) == 216
    assert len({p.digest(q) for bank in data['queries'].values() for q in bank}) == 384
    assert len(p.slots()) == 54 and [sum(s['kind'] == k for s in p.slots()) for k in ('none', 'full', 'extract', 'read')] == [2, 4, 16, 32]
    sizes, public_losses = [], {k: [] for k in ('drop_gate', 'drop_material', 'inherit_material', 'stale_revision', 'omit_second_choice')}
    for pi, person in enumerate(p.PROFILES):
        graph, sources = fixtures.graph(person), data['sources'][person]
        expected = None
        for method in p.METHODS:
            files = p.factory(method).bind(graph, sources, 768)
            text = files['prompt.md']
            value = p.candidate.dense.parse(p.candidate.restore(text))
            if expected is not None: assert value == expected
            expected = value
            assert len(value['groups']) == 6 and sum(len(g['rules']) for g in value['groups']) == 18
            assert len(text) <= 768 and all(public_target(value, row) == row['gold'] for row in data['rows'] if row['person'] == person)
            sizes.append(dict(person=person, method=method, author_fixture_characters=len(text),
                              author_fixture_not_model_output=True, scheme=files['encoding.private.json'].get('scheme')))
        for kind in public_losses:
            altered = damage(expected, kind, pi)
            for row in data['rows']:
                if row['person'] != person: continue
                choice = public_target(altered, row)
                if choice != row['gold']:
                    public_losses[kind].append(dict(person=person, case=row['case'], gold=row['gold'], damaged=choice))
    calibration = p.corpus.damage_summary()
    for kind, losses in public_losses.items():
        assert losses and {p.digest(x) for x in losses} == {p.digest(x) for x in calibration[kind]['losses']}
    return dict(new_model_calls=0, approved=False, measured_results_available=False,
        person_cases=384, known=168, unknown=216, source_messages=216,
        author_fixture_sizes=sizes,
        public_projection_damage_losses={k: len(v) for k, v in public_losses.items()},
        other_policy_calibration_losses={k: len(v['losses']) for k, v in calibration.items() if k not in public_losses},
        all_authored_contract_checks_pass=True, independent_semantic_gold=False,
        production_default_changed=False)


if __name__ == '__main__': print(json.dumps(check(), ensure_ascii=False, indent=2))
