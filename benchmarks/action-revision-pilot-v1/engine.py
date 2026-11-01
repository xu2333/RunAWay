"""Single-graph pilot finite adapter; backend and human grant are separate injections."""
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plan = load('graph_pilot_finite_plan', HERE / 'plan.py')
score = load('graph_pilot_finite_score', HERE / 'score.py')
runner = load('graph_pilot_finite_runner', HERE.parents[1] / 'scripts/finite_method_controller.py')
write_new, usage = runner.write_new, runner.usage


def run(root, destination, invoke, before, *, simulated):
    return runner.run(root, destination, invoke, before, plan=plan, score=score, simulated=simulated)
