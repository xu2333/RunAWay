"""Fresh shopping-plan replay with two extraction methods and one fixed reader."""
import importlib.util
from pathlib import Path

BENCHMARKS = Path(__file__).resolve().parents[1]


def load(folder, name):
    spec = importlib.util.spec_from_file_location(name, BENCHMARKS / folder / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


transfer = load('real-model-selection-transfer-v1', 'protocol')
encoder = load('real-selection-name-extraction-v1', 'encoder')
EXTRACTIONS = encoder.EXTRACTIONS
FIRST_HALF = ('none', 'candidate1', 'original2', 'full', 'original1', 'candidate2')
DELIVERIES = FIRST_HALF + FIRST_HALF[::-1]
REQUIREMENTS = ('quality', 'television', 'bundle', 'membership', 'discount_eligibility', 'cashback')


def prepare(case):
    sources, original, controls = transfer.prepare(case)
    return sources, dict(original=original, candidate=encoder.candidate_request(original), **controls)


def delivery(arm, requests, cards):
    if arm in ('none', 'full'):
        request = requests[arm]
    elif arm in EXTRACTIONS:
        request = transfer.cards.card_request(requests['none'], cards[arm])
    else:
        raise ValueError('Unknown delivery condition')
    return transfer.reader.revised_request(request)


def joint(criteria):
    return all(criteria[key] == 'met' for key in REQUIREMENTS)
