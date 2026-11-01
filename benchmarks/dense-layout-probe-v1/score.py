"""Fixed-parent layout scores; expanded material is an uncapped diagnostic."""
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('dense_read_score_plan', HERE / 'plan.py')
prior = load('dense_read_score_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses):
    methods, outcomes = {}, {}
    for method in plan.METHODS:
        reads = [[responses.get(('h93', method, g, r), {}) for r in (0, 1)] for g in (0, 1)]
        generations = {}
        for g in (0, 1):
            v = plan.view({'profile': 'h93', 'method': method, 'generation': g})
            generations[str(g)] = {'fixed_material_available': True, 'characters': v['characters'],
                'memory_ceiling': v['memory_ceiling'], 'view_class': v['view_class'],
                'first': counts(rows, [reads[g][0]]), 'second': counts(rows, [reads[g][1]]),
                'strict_both_reads': counts(rows, reads[g]),
                'within_parent_read_disagreement': disagreement(rows, [reads[g][0]], [reads[g][1]])}
        methods[method] = {'generations': generations, 'strict_all_parents_and_reads': counts(rows, reads[0]+reads[1])}
        outcomes[method] = reads[0]+reads[1]
    pairs = {}
    for other in ('baseline', 'expanded'):
        tally = {k: 0 for k in ('planned', 'both_correct', 'only_dense_correct', 'only_other_correct', 'neither_correct', 'dense_missing', 'other_missing')}
        for row in rows:
            d, b = counts([row], outcomes['dense'])['joint'], counts([row], outcomes[other])['joint']
            tally['planned'] += 1
            label = 'both_correct' if d['correct'] and b['correct'] else 'only_dense_correct' if d['correct'] else 'only_other_correct' if b['correct'] else 'neither_correct'
            tally[label] += 1; tally['dense_missing'] += d['missing']; tally['other_missing'] += b['missing']
        pairs['dense_vs_'+other] = tally
    return {'methods': methods, 'paired_strict': pairs, 'primary_dense_cases': 40,
        'expanded_is_uncapped_diagnostic_not_memory_candidate': True, 'inherited_producer_generations': 2,
        'new_extractions': 0, 'fresh_generation_stability_test': False, 'independent_semantic_acceptance': False,
        'no_best_of_selection': True, 'validates_j16_or_development': False,
        'new_original_inventory_coverage': 0, 'production_default_changed': False}
