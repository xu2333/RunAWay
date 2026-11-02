"""Injected finite runner; no service backend and no experiment grant."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load('long_task_finite_engine', HERE.parent / 'fresh-source-contrast-v1/engine.py')
plan = load('long_task_engine_plan', HERE / 'plan.py')
score = load('long_task_engine_score', HERE / 'score.py')


def run(root, destination, invoke, before, *, simulated):
    return base.original_run(root, destination, invoke, before,
                             plan=plan, score=score, simulated=simulated)
