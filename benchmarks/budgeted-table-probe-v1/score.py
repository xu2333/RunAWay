"""Reuse isolated paired method functions on40planned h93cases; no new gold."""
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('budgeted_probe_score_plan', HERE / 'plan.py')
core = load('budgeted_probe_score_core', HERE.parent / 'owned-conditions-v1/score.py')
core.plan = plan
counts, disagreement = core.counts, core.disagreement


def summarize(rows, responses, cards):
    result = core.summarize(rows, responses, cards)
    result.update(primary_cases_per_method=40, legacy_cases=40, disputed_cases=0)
    return result
