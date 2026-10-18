"""Offline four-call scale/repair replay against the exact frozen package."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def replay(base, count=None):
    if sys.flags.optimize:
        raise ValueError('Evidence replay requires assertions enabled')
    base = Path(base).resolve()
    frozen = base / 'frozen-source'
    contract = json.loads((base / 'contract.synthetic.json').read_text())
    profile = contract.get('replay_profile', 'scale')
    profiles = {'scale': ('D-0023', 'runs/temporal-scale-v1/runner.py'),
                'conflict_repair': ('D-0026', 'runs/temporal-conflict-repair-v1/runner.py'),
                'conflict_transfer': ('D-0027', 'runs/temporal-conflict-transfer-v1/runner.py')}
    if profile not in profiles: raise ValueError('Unknown frozen replay profile')
    decision, runner_path = profiles[profile]
    for name, sha in contract['source_hashes'].items():
        assert hashlib.sha256((frozen / name).read_bytes()).hexdigest() == sha
    for name, sha in contract['input_hashes'].items():
        assert hashlib.sha256((base / contract['input_aliases'][name]).read_bytes()).hexdigest() == sha
    sys.path.insert(0, str(frozen))
    from runaway import generation
    from runaway.card import canonical, digest
    from runaway.execution_ledger import collect, summarize, checked
    spec = importlib.util.spec_from_file_location('frozen_scale', frozen / runner_path)
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline replay must never invoke a model')
    generation.codex_generate = forbidden
    read = lambda n: json.loads((base / n).read_text())
    report, world, jobs = read('raw-report.synthetic.json'), read('world.synthetic.json'), read('jobs.json')
    assert report['backend_kind'] == 'actual_service'
    controls = s.old_controls(world, read('prior-controls.synthetic.json'))
    assert controls == report['prior_controls_reused_offline_not_new']
    records = collect(base)
    ledger = summarize(records)
    assert ledger == report['calls'] and len(records) == report['external_model_calls'] <= 4
    responses = {r['request_id']: checked(base / 'calls' / (r['request_id'] + '.response.json'))
                 for r in records if r['outcome'] == 'completed'}
    labels = {}; consumed = set()
    def answer(request, stage):
        key = digest(canonical(request))
        assert read('calls/' + key + '.request.json') == request
        labels[key] = stage; consumed.add(key)
        return responses[key]['answer']
    artifacts, memories, checks, predictions = {}, {}, {}, {}
    reproduced_error = None
    try:
        for person, job in zip(world['people'], jobs):
            pid = person['id']
            artifact = s.t.bind(answer(job['request'], 'shared_extraction'), job['sources'])
            artifacts[pid] = artifact
            check = s.source_checks(person, artifact); checks[pid] = check
            if not check['event_span_coverage'] or not all(check['retraction_edges']) or not all(check['current_contexts']) or (profile != 'scale' and not all(check['current_statuses'])):
                reproduced_error = 'source_to_event_gate_failed'; break
            memory = s.t.render(artifact, 768, count=count, budget_tokens=384) if count else s.t.render(artifact, 768)
            if count is None:
                memory['budget_tokens'] = report['memories'][pid]['budget_tokens']
                memory['required_tokens'] = report['memories'][pid]['required_tokens']
                if memory['required_tokens'] > 384:
                    memory['status'] = 'budget_blocked'; memory['text'] = None
            memories[pid] = memory
            if memory['status'] != 'candidate_unvalidated':
                reproduced_error = 'whole_prompt_budget_failed'; break
        if reproduced_error is None:
            for person in world['people']:
                pid = person['id']; public = [c['public'] for c in person['cases']]
                job = s.reader_job('temporal_scale', pid, memories[pid]['text'], public, s.fs.READER, 12)
                predictions[pid] = s.answers_checked(answer(job['request'], 'actual_memory_reader'), public)
    except (ValueError, KeyError) as error:
        reproduced_error = {'type': type(error).__name__, 'message': str(error)}
    assert artifacts == report['artifacts'] and memories == report['memories']
    assert checks == report['source_to_event_checks']
    assert predictions == read('answers.synthetic.json')
    scores = {task: s.fs.score(world, predictions, task) for task in ('current_choice', 'historical_reconstruction', 'joint')}
    assert scores == report['scores']
    assert (scores['current_choice']['planned'], scores['historical_reconstruction']['planned'], scores['joint']['planned']) == (112, 38, 150)
    if report['status'] == 'complete':
        assert reproduced_error is None and len(records) == 4
        assert ledger['executions_missing_usage'] == 0 and all(r['outcome'] == 'completed' for r in records)
        assert set(labels) == {r['request_id'] for r in records}
        assert all(len(c['current_contexts']) == 27 and all(c['current_contexts']) and c['event_span_coverage'] and all(c['retraction_edges']) for c in checks.values())
        if profile != 'scale': assert all(len(c['current_statuses']) == 27 and all(c['current_statuses']) for c in checks.values())
    else:
        assert report['status'] == 'stopped' and reproduced_error is not None
    stages = {stage: summarize([r for r in records if labels.get(r['request_id']) == stage]) for stage in s.STAGES}
    assert {stage: cost['execution_records'] for stage, cost in stages.items() if cost['execution_records']} == report['stage_attempts']
    summary = {'decision': decision, 'status': report['status'], 'proposal_id': report['proposal_id'],
        'calls': ledger, 'stage_costs': stages, 'scores': scores, 'stop_reason': report['stop_reason'],
        'prior_controls_reused_offline_not_new': controls, 'source_to_event_checks': checks,
        'memories': [{'person_id': pid, 'text': m['text'], 'characters': m['required_characters'], 'actual_tokens': m['required_tokens']} for pid, m in memories.items()],
        'checks': {'raw_calls_and_ledger_replayed': True, 'old_controls_replayed_offline_only': True,
            'source_artifacts_and_gates_rebuilt': True, 'predictions_and_scores_rebuilt': True,
            'rendering_rebuilt': True, 'actual_tokenizer_recounted': count is not None},
        'paired_statistical_units': 1, 'new_holdout': False, 'real_person_fidelity_verified': False,
        'external_model_calls_by_replay': 0,
        'interpretation': 'One consumed six-domain paired development diagnostic. Old D18 full-source controls are reused offline, not contemporary controls, new calls, samples or costs. No real-person, population, causal old/new, fresh-holdout or cross-provider claim.'}
    if profile != 'scale':
        summary['checks']['actual_tokenizer_recounted'] = count is not None and bool(memories)
        summary['checks']['conflict_states_rebuilt'] = True
        summary['actual_memory_token_recounts'] = len(memories) if count is not None else 0
        summary['interpretation'] = 'One consumed D25 development pair. Explicit-conflict preservation repair only; old D25 full-source controls reused offline, not contemporary controls, new samples, calls or costs. D25 remains stopped. No renewed transfer success, fresh holdout, population, real-person, causal old/new or cross-provider claim.'
        if profile == 'conflict_transfer':
            summary['interpretation'] = 'The fixed remaining D25 pair, previously source-read but not extracted/read by D25/D26. Product instruction and rendering unchanged from D26. One consumed paired unit, reported separately from D26; old D25 full-source controls reused offline, not contemporary or new samples/calls/costs. D25 remains stopped. No fresh-holdout, population, real-person, causal old/new or cross-provider claim.'
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True); parser.add_argument('--tokenizer')
    args = parser.parse_args(); model = None
    try:
        count = None
        if args.tokenizer:
            import llama_cpp
            model = llama_cpp.Llama(model_path=args.tokenizer, vocab_only=True, n_gpu_layers=0, verbose=False)
            count = lambda text: len(model.tokenize(text.encode(), add_bos=False, special=False))
        print(json.dumps(replay(args.base, count), ensure_ascii=False))
    finally:
        if model is not None: model.close()
