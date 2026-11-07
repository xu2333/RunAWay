"""Same strict30-case counts; source bookkeeping is not a fidelity endpoint."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('accounted_original_score', HERE.parent / 'ambiguous-source-repeat-v1/score.py')
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)
spec = importlib.util.spec_from_file_location('accounted_score_plan', HERE / 'plan.py')
plan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan)
counts, disagreement = original.counts, original.disagreement


def summarize(rows, responses, cards):
    # The existing aggregator is parameterized by its plan module. Keep a local
    # function/global namespace instead of mutating the imported frozen module.
    import types
    globals_for_run = dict(original.__dict__, plan=plan)
    pooled = types.FunctionType(original.summarize.__code__, globals_for_run)
    result = pooled(rows, responses, cards)
    result['source_only_generic_guidance_intervention'] = False
    result['source_accounted_schema_intervention'] = True
    result['source_accounting_is_behavioral_endpoint'] = False
    return result
