"""Inspect an archived failure without new model calls or automatic cause claims."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('direct768_localization_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


def trace(prepared, execution, person, case, method, generation):
    p.verify(prepared)
    if person not in p.PROFILES or method not in p.METHODS or type(generation) is not int or generation not in (0, 1):
        raise ValueError('Outside frozen coordinates')
    data = p.inputs()
    row = next((r for r in data['rows'] if (r['person'], r['case']) == (person, case)), None)
    if row is None: raise ValueError('Unknown case')
    navigation = next(r for r in data['author_evidence'] if (r['person'], r['case']) == (person, case))
    slots = [s for s in p.slots() if (s['profile'], s['method'], s['generation']) == (person, method, generation)]
    extraction = next(s for s in slots if s['kind'] == 'extract')
    folder = Path(execution) / ('attempt-%02d' % extraction['slot'])
    raw = p.read(folder / 'answer.json') if (folder / 'answer.json').exists() else None
    captured = p.read(folder / 'raw-response.json') if (folder / 'raw-response.json').exists() else {}
    artifact = p.read(folder / 'artifact.json') if (folder / 'artifact.json').exists() else None
    resolved, ledger, failure = None, None, None
    if raw is not None:
        try:
            resolved = p.candidate.base.resolve(raw, data['sources'][person])
            # Keep the entire inherited audit graph as well as any compiled rows;
            # a failed bind is evidence, not an excuse to repair its contents.
            diagnostic = p.candidate.base.bind(raw, data['sources'][person], p.candidate.INTERMEDIATE_CEILING)
            ledger = diagnostic.get('source-order.private.json', {}).get('original_ledger')
            files = p.bind(extraction, raw)
        except (ValueError, KeyError, TypeError) as exc:
            failure = dict(type=type(exc).__name__, detail=str(exc))
        if artifact is not None and (failure is not None or files['prompt.md'] != artifact['prompt']):
            raise ValueError('Archived valid public card does not reconstruct')
    reads = []
    for s in slots:
        if s['kind'] != 'read': continue
        f = Path(execution) / ('attempt-%02d' % s['slot'])
        a = p.read(f / 'answer.json') if (f / 'answer.json').exists() else {}
        result = p.read(f / 'result.json') if (f / 'result.json').exists() else {}
        reads.append(dict(slot=s['slot'], read_repeat=s['read_repeat'],
            state=result.get('state', 'not_called'), raw_answers=[a.get(q) for q in row['query_ids']],
            answers=[a.get(q) if result.get('state') == 'completed' else None for q in row['query_ids']]))
    return dict(person=person, case=case, method=method, generation=generation,
        reference=row['gold'], cohort=row['cohort'],
        complete_source_episodes=[s for s in data['sources'][person]['sources']
                                 if s['id'] in navigation['complete_episode_source_ids']],
        public_queries=[q for q in data['queries'][p.bank(person)] if q['id'] in row['query_ids']],
        raw_source_id_graph=raw, original_raw_response=captured.get('raw'),
        resolved_graph=resolved, compiled_active_rows=ledger,
        row_diagnostic_ceiling_not_reader_memory=p.candidate.INTERMEDIATE_CEILING,
        public_card=artifact['prompt'] if artifact is not None else None,
        binding_failure=failure, reads=reads, whole_character_ceiling=768,
        author_navigation_is_not_semantic_acceptance=True,
        omission_or_scope_cause_requires_review=True, new_model_calls=0)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--prepared', type=Path, required=True)
    cli.add_argument('--execution', type=Path, required=True)
    cli.add_argument('--person', choices=p.PROFILES, required=True)
    cli.add_argument('--case', required=True)
    cli.add_argument('--method', choices=p.METHODS, required=True)
    cli.add_argument('--generation', type=int, choices=(0, 1), required=True)
    a = cli.parse_args()
    print(json.dumps(trace(a.prepared, a.execution, a.person, a.case, a.method, a.generation), ensure_ascii=False, indent=2))
