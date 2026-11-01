"""One generated graph/two reads; fixed40-case pilot, not generation stability."""
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('graph_pilot_score_plan', HERE / 'plan.py')
prior = load('graph_pilot_count_functions', HERE.parent / 'compression-stability-v1/score.py')
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    key = ('h93', 'graph-v1', 0); card = cards.get(key)
    reads = [responses.get(key+(r,), {}) if card is not None else {} for r in (0, 1)]
    return {'primary_cases': 40, 'generated_cards_planned': 1, 'valid_artifact': card is not None,
        'characters': card['characters'] if card else None, 'first': counts(rows, [reads[0]]),
        'second': counts(rows, [reads[1]]), 'strict_both_reads': counts(rows, reads),
        'within_card_read_disagreement': disagreement(rows, [reads[0]], [reads[1]]),
        'answers_per_case': 4, 'fresh_generation_stability_test': False,
        'independent_semantic_acceptance': False, 'validates_j16_or_development': False,
        'new_original_inventory_coverage': 0, 'production_default_changed': False}
