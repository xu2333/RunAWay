"""Prepare5unapproved calls for one fresh source-only revision graph and two reads."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prior = load('graph_pilot_isolated_source_builder', HERE.parent / 'object-table-probe-v1/plan.py')
original_implementation = prior.implementation
candidate = load('graph_pilot_encoder', HERE.parent / 'action-revision-graph-v1/candidate.py')
prior.candidate, prior.METHODS, prior.CAP = candidate, ('graph-v1',), 5


def slots():
    jobs = [('none', 'shared_h', None, None), ('full', 'h93', None, None),
            ('extract', 'h93', 'graph-v1', None), ('read', 'h93', 'graph-v1', 0), ('read', 'h93', 'graph-v1', 1)]
    return [{'slot': i+1, 'kind': k, 'profile': p, 'method': m, 'generation': 0 if m else None,
        'read_repeat': r, 'budget': 1536 if m else None,
        'key': ':'.join(map(str, (k, p, m, 0 if m else None, r)))} for i, (k, p, m, r) in enumerate(jobs)]


prior.slots = slots


def implementation():
    values = original_implementation()
    paths = list(HERE.glob('*.py')) + [HERE.parent / 'action-revision-graph-v1/candidate.py', HERE.parent / 'owned-dense-v1/codec.py']
    values.update({str(p.relative_to(ROOT)): prior.sha(p) for p in paths})
    return dict(sorted(values.items()))


prior.implementation = implementation
PROFILES, METHODS, MODEL, AS_OF, CAP, BUDGET = prior.PROFILES, prior.METHODS, prior.MODEL, prior.AS_OF, prior.CAP, prior.BUDGET
read, sha, digest = prior.read, prior.sha, prior.digest
inputs, parent, bank, bind, request, verify = prior.inputs, prior.parent, prior.bank, prior.bind, prior.request, prior.verify
choice_reader, grouped_support = prior.choice_reader, prior.grouped_support


def prepare(out):
    with tempfile.TemporaryDirectory() as temp:
        staging = Path(temp) / 'inputs'; prior.prepare(staging)
        values = {n: read(staging / n) for n in read(staging / 'manifest.json')['files']}
    p = values['proposal.json']
    p.update(kind='unapproved_action_revision_graph5_h93_pilot', max_new_local_cli_attempts=5,
        stages={'controls': 2, 'source_only_extractions': 1, 'bound_reads': 2},
        methods=['graph-v1'], generations_per_method=1, reads_per_card=2,
        method='One fresh source-only typed action-revision graph,compiled to the unchanged dense syntax. Action-only edges inherit parent conditions;independent bases do not automatically inherit unrelated ordinary conditions. Edge meaning/completeness remains unverified.',
        primary='One generated card,40fixed cases,each requires both reads*bothorders correct. This is4answers/case,not the8-answer two-parent endpoint in prior studies. Keep missing40if graph invalid. No fresh-card baseline,causal improvement or producer-stability claim.',
        max_nominal_timeout_sum_seconds=900, current_unknown_loss_is_not_a_new_gold=True,
        fresh_generation_stability_test=False, old_model_outputs_cards_or_feedback_sent=False)
    values['dynamic-rules.json']['builder'] = 'benchmarks/action-revision-pilot-v1/plan.py:request'
    out.mkdir(parents=True, exist_ok=False)
    for name, value in values.items():
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (out / 'manifest.json').write_text(json.dumps({'files': {n: sha(out / n) for n in sorted(values)}, 'new_model_calls': 0}, indent=2)+'\n')
    return p


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path, required=True)
    args = p.parse_args(); print(json.dumps(prepare(args.out), ensure_ascii=False, indent=2))
