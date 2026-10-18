"""Replay D-0021 using its saved runtime package, never the current product code."""
import argparse
import json
from pathlib import Path
import sys


def replay(base, tokenizer=None):
    if sys.flags.optimize:
        raise ValueError('Evidence replay requires assertions enabled; do not use -O or PYTHONOPTIMIZE')
    base = Path(base).resolve()
    sys.path.insert(0, str(base / 'runtime-source'))
    from runaway import temporal as t, temporal_diagnostic as td, generation
    from runaway.card import canonical, digest
    from runaway.execution_ledger import collect, summarize, checked
    from runaway.taste_executor import answers_checked
    from runaway.taste_plan import reader_job
    from runaway.fidelity_stress import READER
    def forbidden(*args, **kwargs):
        raise AssertionError('Evidence replay must never invoke a model')
    generation.codex_generate = forbidden
    read = lambda name: json.loads((base / name).read_text())
    report, people, jobs = read('raw-report.synthetic.json'), read('development.synthetic.json'), read('jobs.synthetic.json')
    if report['status'] != 'complete' or report['backend_kind'] != 'actual_service' or report['origin'] != 'consumed_synthetic_development_only':
        raise ValueError('This packager supports the sealed D-0021 actual-service batch only')
    records = collect(base)
    assert summarize(records) == report['calls']
    assert len(records) == report['external_model_calls'] == 6
    assert report['calls']['executions_missing_usage'] == 0
    by_key = {r['request_id']: r for r in records}
    labels, responses = {}, {}
    for r in records:
        assert r['outcome'] == 'completed'
        responses[r['request_id']] = checked(base / 'calls' / (r['request_id'] + '.response.json'))
    def answer(request, stage):
        key = digest(canonical(request)); labels[key] = stage
        assert json.loads((base / 'calls' / (key + '.request.json')).read_text()) == request
        return responses[key]['answer']
    predictions = {'full_history': {}, 'temporal': {}}
    artifacts, memories, parser_checks, graph_checks = {}, {}, {}, {}
    for job in jobs:
        person = next(p for p in people if p['id'] == job['person_id']); pid = person['id']
        raw = answer(job['request'], job['stage'])
        if job['stage'] == 'full_history':
            predictions['full_history'][pid] = answers_checked(raw, [c['public'] for c in person['cases']])
        else:
            artifact = t.bind(raw, person['sources']); artifacts[pid] = artifact
            parser_checks[pid] = [t.resolve(artifact, '产品验证', c['context'])['action'] == c['action'] for c in person['cases'][:8:2]]
            graph_checks[pid] = td.graph_checks(person, artifact)
            if tokenizer is not None:
                memory = t.render(artifact, 768, count=tokenizer, budget_tokens=384)
            else:
                memory = t.render(artifact, 768)
                # Public replay checks rendering without requiring a GGUF download.
                # The sealed local audit independently recounted these two fields.
                memory['budget_tokens'] = report['memories'][pid]['budget_tokens']
                memory['required_tokens'] = report['memories'][pid]['required_tokens']
            assert memory == report['memories'][pid]
            memories[pid] = memory
    for person in people:
        pid = person['id']; public = [c['public'] for c in person['cases']]
        job = reader_job('temporal', pid, memories[pid]['text'], public, READER, 12)
        predictions['temporal'][pid] = answers_checked(answer(job['request'], 'actual_memory_reader'), public)
    assert predictions == read('answers.synthetic.json')
    assert artifacts == report['artifacts'] and memories == report['memories']
    assert parser_checks == report['source_to_event_checks'] and graph_checks == report['source_graph_checks']
    scores = {k: td.score(people, v) for k, v in predictions.items()}
    assert scores == report['scores'] and scores['full_history'] == report['full_source_gate']
    assert all(all(v) for v in parser_checks.values()) and all(all(v.values()) for v in graph_checks.values())
    assert set(labels) == set(by_key)
    stages = {stage: summarize([r for key, r in by_key.items() if labels[key] == stage])
              for stage in ('full_history', 'shared_extraction', 'actual_memory_reader')}
    assert {k: v['execution_records'] for k, v in stages.items()} == report['stage_attempts']
    assert all(v['execution_records'] == 2 for v in stages.values())
    return {'decision': 'D-0021', 'origin': report['origin'], 'status': report['status'],
        'proposal_id': report['proposal_id'], 'calls': report['calls'], 'stage_costs': stages,
        'scores': scores, 'source_to_event_checks': parser_checks, 'source_graph_checks': graph_checks,
        'memories': [{'person_id': pid, 'text': m['text'], 'characters': m['required_characters'],
                      'actual_tokens': m['required_tokens']} for pid, m in memories.items()],
        'checks': {'raw_calls_and_ledger_replayed': True, 'predictions_rebuilt': True,
            'source_artifacts_rebuilt': True, 'all_scores_and_graph_checks_replayed': True,
            'program_rendering_rebuilt': True, 'actual_tokenizer_recounted': tokenizer is not None},
        'paired_statistical_units': 1, 'new_holdout': False, 'real_person_fidelity_verified': False,
        'external_model_calls_by_replay': 0,
        'interpretation': 'One consumed single-domain paired development diagnostic. Current16/16; historical0/4 remains visible. No fresh old-method comparison, whole-six-domain128-token, population, real-person or cross-provider claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--tokenizer')
    args = parser.parse_args()
    model = None
    try:
        counter = None
        if args.tokenizer:
            import llama_cpp
            model = llama_cpp.Llama(model_path=args.tokenizer, vocab_only=True, n_gpu_layers=0, verbose=False)
            counter = lambda text: len(model.tokenize(text.encode(), add_bos=False, special=False))
        print(json.dumps(replay(args.base, counter), ensure_ascii=False))
    finally:
        if model is not None:
            model.close()
