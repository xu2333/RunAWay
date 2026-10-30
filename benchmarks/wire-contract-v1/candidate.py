"""Unmeasured when-field wire alignment; source, prompt and binder unchanged."""
import copy
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('wire_alignment_policy', ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def make_request(sources, budget=768):
    req = copy.deepcopy(base.make_request(sources, budget))
    when = req['schema']['properties']['groups']['items']['properties']['rules']['items']['properties']['when']
    when.update(minLength=1, maxLength=120)
    return req


def bind(answer, sources, budget=768):
    return base.bind(answer, sources, budget)
