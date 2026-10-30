"""New-scope adapter for the unchanged injected finite controller; no backend."""
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


core = load('remaining_finite_core', HERE.parent / 'compression-stability-v1/engine.py')
plan = load('remaining_finite_plan', HERE / 'plan.py')
score = load('remaining_finite_score', HERE / 'score.py')
# Each load creates an isolated module object. Neither the original controller
# nor its41scope global state is modified. Both dependencies are frozen here.
core.plan, core.score = plan, score
write_new, usage = core.write_new, core.usage


def run(root, destination, invoke, before, *, simulated):
    first = plan.slots()[:4]
    if [s['kind'] for s in first] != ['none', 'full', 'full', 'full']:
        raise ValueError('All3full controls must precede extraction')
    return core.run(root, destination, invoke, before, simulated=simulated)
