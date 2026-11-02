"""One producer/person, two reads/two orders; missing stays in 40-case denominator."""
from collections import Counter
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('long_task_score_plan', HERE / 'plan.py')
prior = load('long_task_count_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    pooled, profiles, outcomes = {}, {}, {}
    for view in ('card', 'tail'):
        totals = {key: Counter() for key in counts([], [{}])}
        for pid in plan.PROFILES:
            key = pid, plan.METHODS[0], 0
            card = cards.get(key)
            answers = [responses.get(key + (view, repeat), {}) if card else {} for repeat in (0, 1)]
            own = [r for r in rows if r['person'] == pid]
            strict = counts(own, answers)
            source_chars = len(plan.transcript(plan.inputs()['sources'][pid]))
            profiles[pid + ':' + view] = {
                'valid_parent': card is not None,
                'characters': len(plan.material(pid, card['prompt'], view)) if card else None,
                'source_characters': source_chars,
                'source_to_view_character_ratio': source_chars / card['characters'] if card else None,
                'first': counts(own, [answers[0]]), 'second': counts(own, [answers[1]]),
                'strict_both_reads': strict,
                'within_parent_read_disagreement': disagreement(own, [answers[0]], [answers[1]]),
                'by_task': {task: counts([r for r in own if r['task'] == task], answers)
                            for task in sorted({r['task'] for r in own})}}
            for name, value in strict.items():
                totals[name].update(value)
            for row in own:
                outcomes[pid, row['case'], view] = counts([row], answers)['joint']
        pooled[view] = {k: dict(v) for k, v in totals.items()}
    paired = {k: 0 for k in ('planned', 'both_correct', 'card_only', 'tail_only', 'neither_correct', 'card_missing', 'tail_missing')}
    for row in rows:
        a, b = (outcomes[row['person'], row['case'], v] for v in ('card', 'tail'))
        paired['planned'] += 1
        category = 'both_correct' if a['correct'] and b['correct'] else 'card_only' if a['correct'] else 'tail_only' if b['correct'] else 'neither_correct'
        paired[category] += 1
        paired['card_missing'] += a['missing']
        paired['tail_missing'] += b['missing']
    pairs = []
    for donor in plan.PROFILES:
        recipient = plan.corpus.PAIRS[donor]
        own = {r['case']: r for r in rows if r['person'] == donor}
        divergent = [r for r in rows if r['person'] == recipient and r['gold'] != own[r['case']]['gold']]
        key = donor, plan.METHODS[0], 0
        answers = [responses.get(key + ('card', repeat), {}) if key in cards else {} for repeat in (0, 1)]
        pairs.append({'donor': donor, 'recipient': recipient, 'divergent_cases': counts(divergent, answers),
                      'new_calls': 0, 'independent_evidence': False})
    return {'per_view_strict': pooled, 'profiles': profiles, 'paired_card_tail': paired,
            'dependent_pair_rescoring': pairs, 'primary_cases_per_view': 40,
            'answers_per_case_per_view': 4, 'producers_per_person': 1,
            'generation_stability_verified': False, 'independent_holdout': False,
            'independent_semantic_acceptance': False, 'real_person_fidelity_verified': False,
            'character_ratio_is_token_ratio_or_economic_savings': False,
            'old_benchmark_scores_replaced': False, 'production_default_changed': False}
