"""Rebuild D-0024 negative controls, predictions and costs with no service calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


def replay(base, count=None):
    if sys.flags.optimize: raise ValueError('Evidence replay requires assertions enabled')
    base = Path(base).resolve(); frozen = base / 'frozen-source'
    read = lambda n: json.loads((base / n).read_text())
    contract = read('contract.synthetic.json')
    for n, sha in contract['source_hashes'].items(): assert hashlib.sha256((frozen / n).read_bytes()).hexdigest() == sha
    for n, sha in contract['input_hashes'].items(): assert hashlib.sha256((base / contract['input_aliases'][n]).read_bytes()).hexdigest() == sha
    sys.path.insert(0, str(frozen))
    spec = importlib.util.spec_from_file_location('frozen_discrimination', frozen / 'runs/temporal-discrimination-v1/runner.py')
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    from runaway.execution_ledger import collect, summarize, checked
    def forbidden(*args, **kwargs): raise AssertionError('Offline replay must not call a model')
    s.generation.codex_generate = forbidden
    world, original, report = read('world.synthetic.json'), read('source-report.synthetic.json'), read('raw-report.synthetic.json')
    prior = s.prior_controls(world, read('prior-controls.synthetic.json'), original)
    assert prior == report['prior_intact_controls_offline_not_new']
    expected = {k: {'predictions': s.semantic_predictions(world, original, k), 'kind': 'program_event_graph_calibration_not_model_quality'} for k in ('intact', *s.STAGES)}
    for row in expected.values(): row['scores'] = {task: s.fs.score(world, row['predictions'], task) for task in ('current_choice', 'historical_reconstruction', 'joint')}
    assert expected == read('calibration.synthetic.json')
    jobs, mutations = [], []
    for condition in s.STAGES:
        for person in world['people']:
            pid = person['id']; owner = person['twin'] if condition == 'wrong_person_reader' else pid
            text = original['memories'][owner]['text']; before = text
            if condition == 'drop_hard_reader':
                text, removed = re.subn(r'；硬约束若[^。\n]*', '', before); assert removed == 3
                mutations.append({'person_id': pid, 'operation': 'Remove exactly three active hard-constraint clauses; preserve all other bytes.', 'before': before, 'after': text, 'removed_clauses': removed})
            jobs.append({**s.reader_job(condition, pid, text, [c['public'] for c in person['cases']], s.fs.READER, 12), 'stage': condition, 'memory_owner': owner})
    assert jobs == read('jobs.json') and mutations == read('mutations.json')
    records = collect(base); ledger = summarize(records)
    assert ledger == report['calls'] and report['backend_kind'] == 'actual_service'
    assert len(records) == report['external_model_calls'] <= 4
    lookup = {r['request_id']: r for r in records}; labels = {}; budgets = []; predictions = {k: {} for k in s.STAGES}
    for job in jobs:
        key = job['request_id']; text = json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n', 1)[1])['memory']
        stored_budget = next(b for b in report['budgets'] if b['request_id'] == key)
        budget = {'request_id': key, 'characters': len(text), 'tokens': count(text) if count else stored_budget['tokens']}
        assert budget == stored_budget and budget['characters'] <= 768 and budget['tokens'] <= 384; budgets.append(budget)
        if key not in lookup: continue
        labels[key] = job['stage']; assert read('calls/' + key + '.request.json') == job['request']
        if lookup[key]['outcome'] != 'completed' or lookup[key]['usage'] is None: continue
        answer = checked(base / 'calls' / (key + '.response.json'))['answer']
        public = json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n', 1)[1])['queries']
        predictions[job['stage']][job['persona_id']] = s.answers_checked(answer, public)
    assert set(labels) == set(lookup) and predictions == read('answers.synthetic.json')
    scores = {k: {task: s.fs.score(world, v, task) for task in ('current_choice', 'historical_reconstruction', 'joint')} for k, v in predictions.items()}
    assert scores == report['scores']
    concordance = {k: {'correct': sum(predictions[k].get(pid, {}).get(qid) == action for pid, answers in expected[k]['predictions'].items() for qid, action in answers.items()), 'planned': 150} for k in s.STAGES}
    assert concordance == report['manipulation_semantics_concordance']
    success = report['status'] == 'complete' and all(scores[k]['current_choice']['correct'] < 112 and concordance[k]['correct'] == 150 for k in s.STAGES) and scores['wrong_person_reader']['current_choice']['matched_domain_contrasts']['correct'] < 3
    assert success == report['diagnostic_success']
    if report['status'] == 'complete': assert len(records) == 4 and ledger['executions_missing_usage'] == 0 and all(r['outcome'] == 'completed' for r in records)
    stages = {k: summarize([r for r in records if labels[r['request_id']] == k]) for k in s.STAGES}
    assert {k: v['execution_records'] for k, v in stages.items() if v['execution_records']} == report['stage_attempts']
    return {'decision': 'D-0024', 'proposal_id': report['proposal_id'], 'status': report['status'], 'diagnostic_success': success, 'stop_reason': report['stop_reason'],
        'calls': ledger, 'stage_costs': stages, 'scores': scores, 'manipulation_semantics_concordance': concordance, 'budgets': budgets,
        'prior_intact_controls_offline_not_new': prior,
        'checks': {'raw_calls_and_ledger_replayed': True, 'manipulations_rebuilt_byte_exactly': True, 'fixed_semantics_rebuilt': True, 'old_controls_replayed_offline_only': True, 'predictions_scores_and_success_rebuilt': True, 'actual_tokenizer_recounted': count is not None},
        'paired_statistical_units': 1, 'new_holdout': False, 'real_person_fidelity_verified': False, 'external_model_calls_by_replay': 0,
        'interpretation': 'Fixed consumed development pair. Negative-control model reading is measured separately from program calibration. Old intact controls are reused offline, not contemporary controls, independent samples, new calls or costs. No population, real-person, fresh-holdout, causal-old-new or cross-provider claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--base', required=True); parser.add_argument('--tokenizer'); args = parser.parse_args(); model = None
    try:
        counter = None
        if args.tokenizer:
            import llama_cpp
            model = llama_cpp.Llama(model_path=args.tokenizer, vocab_only=True, n_gpu_layers=0, verbose=False)
            counter = lambda text: len(model.tokenize(text.encode(), add_bos=False, special=False))
        print(json.dumps(replay(args.base, counter), ensure_ascii=False))
    finally:
        if model is not None: model.close()
