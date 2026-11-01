"""Prepare an unapproved24-attempt,three-source graph stability study; no backend."""
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


prior = load('graph_stability_isolated_builder', HERE.parent / 'owned-conditions-v1/plan.py')
original_implementation = prior.implementation
candidate = load('graph_stability_same_encoder', HERE.parent / 'action-revision-graph-v1/candidate.py')
prior.candidate, prior.METHODS, prior.CAP = candidate, ('graph-v1',), 24


def implementation():
    values = original_implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'action-revision-graph-v1/candidate.py',
        HERE.parent / 'owned-dense-v1/codec.py', ROOT / 'scripts/finite_method_controller.py']
    values.update({str(p.relative_to(ROOT)): prior.sha(p) for p in paths})
    return dict(sorted(values.items()))


prior.implementation = implementation
PROFILES, METHODS, MODEL, AS_OF, CAP, BUDGET = prior.PROFILES, prior.METHODS, prior.MODEL, prior.AS_OF, prior.CAP, prior.BUDGET
read, sha, digest = prior.read, prior.sha, prior.digest
inputs, parent, bank, bind, request, verify = prior.inputs, prior.parent, prior.bank, prior.bind, prior.request, prior.verify
slots, cells, choice_reader = prior.slots, prior.cells, prior.choice_reader


def prepare(out):
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp) / 'inputs'; prior.prepare(staging)
        values = {n: read(staging / n) for n in read(staging / 'manifest.json')['files']}
    proposal = values['proposal.json']
    proposal.update(kind='unapproved_action_revision_graph24_stability', max_new_local_cli_attempts=24,
        stages={'controls': 6, 'source_only_extractions': 6, 'bound_reads': 12},
        methods=['graph-v1'], generations_per_source_method=2, reads_per_card=2,
        methods_are_bundled='Same frozen action-revision graph encoder and dense compiler as the closed one-card pilot. No method,guide,reader,source or budget revision and no fresh baseline arm.',
        ownership_proof_limit='Compiler preserves declared parent conditions,not semantic edge classification or original-source completeness.',
        primary='79fixed unflagged authored cases,each requiring2new generations*2reads*2orders correct. Invalid/unread generations remain missing. This is8answers/case,not the old one-card4-answer endpoint. No pilot-card pooling or historical causal comparison.',
        max_nominal_timeout_sum_seconds=4320, fresh_generations_planned=6,
        old_cards_responses_or_feedback_sent=False, baseline_arm=False,
        repeat_generation_design=True, independent_generalization=False,
        changes_frozen_encoder_or_renderer=False)
    values['dynamic-rules.json']['builder'] = 'benchmarks/action-revision-stability-v1/plan.py:request'
    out.mkdir(parents=True, exist_ok=False)
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2)+'\n')
    return proposal


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
