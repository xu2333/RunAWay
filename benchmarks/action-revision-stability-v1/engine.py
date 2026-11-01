"""Injected24-slot runner; no service backend or grant issuer."""
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


plan = load('graph_stability_engine_plan', HERE / 'plan.py')
score = load('graph_stability_engine_score', HERE / 'score.py')
runner = load('graph_stability_engine_runner', HERE.parents[1] / 'scripts/finite_method_controller.py')
write_new, usage = runner.write_new, runner.usage


def run(root, destination, invoke, before, *, simulated):
    return runner.run(root, destination, invoke, before, plan=plan, score=score, simulated=simulated)
