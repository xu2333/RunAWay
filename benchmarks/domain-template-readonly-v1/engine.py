"""Reuse the frozen question-contract finite controller with one common task.

That controller has generic plan/score dependencies. A separate module instance
binds this scope's one question bank and two fixed views;no backend is supplied.
"""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


plan=load('domain_readonly_engine_plan',HERE/'plan.py')
score=load('domain_readonly_engine_score',HERE/'score.py')
gate=load('domain_readonly_engine_gate',HERE/'gate.py')
base=load('domain_readonly_finite_io',HERE.parent/'question-contract-diagnostic-v1/engine.py')
base.plan,base.score=plan,score
usage=base.usage


def run(root,destination,invoke,before,*,simulated,approval=None,verify_human_grant=None):
    if type(simulated)is not bool:raise ValueError('Explicit boolean execution mode required')
    if not simulated:gate.verify(root,approval,verify_human_grant)
    return base.run(root,destination,invoke,before,simulated=simulated)
