"""Finite injected runner. Actual service requires a separate exact human gate."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


base = load('epistemic_finite_base', HERE.parent / 'fresh-source-contrast-v1/engine.py')
plan = load('epistemic_engine_plan', HERE / 'plan.py')
score = load('epistemic_engine_score', HERE / 'score.py')
usage = base.usage


def run(root, destination, invoke, before, *, simulated):
    return base.original_run(root, destination, invoke, before,
                             plan=plan, score=score, simulated=simulated)
