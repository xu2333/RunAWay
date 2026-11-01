"""New unapproved14scope: budget-aware encoding with the same object-table wire."""
import argparse
import json
import tempfile
from pathlib import Path
import importlib.util
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prior = load('budgeted_probe_isolated_plan', HERE.parent / 'object-table-probe-v1/plan.py')
original_implementation = prior.implementation
candidate = load('budgeted_probe_candidate', HERE.parent / 'budgeted-object-table-v1/candidate.py')
prior.candidate, prior.METHODS = candidate, ('scope-v1', 'budgeted-table-v1')


def implementation():
    values = original_implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'budgeted-object-table-v1/candidate.py']
    values.update({str(p.relative_to(ROOT)): prior.sha(p) for p in paths})
    return dict(sorted(values.items()))


prior.implementation = implementation
PROFILES, METHODS, MODEL, AS_OF, CAP, BUDGET = prior.PROFILES, prior.METHODS, prior.MODEL, prior.AS_OF, prior.CAP, prior.BUDGET
read, sha, digest = prior.read, prior.sha, prior.digest
inputs, cells, slots, parent, bank, bind, request, verify = prior.inputs, prior.cells, prior.slots, prior.parent, prior.bank, prior.bind, prior.request, prior.verify
baseline, choice_reader, grouped_support = prior.baseline, prior.choice_reader, prior.grouped_support


def prepare(out):
    # Stage the reused builder in a temporary folder. Only the final new-scope
    # files and manifest are written to the exclusive destination; no sealed
    # historical package or existing approved scope is modified.
    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp) / 'inputs'
        prior.prepare(staged)
        names = read(staged / 'manifest.json')['files']
        values = {n: read(staged / n) for n in names}
    proposal = values['proposal.json']
    proposal.update(kind='unapproved_budgeted_object_table14_consumed_h93_probe',
        method='Fresh scope-v1 versus budget-aware object-table encoder. Same wire/compiler/renderer/codec/reader and1536public-character ceiling. Candidate now sees source,budget,fixed header/guide,plus concise-question guidance. Does not repair old cards or test j16/w11;not a pure budget-information ablation.',
        encoder_sees_budget=True, changes_only_encoder_request_relative_to_table_wire=True,
        pure_budget_information_effect_isolated=False)
    values['dynamic-rules.json']['builder'] = 'benchmarks/budgeted-table-probe-v1/plan.py:request'
    out.mkdir(parents=True, exist_ok=False)
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2) + '\n')
    return proposal


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
