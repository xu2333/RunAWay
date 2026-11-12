"""Dependency-injected finite runner; it cannot contact a model on its own."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


plan = load('domain_revision_engine_plan', HERE / 'plan.py')
score = load('domain_revision_engine_score', HERE / 'score.py')
gate = load('domain_revision_engine_gate', HERE / 'gate.py')
base = load('domain_revision_engine_io', HERE.parent / 'fresh-source-contrast-v1/engine.py')
usage = base.usage


def run(root, destination, invoke, before, *, simulated, approval=None, verify_human_grant=None):
    if type(simulated) is not bool: raise ValueError('Explicit boolean execution mode required')
    if not simulated: gate.verify(root, approval, verify_human_grant)
    return base.original_run(root, destination, invoke, before, plan=plan, score=score, simulated=simulated)
