"""Compose the frozen extraction and reading methods on a new retrospective task."""
import importlib.util
from pathlib import Path

BENCHMARKS = Path(__file__).resolve().parents[1]


def load_builder(folder, name):
    spec = importlib.util.spec_from_file_location(name, BENCHMARKS / folder / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cards = load_builder('real-recording-card-v1', 'protocol')
boundary = load_builder('real-control-boundary-v1', 'comparison')
switch = load_builder('real-control-switch-v1', 'encoder')
reader = load_builder('real-fixed-card-reader-v1', 'reader')

EXTRACTIONS = ('card1', 'card2')
DELIVERIES = ('none', 'full', 'card1_old', 'card2_new', 'card1_new', 'card2_old',
              'card2_old', 'card1_new', 'card2_new', 'card1_old', 'full', 'none')


def prepare(case):
    sources, original, controls = cards.prepare(case)
    return sources, switch.switch_request(boundary.candidate_request(original)), controls


def make_delivery(arm, controls, fixed_cards):
    if arm in ('none', 'full'):
        return controls[arm]
    if arm not in DELIVERIES:
        raise ValueError('Unknown delivery condition')
    card, method = arm.split('_')
    original = cards.card_request(controls['none'], fixed_cards[card])
    return reader.revised_request(original) if method == 'new' else original
