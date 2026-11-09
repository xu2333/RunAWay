"""Trace original source, raw/resolved graph, public card and four answers;zero calls."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pressure_trace_replay', HERE / 'replay_guard_pressure.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


def trace(data, report, person, case, method):
    p = r.p
    if person not in p.PROFILES or method not in p.METHODS: raise ValueError('Outside frozen coordinates')
    cell = next((x for x in report['all_case_transitions'] if (x['person'], x['case']) == (person, case)), None)
    if cell is None: raise ValueError('Foreign case')
    parent = next((x for x in data['records'] if x['kind'] == 'extract' and
                   x['profile'] == person and x['method'] == method), None)
    raw, resolved, ledger, diagnostic = None, None, None, None
    if parent and parent['raw_present']:
        try:
            raw = r.e.parse_answer(parent['raw'])
            sources = data['prepared_files']['sources.json'][person]
            resolved = p.candidate.base.resolve(raw, sources)
            full = p.candidate.base.bind(raw, sources, p.candidate.INTERMEDIATE_CEILING)
            ledger = full.get('source-order.private.json', {}).get('original_ledger')
        except (ValueError, KeyError, TypeError) as exc:
            diagnostic = dict(error_type=type(exc).__name__, detail=str(exc))
    row = next(x for x in data['prepared_files']['reference.private.json'] if (x['person'], x['case']) == (person, case))
    source = data['prepared_files']['sources.json'][person]['sources']
    card = parent['artifact']['prompt'] if parent and parent['artifact'] else None
    reads = [x for x in data['records'] if x['kind'] == 'read' and x['profile'] == person and x['method'] == method]
    return dict(person=person, case=case, method=method, budget=p.METHOD_BUDGET[method], reference=cell['gold'],
        cohort=cell['cohort'], family=cell['family'],
        complete_related_source_episodes=[s for s in source if s['id'] in cell['source_ids_for_review']],
        source_links_are_author_navigation_not_independent_gold=True,
        public_queries=[q for q in data['prepared_files']['queries.public.json'][person] if q['id'] in row['query_ids']],
        parent_slot=parent['slot'] if parent else None, parent_state=parent['state'] if parent else 'not_attempted',
        original_raw_response=parent['raw'] if parent and parent['raw_present'] else None,
        original_raw_graph=raw, deterministically_resolved_graph=resolved, compiled_active_rows=ledger,
        private_diagnostic_ceiling_not_reader_memory=p.candidate.INTERMEDIATE_CEILING, graph_diagnostic=diagnostic,
        original_public_card=card, expanded_public_projection=p.candidate.dense.parse(p.candidate.restore(card)) if card else None,
        parent_product_invalid=bool(parent['execution_record'].get('product_invalid')) if parent else False,
        original_read_slots=[x['slot'] for x in reads],
        answers_by_read_and_order=[cell[method]['answers'][:2], cell[method]['answers'][2:]],
        cell_loss_kind=cell[method]['loss_kind'], no_automatic_semantic_cause_claim=True, new_service_calls=0)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--evidence', type=Path, default=r.DEFAULT)
    cli.add_argument('--person', required=True, choices=r.p.PROFILES)
    cli.add_argument('--case', required=True)
    cli.add_argument('--method', required=True, choices=r.p.METHODS)
    a = cli.parse_args(); report = r.check(a.evidence)
    print(json.dumps(trace(r.p.read(a.evidence), report, a.person, a.case, a.method), ensure_ascii=False, indent=2))
