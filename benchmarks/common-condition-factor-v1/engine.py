"""Injected fixed-view runner;no backend,grant issuer or transport CLI."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
plan=load('common_factor_engine_plan',HERE/'plan.py')
score=load('common_factor_engine_score',HERE/'score.py')
base=load('common_factor_injected_runner',HERE.parent/'orthogonal-condition-diagnostic-v1/engine.py')
base.plan,base.score=plan,score
usage=base.usage

def run(root,destination,invoke,before,*,simulated):
 return base.run(root,destination,invoke,before,simulated=simulated)
