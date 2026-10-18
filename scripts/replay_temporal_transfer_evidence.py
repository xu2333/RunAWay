"""Replay complete or stopped D-0025 from frozen inputs; never invoke a model."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def replay(base, count=None):
    if sys.flags.optimize: raise ValueError('Evidence replay requires assertions enabled')
    base = Path(base).resolve(); frozen = base / 'frozen-source'; read = lambda n: json.loads((base / n).read_text())
    contract = read('contract.synthetic.json')
    for n, sha in contract['source_hashes'].items(): assert hashlib.sha256((frozen / n).read_bytes()).hexdigest() == sha
    for n, sha in contract['input_hashes'].items(): assert hashlib.sha256((base / contract['input_aliases'][n]).read_bytes()).hexdigest() == sha
    sys.path.insert(0, str(frozen))
    spec = importlib.util.spec_from_file_location('frozen_transfer', frozen / 'runs/temporal-transfer-v1/runner.py')
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    from runaway.execution_ledger import collect, summarize, checked
    def forbidden(*args, **kwargs): raise AssertionError('Offline replay must never call a model')
    s.generation.codex_generate = forbidden
    report, world, jobs = read('raw-report.synthetic.json'), read('world.synthetic.json'), read('jobs.json')
    engine = s.world_engine(read('domains.json')); people = {p['id']: p for p in world['people']}
    assert report['backend_kind'] == 'actual_service' and report['paired_statistical_units'] == 2
    records = collect(base); ledger = summarize(records); lookup = {r['request_id']: r for r in records}
    assert ledger == report['calls'] and len(records) == report['external_model_calls'] <= 12
    labels = {}; visited = set()
    class SavedStop(Exception): pass
    def answer(request, stage):
        key = s.digest(s.canonical(request)); assert key in lookup
        assert read('calls/' + key + '.request.json') == request
        labels[key] = stage; visited.add(key); record = lookup[key]
        if record['outcome'] != 'completed' or record['usage'] is None: raise SavedStop('Saved invocation did not return a usable known-usage response')
        return checked(base / 'calls' / (key + '.response.json'))['answer']
    predictions = {'full_history': {}, 'temporal': {}}; artifacts = {}; memories = {}; checks = {}; full_gate = None; error = None
    try:
        for job in jobs:
            if job['stage'] != 'full_history': continue
            pid = job['person_id']; person = people[pid]
            expected = s.reader_job('transfer_full', pid, person['history'], [c['public'] for c in person['cases']], engine.READER, 12)['request']
            assert expected == job['request']
            predictions['full_history'][pid] = s.answers_checked(answer(expected, 'full_history'), [c['public'] for c in person['cases']])
        full_gate = {task: engine.score(world, predictions['full_history'], task) for task in ('current_choice', 'historical_reconstruction', 'joint')}
        if any(v['correct'] != v['planned'] for v in full_gate.values()): raise SavedStop('full_source_gate_failed')
        for job in jobs:
            if job['stage'] != 'shared_extraction': continue
            pid = job['person_id']; person = people[pid]
            assert job['sources']['sources'][0]['text'] == person['history']
            assert job['request'] == {'prompt': s.t.make_request(job['sources']), 'schema': s.t.SCHEMA, 'model': 'gpt-6-luna', 'system': s.SYSTEM}
            artifact = s.t.bind(answer(job['request'], 'shared_extraction'), job['sources']); artifacts[pid] = artifact
            check = s.source_checks(person, artifact, engine); checks[pid] = check
            if not check['event_span_coverage'] or not all(check['retraction_edges']) or not all(check['current_contexts']): raise SavedStop('source_to_event_gate_failed')
            if count:
                memory = s.t.render(artifact, 768, count=count, budget_tokens=384)
            else:
                memory = s.t.render(artifact, 768); stored = report['memories'][pid]
                memory['budget_tokens'] = 384; memory['required_tokens'] = stored['required_tokens']
                assert type(memory['required_tokens']) is int
                if memory['required_tokens'] > 384: memory['status'] = 'budget_blocked'; memory['text'] = None
            memories[pid] = memory
            if memory['status'] != 'candidate_unvalidated': raise SavedStop('whole_prompt_budget_failed')
        for person in world['people']:
            pid = person['id']; public = [c['public'] for c in person['cases']]
            request = s.reader_job('transfer_memory', pid, memories[pid]['text'], public, engine.READER, 12)['request']
            predictions['temporal'][pid] = s.answers_checked(answer(request, 'actual_memory_reader'), public)
    except (SavedStop, ValueError) as exc:
        error = {'type': type(exc).__name__, 'message': str(exc)}
    assert visited == set(lookup), 'Unexplained calls or calls after a reproduced stop'
    assert predictions == read('answers.synthetic.json') and artifacts == report['artifacts'] and memories == report['memories'] and checks == report['source_to_event_checks']
    assert full_gate == report['full_source_gate']
    scores = {condition: {task: engine.score(world, v, task) for task in ('current_choice', 'historical_reconstruction', 'joint')} for condition, v in predictions.items()}
    assert scores == report['scores']
    current = scores['temporal']['current_choice']; success = error is None and current['correct'] == 224 and current['matched_domain_contrasts']['correct'] == 6 and current['hard_constraints']['observed_violations'] == 0
    assert success == report['strict_current_target_passed']
    assert (report['status'] == 'complete') == (error is None)
    if report['status'] == 'complete': assert len(records) == 12 and ledger['executions_missing_usage'] == 0
    stages = {k: summarize([r for r in records if labels[r['request_id']] == k]) for k in s.STAGES}
    assert {k: v['execution_records'] for k, v in stages.items() if v['execution_records']} == report['stage_attempts']
    return {'decision': 'D-0025', 'proposal_id': report['proposal_id'], 'status': report['status'], 'strict_current_target_passed': success, 'stop_reason': report['stop_reason'], 'reproduced_stop': error,
        'calls': ledger, 'stage_costs': stages, 'scores': scores, 'full_source_gate': full_gate, 'source_to_event_checks': checks,
        'memories': [{'person_id': pid, 'text': m['text'], 'characters': m['required_characters'], 'actual_tokens': m['required_tokens'], 'status': m['status']} for pid, m in memories.items()],
        'checks': {'raw_calls_and_ledger_replayed': True, 'requests_and_new_domain_protocol_rebuilt': True, 'predictions_scores_and_target_rebuilt': True, 'source_artifacts_and_gates_rebuilt': True, 'program_rendering_rebuilt': True, 'actual_tokenizer_recounted': count is not None, 'no_calls_after_reproduced_stop': True},
        'paired_statistical_units': 2, 'new_to_experiment_service': True, 'finite_event_grammar_unchanged': True, 'training_independence_verified': False, 'real_person_fidelity_verified': False, 'external_model_calls_by_replay': 0,
        'interpretation': 'Four new experiment people in two paired clusters, six new lexical domain labels within the unchanged finite event grammar. New same-batch full-source controls; no reuse or double-count of prior evidence. Not naturalistic, training-independent, population, real-person or cross-provider evidence.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--base', required=True); parser.add_argument('--tokenizer'); args = parser.parse_args(); model = None
    try:
        count = None
        if args.tokenizer:
            import llama_cpp
            model = llama_cpp.Llama(model_path=args.tokenizer, vocab_only=True, n_gpu_layers=0, verbose=False)
            count = lambda text: len(model.tokenize(text.encode(), add_bos=False, special=False))
        print(json.dumps(replay(args.base, count), ensure_ascii=False))
    finally:
        if model is not None: model.close()
