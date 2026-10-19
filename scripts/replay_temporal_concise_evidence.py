"""Offline replay of D-0028. Frozen codec/proofs are never model-quality claims."""
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
    spec = importlib.util.spec_from_file_location('frozen_concise_runner', frozen / 'runs/temporal-concise-v1/runner.py')
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    from runaway.execution_ledger import collect, summarize, checked
    def forbidden(*args, **kwargs): raise AssertionError('Offline replay must never invoke a model')
    s.generation.codex_generate = forbidden
    report, world, artifacts = read('raw-report.synthetic.json'), read('world.synthetic.json'), read('artifacts.synthetic.json')
    assert report['backend_kind'] == 'actual_service' and report['proposal_id'] == contract['id']
    assert report['status'] in ('complete', 'stopped') and (report['stop_reason'] is None) == (report['status'] == 'complete')
    assert report['paired_statistical_units'] == 2 and report['new_holdout'] is False and report['real_person_fidelity_verified'] is False
    assert contract['calls_max'] == 4 and contract['stage_caps'] == {'actual_memory_reader': 4}
    assert contract['token_budget'] == 288 and contract['character_budget'] == 768
    old = s.baseline(world, artifacts, read('controls.synthetic.json')); assert old == report['separate_old_reference_batches']
    frozen_deliveries = read('deliveries.synthetic.json'); memories = {}; proofs = {}; jobs = []
    for person in world['people']:
        pid = person['id']; proofs[pid] = s.codec.prove(artifacts[pid])
        if count:
            delivery = s.codec.encode(artifacts[pid], count=count, budget_tokens=288)
        else:
            delivery = s.codec.encode(artifacts[pid]); delivery['actual_tokens'] = frozen_deliveries['memories'][pid]['actual_tokens']; delivery['budget_tokens'] = 288
        assert delivery['status'] == 'experimental_unvalidated' and type(delivery['actual_tokens']) is int and 0 < delivery['actual_tokens'] <= 288 and delivery['characters'] <= 768
        memories[pid] = delivery
        jobs.append(s.reader_job('concise_current_policy', pid, delivery['text'], [c['public'] for c in person['cases']], s.fs.READER, 12))
    assert memories == report['memories'] == frozen_deliveries['memories'] and proofs == frozen_deliveries['proofs'] and jobs == read('jobs.json')
    records = collect(base); ledger = summarize(records); lookup = {r['request_id']: r for r in records}; visited = set(); predictions = {}; parse_failure = False
    assert ledger == report['calls'] and report['external_model_calls'] == len(records) <= 4
    for job in jobs:
        key = job['request_id']
        if key not in lookup: break
        visited.add(key); assert read('calls/' + key + '.request.json') == job['request']
        record = lookup[key]
        if record['outcome'] != 'completed' or record['usage'] is None:
            parse_failure = True; break
        try:
            raw = checked(base / 'calls' / (key + '.response.json'))['answer']
            public = json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n', 1)[1])['queries']
            predictions[job['persona_id']] = s.answers_checked(raw, public)
        except ValueError:
            parse_failure = True; break
    assert visited == set(lookup) and predictions == read('answers.synthetic.json')
    scores = {task: s.fs.score(world, predictions, task) for task in ('current_choice', 'historical_reconstruction', 'joint')}; assert scores == report['scores']
    current = scores['current_choice']; success = report['status'] == 'complete' and current['correct'] == 224 and current['matched_domain_contrasts']['correct'] == 6 and current['hard_constraints']['observed_violations'] == 0
    assert success == report['strict_current_target_passed']
    if report['status'] == 'complete': assert len(records) == 4 and ledger['executions_missing_usage'] == 0 and not parse_failure
    assert report['stage_attempts'] == {'actual_memory_reader': len(records)}
    return {'decision': 'D-0028', 'status': report['status'], 'proposal_id': report['proposal_id'], 'strict_current_target_passed': success, 'stop_reason': report['stop_reason'],
        'calls': ledger, 'stage_costs': {'actual_memory_reader': ledger}, 'scores': scores, 'memories': memories, 'separate_old_reference_batches': old,
        'codec_proofs_not_model_quality': proofs, 'actual_memory_token_recounts': len(memories) if count else 0,
        'checks': {'raw_calls_and_ledger_replayed': True, 'old_reference_batches_rebuilt_separately': True, 'codec_roundtrips_and_partial_states_rebuilt': True, 'whole_prompts_requests_and_scores_rebuilt': True, 'actual_tokenizer_recounted': count is not None},
        'paired_statistical_units': 2, 'new_holdout': False, 'real_person_fidelity_verified': False, 'external_model_calls_by_replay': 0,
        'interpretation': 'Two consumed synthetic pairs; a new shorter current-policy encoding readout only. Old reference batches reused offline, not contemporary/new samples/costs. Grammar and scope are within measured memory; no model decoder supplied. Not full-trajectory losslessness, population, real-person, cross-provider or causal evidence.'}


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
