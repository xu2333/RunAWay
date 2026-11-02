"""Two-method56-case collateral comparison; no j16 pooling."""
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


plan = load('order_regression_score_plan', HERE / 'plan.py')
prior = load('order_regression_score_functions', HERE.parent / 'owned-conditions-v1/score.py')
prior.plan = plan
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    result = prior.summarize(rows, responses, cards)
    result.update(primary_cases_per_method=56, legacy_cases=56, disputed_cases=0,
                  semantic_annotation_independently_accepted=False,validates_j16=False,pooled79case_claim=False)
    return result
