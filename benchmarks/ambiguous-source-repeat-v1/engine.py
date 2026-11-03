"""Finite injected comparison runner; live execution needs a separate human gate."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
plan=load('coverage_engine_plan',HERE/'plan.py')
score=load('coverage_engine_score',HERE/'score.py')
base=load('coverage_existing_controller',plan.ROOT/'benchmarks/epistemic-transfer-v1/engine.py')
usage=base.usage

def run(root,destination,invoke,before,*,simulated):
 return base.base.original_run(root,destination,invoke,before,plan=plan,score=score,simulated=simulated)
