"""Injected finite runner only; real use needs a separately verified direct grant."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m); return m


plan = load('direct768_engine_plan', HERE / 'plan.py')
score = load('direct768_engine_score', HERE / 'score.py')
base = load('direct768_finite_io', HERE.parent / 'fresh-source-contrast-v1/engine.py')
gate = load('direct768_engine_gate', HERE / 'gate.py')
usage = base.usage


def run(root, destination, invoke, before, *, simulated, approval=None, verify_human_grant=None):
    if type(simulated) is not bool:
        raise ValueError('Explicit boolean execution mode required')
    if not simulated:
        gate.verify(root, approval, verify_human_grant)
    return base.original_run(root, destination, invoke, before, plan=plan, score=score, simulated=simulated)
