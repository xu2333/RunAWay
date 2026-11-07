"""Reuse the frozen repeat controller; no live transport, grant or retry."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fresh_decision_plan', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)
shared = plan.load('fresh_decision_shared_engine', plan.ROOT / 'benchmarks/single-pass-repeat-v1/engine.py')
shared.plan = plan
original_summarize = shared.summarize


def summarize(rows, responses):
    result = original_summarize(rows, responses)
    result['cohort_slices'] = {
        cohort: original_summarize([r for r in rows if r['cohort'] == cohort], responses)['joint']
        for cohort in sorted({r['cohort'] for r in rows})}
    return result


shared.summarize = summarize
run = shared.run
