"""Two-method23-case nested comparison; original disputed case stays unscored."""
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


plan = load('action_policy_score_plan', HERE / 'plan.py')
prior = load('action_policy_score_functions', HERE.parent / 'owned-conditions-v1/score.py')
prior.plan = plan
counts, disagreement = prior.counts, prior.disagreement


def summarize(rows, responses, cards):
    result = prior.summarize(rows, responses, cards)
    result.update(primary_cases_per_method=23, legacy_cases=24, disputed_cases=1,
                  new_semantic_guidance_verified=False)
    return result
