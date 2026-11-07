"""Reuse finite injected controller; this module provides no service transport."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('accounted_engine_plan', HERE / 'plan.py')
score = load('accounted_engine_score', HERE / 'score.py')
base = load('accounted_existing_controller', plan.ROOT / 'benchmarks/fresh-source-contrast-v1/engine.py')
usage = base.usage


def run(root, destination, invoke, before, *, simulated):
    return base.original_run(root, destination, invoke, before,
                             plan=plan, score=score, simulated=simulated)
