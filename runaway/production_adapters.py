"""Offline-first adapters for the actual browser and program-bound compressors.

No service is selected or invoked by this module. The caller must explicitly
provide a checkpointed call object (e.g. selfplay.Calls with an approved backend).
Mock/replayed answers test plumbing, never establish model compression quality.
"""
import argparse
import json
from pathlib import Path

from . import bound_memory
from .card import canonical, digest
from .pipeline import write_once
from .selfplay import BROWSER_SCHEMA, browser
from .synthetic_metric import ROOT, frozen_data, PROTOCOL

FILES = (
    'runaway/production_adapters.py', 'runaway/selfplay.py',
    'runaway/bound_memory.py', 'runaway/decision_memory.py',
    'runaway/compression.py', 'runaway/profile.py', 'runaway/review.py',
    'runaway/portable.py', 'runaway/card.py', 'runaway/text_integrity.py',
    'runaway/generation.py', 'runaway/execution_ledger.py',
    'runaway/pipeline.py', 'runaway/metric_jobs.py',
    'web/dist/core.mjs', 'web/dist/manual-core.mjs',
    'web/dist/text-integrity.mjs', 'scripts/selfplay-browser.mjs',
    'scripts/read-stdin-json.mjs',
)
CONDITIONS = ['current_browser', 'new_bound']


def hashes():
    return {name: digest((ROOT / name).read_text(encoding='utf-8')) for name in FILES}


def sources(history):
    # The natural-language history is the entire input. No event truth, seed,
    # query, answer, split, twin identity or metric strata enter model requests.
    return {'schema_version': 1, 'sources': [
        {'id': 'history', 'episode_id': 'synthetic', 'role': 'user', 'text': history},
        {'id': 'protocol', 'episode_id': 'synthetic', 'role': 'context', 'text': PROTOCOL}]}


def freeze(out, metric_run, budgets, generator_model):
    metric_run = Path(metric_run).resolve()
    metric_plan, world = frozen_data(metric_run)
    if (not budgets or len(set(budgets)) != len(budgets)
            or any(type(b) is not int or b <= 0 or b not in metric_plan['budgets'] for b in budgets)):
        raise ValueError('Choose positive unique frozen metric budgets')
    if not isinstance(generator_model, str) or not generator_model.strip():
        raise ValueError('Freeze an explicit generator model')
    people = [p['id'] for p in world['people'] if p['split'] == 'eval']
    cells = len(people) * len(budgets)
    body = {
        'schema_version': 1, 'metric_plan_id': metric_plan['id'],
        'metric_run': str(metric_run), 'people': people, 'budgets': list(budgets),
        'tokenizer': metric_plan['tokenizer'], 'generator_model': generator_model,
        'conditions': CONDITIONS, 'source_hashes': hashes(),
        'character_budgets': {str(b): min(16000, max(200, 2*b)) for b in budgets},
        'budget_policy': 'Fixed character request limit max(200,min(16000,2*budget)); '
                         'actual full rendered token/byte count checked separately; reject, never truncate or retry.',
        'stages': [
            {'id': 'shared_extraction', 'calls_upper_bound': cells,
             'implementation': 'selfplay.browser request + BROWSER_SCHEMA + browser validate/makeBundle',
             'outputs': ['current_browser memory', 'shared evidence-linked profile']},
            {'id': 'new_compression', 'calls_upper_bound': cells,
             'implementation': 'bound_memory.make_request + SCHEMA + bind',
             'input': 'The same extracted profile, including original evidence; no gold.'}],
        'calls_upper_bound': 2*cells, 'automatic_retries': 0,
        'methodology': 'Paired comparison conditional on shared extraction. Current uses one model call/cell; '
                       'new additionally uses one compression call/cell. Shared extraction cost counted once '
                       'in batch and charged to each method when reporting standalone pipeline cost.',
        'semantic_audit_calls': 0, 'semantic_preservation_verified': False,
        'true_person_fidelity_verified': False,
    }
    plan = {**body, 'id': digest(canonical(body))}
    dest = Path(out); dest.mkdir(parents=True, exist_ok=False)
    write_once(dest/'adapter-plan.json', plan)
    for name in FILES:
        target = dest/'frozen-source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    return plan


def load_plan(root):
    plan = json.loads((Path(root)/'adapter-plan.json').read_text(encoding='utf-8'))
    if (plan['id'] != digest(canonical({k:v for k,v in plan.items() if k != 'id'}))
            or plan['source_hashes'] != hashes()):
        raise ValueError('Adapter plan or source changed; freeze a new run')
    metric_plan, world = frozen_data(plan['metric_run'])
    if plan['metric_plan_id'] != metric_plan['id']:
        raise ValueError('Metric plan changed')
    return plan, world


def run(root, calls, count, tokenizer):
    """Call actual product functions with an explicitly injected call executor.

    A transport/model-call failure halts further calls; local validator failures
    do not trigger repairs. All planned outputs, including skipped ones, remain.
    Exact request replay/reuse and invocation accounting belong to ``calls``.
    """
    plan, world = load_plan(root)
    if tokenizer != plan['tokenizer']:
        raise ValueError('Tokenizer identity differs from frozen metric plan')
    rows, stages, stopped = [], [], False
    for person in (p for p in world['people'] if p['id'] in plan['people']):
        for budget in plan['budgets']:
            values = {key: None for key in CONDITIONS}
            failures = {key: 'Skipped after backend failure' if stopped else None for key in CONDITIONS}
            source = sources(person['history']); chars = plan['character_budgets'][str(budget)]
            bundle = None
            for stage in ('shared_extraction', 'new_compression'):
                if stopped or (stage == 'new_compression' and bundle is None):
                    stages.append({'persona_id':person['id'], 'budget':budget, 'stage':stage, 'status':'skipped'})
                    continue
                try:
                    request = (browser('request', source, chars)['request'] if stage == 'shared_extraction'
                               else bound_memory.make_request(bundle['profile'], chars))
                except ValueError as exc:
                    affected = CONDITIONS if stage == 'shared_extraction' else ['new_bound']
                    for key in affected: failures[key] = str(exc)
                    stages.append({'persona_id':person['id'], 'budget':budget, 'stage':stage, 'status':'request_failed'})
                    continue
                schema = BROWSER_SCHEMA if stage == 'shared_extraction' else bound_memory.SCHEMA
                try:
                    answer = calls.call(request, schema, plan['generator_model'])
                except Exception:
                    # Calls persists the original diagnostic privately. Never
                    # leak arbitrary backend exception text into a public report.
                    stopped = True
                    affected = CONDITIONS if stage == 'shared_extraction' else ['new_bound']
                    for key in affected: failures[key] = 'Backend failed; no automatic retry'
                    stages.append({'persona_id':person['id'], 'budget':budget, 'stage':stage, 'status':'backend_failed'})
                    continue
                text, units = None, None
                try:
                    if stage == 'shared_extraction':
                        bundle = browser('validate', source, chars, answer)
                        text = bundle['portable']['text']; key = 'current_browser'
                    else:
                        text, _ = bound_memory.bind(answer, bundle['profile'], chars); key = 'new_bound'
                    units = count(text)
                    if type(units) is not int or units < 0:
                        raise ValueError('Tokenizer returned invalid count')
                    if units > budget:
                        raise ValueError('Actual memory exceeds frozen budget; no truncation')
                    values[key] = text
                    stages.append({'persona_id':person['id'], 'budget':budget, 'stage':stage,
                                   'status':'usable', 'units':units, 'characters':len(text),
                                   'memory_sha256':digest(text)})
                except ValueError as exc:
                    affected = CONDITIONS if bundle is None else [
                        'current_browser' if stage == 'shared_extraction' else 'new_bound']
                    for key in affected: failures[key] = str(exc)
                    stages.append({'persona_id':person['id'], 'budget':budget, 'stage':stage,
                                   'status':'validation_failed', 'units':units,
                                   'characters':len(text) if text is not None else None})
            for condition in CONDITIONS:
                rows.append({'persona_id':person['id'], 'condition':condition, 'budget':budget,
                             'memory':values[condition], 'failure':failures[condition]})
    result = {'adapter_plan_id':plan['id'], 'rows':rows, 'stages':stages,
              'stopped_after_backend_failure':stopped,
              'quality_claim':'None: model output provenance and independent decoder scores required.'}
    write_once(Path(root)/'adapter-result.private.json', result)
    write_once(Path(root)/'memories.private.json', rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metric-run', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--budgets', required=True)
    parser.add_argument('--generator-model', required=True)
    args = parser.parse_args()
    plan = freeze(args.out, args.metric_run, [int(v) for v in args.budgets.split(',')], args.generator_model)
    print(json.dumps({'plan_id':plan['id'], 'calls_upper_bound':plan['calls_upper_bound'],
                      'external_calls_made':0}))


if __name__ == '__main__': main()
