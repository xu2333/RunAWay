"""Prepare an unapproved28-slot collateral comparison on consumed h93/dev."""
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


prior = load('order_regression_isolated_builder', HERE.parent / 'owned-conditions-v1/plan.py')
original_inputs, original_implementation = prior.inputs, prior.implementation
baseline = load('order_regression_old_encoder', HERE.parent / 'action-policy-v2/candidate.py')
candidate = load('order_regression_new_encoder', HERE.parent / 'source-order-v3/candidate.py')
prior.PROFILES, prior.METHODS, prior.CAP = ('h93','dev'), ('policy-v2', 'source-order-v3'), 28
prior.baseline, prior.candidate = baseline, candidate


def inputs():
    data = original_inputs()
    return {'sources': {p:data['sources'][p] for p in ('h93','dev')},
            'queries': {k:data['queries'][k] for k in ('h','dev')},
            **{k:[r for r in data[k] if r['person'] in ('h93','dev')]
               for k in ('rows','legacy_rows','disputed_rows')}}


def request(slot, parents=None):
    if slot not in prior.slots(): raise ValueError('Outside frozen28slot schedule')
    if slot['kind'] != 'extract': return original_request(slot, parents)
    encoder = baseline if slot['method'] == 'policy-v2' else candidate
    return {'model': prior.MODEL, 'system': prior.grouped_support.SYSTEM,
            **encoder.make_request(inputs()['sources'][slot['profile']], prior.BUDGET)}


def bind(slot, answer):
    if slot not in prior.slots() or slot['kind'] != 'extract': raise ValueError('Only own extraction binds')
    encoder = baseline if slot['method'] == 'policy-v2' else candidate
    return encoder.bind(answer, inputs()['sources'][slot['profile']], slot['budget'])


def implementation():
    values = original_implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'source-order-v3/candidate.py',
        HERE.parent / 'action-policy-v2/candidate.py',HERE.parent / 'order-targets-v1/prototype.py',
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
    p.update(kind='unapproved_source_order28_h93_dev_regression',max_new_local_cli_attempts=28,
        stages={'controls':4,'source_only_extractions':8,'bound_reads':16},
        source_messages=62,distinct_public_question_forms=112,legacy_cases=56,
        primary_unflagged_author_cases=56,unscored_disputed_cases=0,
        controls='New full h93 immediately40cases and dev16cases,bothorders,no missing.H93personal-known>h-none;devknown>dev-none.All4control calls before any extraction;any full failure closes before extract5.',
        primary='Per method56fixed author cases:2new generations*2reads*2orders correct.Invalid generations stay missing.No old-card pooling,best-of or combined79claim.',
        methods_are_bundled='Fresh policy-v2 versus unchanged source-order-v3. Same1536whole-char cap,reader,source and dense codec.New optional annotation/guidance/projection is a bundled method,not isolated causal attribution.',
        ownership_proof_limit='Declared graph/source anchors and scope preservation are structural checks,not semantic annotation or source-completeness proof.',
        max_nominal_timeout_sum_seconds=5040,old_cards_responses_or_feedback_sent=False,
        old_raw_cards_responses_scores_or_case_specific_feedback_sent=False,
        development_informed=True,independent_generalization=False,
        source_order22_reused=False,j16_included=False,auxiliary_order_questions_included=False,
        disputed_policy='No j16/w14in this fixed56case scope;no relabeling or new gold acceptance.',
        changes_frozen_source_order_encoder=False)
    values['dynamic-rules.json']['builder'] = 'benchmarks/source-order-regression-v1/plan.py:request'
    out.mkdir(parents=True, exist_ok=False)
    for name, value in values.items(): (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2)+'\n')
    return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
