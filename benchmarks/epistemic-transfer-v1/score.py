"""Fixed120case endpoints with separate entailment and abstention slices."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('epistemic_score_plan', HERE / 'plan.py')
prior = load('epistemic_count_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    pooled, profiles, outcomes, slices = {}, {}, {}, {}
    for view in ('card', 'tail'):
        total = {k: Counter() for k in counts([], [{}])}
        view_slices = {}
        for pid in plan.PROFILES:
            key = pid, plan.METHODS[0], 0
            card = cards.get(key)
            answers = [responses.get(key + (view, repeat), {}) if card else {} for repeat in (0, 1)]
            own = [r for r in rows if r['person'] == pid]
            strict = counts(own, answers)
            groups = {c: [r for r in own if r['cohort'] == c] for c in sorted({r['cohort'] for r in rows})}
            groups.update({k: [r for r in own if r[k]] for k in
                           ('derived_known', 'structural_known', 'personal_known', 'guarantee_withdrawal_sensitive')})
            for name, selected in groups.items():
                view_slices.setdefault(name, Counter()).update(counts(selected, answers)['joint'])
            profiles[pid + ':' + view] = {'valid_parent': card is not None,
                'characters': card['characters'] if card else None,
                'full_transcript_characters': len(plan.transcript(plan.inputs()['sources'][pid])),
                'strict_both_reads': strict, 'first': counts(own, [answers[0]]),
                'second': counts(own, [answers[1]]),
                'within_parent_read_disagreement': disagreement(own, [answers[0]], [answers[1]])}
            for k, value in strict.items():
                total[k].update(value)
            for row in own:
                outcomes[pid, row['case'], view] = counts([row], answers)['joint']
        pooled[view] = {k: dict(v) for k, v in total.items()}
        slices[view] = {k: dict(v) for k, v in view_slices.items()}
    paired = {k: 0 for k in ('planned', 'both_correct', 'card_only', 'tail_only', 'neither_correct', 'card_missing', 'tail_missing')}
    for row in rows:
        a, b = (outcomes[row['person'], row['case'], v] for v in ('card', 'tail'))
        paired['planned'] += 1
        label = 'both_correct' if a['correct'] and b['correct'] else 'card_only' if a['correct'] else 'tail_only' if b['correct'] else 'neither_correct'
        paired[label] += 1
        paired['card_missing'] += a['missing']
        paired['tail_missing'] += b['missing']
    return {'per_view_strict': pooled, 'profiles': profiles, 'slices': slices,
        'paired_card_tail': paired, 'primary_cases_per_view': 120, 'answers_per_case_per_view': 4,
        'producers_per_person': 1, 'external_reader_decoder': False,
        'hidden_generating_truth_resolves_unknown': False,
        'independent_holdout': False, 'independent_semantic_acceptance': False,
        'generation_stability_verified': False, 'real_person_fidelity_verified': False,
        'old_scores_replaced': False, 'production_default_changed': False}
