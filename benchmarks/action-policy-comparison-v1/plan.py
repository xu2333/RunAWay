"""Prepare an unapproved14-slot encoding-guidance comparison on consumed j16."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


prior = load('action_policy_isolated_builder', HERE.parent / 'owned-conditions-v1/plan.py')
original_inputs, original_implementation = prior.inputs, prior.implementation
baseline = load('action_policy_old_encoder', HERE.parent / 'action-revision-graph-v1/candidate.py')
candidate = load('action_policy_new_encoder', HERE.parent / 'action-policy-v2/candidate.py')
prior.PROFILES, prior.METHODS, prior.CAP = ('j16',), ('graph-v1', 'policy-v2'), 14
prior.baseline, prior.candidate = baseline, candidate


def inputs():
    data = original_inputs()
    return {'sources': {'j16': data['sources']['j16']}, 'queries': {'j': data['queries']['j']},
            **{k: [r for r in data[k] if r['person'] == 'j16'] for k in ('rows', 'legacy_rows', 'disputed_rows')}}


def request(slot, parents=None):
    if slot not in prior.slots(): raise ValueError('Outside frozen14slot schedule')
    if slot['kind'] != 'extract': return original_request(slot, parents)
    encoder = baseline if slot['method'] == 'graph-v1' else candidate
    return {'model': prior.MODEL, 'system': prior.grouped_support.SYSTEM,
            **encoder.make_request(inputs()['sources']['j16'], prior.BUDGET)}


def bind(slot, answer):
    if slot not in prior.slots() or slot['kind'] != 'extract': raise ValueError('Only own extraction binds')
    encoder = baseline if slot['method'] == 'graph-v1' else candidate
    return encoder.bind(answer, inputs()['sources']['j16'], slot['budget'])


def implementation():
    values = original_implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'action-policy-v2/candidate.py',
        HERE.parent / 'action-revision-graph-v1/candidate.py', HERE.parent / 'owned-dense-v1/codec.py',
        ROOT / 'scripts/finite_method_controller.py']
    values.update({str(p.relative_to(ROOT)): prior.sha(p) for p in paths})
    return dict(sorted(values.items()))


original_request = prior.request
prior.inputs, prior.request, prior.bind, prior.implementation = inputs, request, bind, implementation
PROFILES, METHODS, MODEL, AS_OF, CAP, BUDGET = prior.PROFILES, prior.METHODS, prior.MODEL, prior.AS_OF, prior.CAP, prior.BUDGET
read, sha, digest = prior.read, prior.sha, prior.digest
slots, cells, parent, bank, verify, choice_reader = prior.slots, prior.cells, prior.parent, prior.bank, prior.verify, prior.choice_reader


def prepare(out):
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp) / 'inputs'; prior.prepare(staging)
        values = {n: read(staging / n) for n in read(staging / 'manifest.json')['files']}
    p = values['proposal.json']
    p.update(kind='unapproved_action_policy14_j16_comparison', max_new_local_cli_attempts=14,
        stages={'controls': 2, 'source_only_extractions': 4, 'bound_reads': 8},
        source_messages=34, distinct_public_question_forms=48, legacy_cases=24,
        primary_unflagged_author_cases=23, unscored_disputed_cases=1,
        controls='New full immediately23primary cases,bothorders,no missing,personal-known>new no-memory;w14excluded. Failure stops before extract3.',
        primary='Per method23fixed cases,each needs2fresh generations*2reads*2orders correct;invalid generations stay missing. No old-card pooling or best-of.',
        methods_are_bundled='Same graph schema shape/compiler,dense renderer,reader and1536cap. Only source-only encoding guidance/version changes. Guidance about action labels and complete policy restatement is bundled;no individual-component causal claim.',
        ownership_proof_limit='Existing conditional graph invariants remain. New semantic guidance has no new structural proof or observed efficacy.',
        max_nominal_timeout_sum_seconds=2520, old_cards_responses_or_feedback_sent=False,
        guidance_informed_by_prior_consumed_development_failures=True,
        old_raw_cards_responses_scores_or_case_specific_feedback_sent=False)
    values['dynamic-rules.json']['builder'] = 'benchmarks/action-policy-comparison-v1/plan.py:request'
    out.mkdir(parents=True, exist_ok=False)
    for name, value in values.items(): (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2)+'\n')
    return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
