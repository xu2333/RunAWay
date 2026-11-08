"""Inspect original source/graph/card/answers;no new inference or repair."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location('direct768_trace_replay', HERE / 'replay_fresh_direct768.py')
r = importlib.util.module_from_spec(s); s.loader.exec_module(r)


def trace(data, report, person, case, method, budget, generation):
    p = r.p
    if (person not in p.PROFILES or method not in p.METHODS or type(budget) is not int or
            budget not in p.BUDGETS or type(generation) is not int or generation not in (0, 1)):
        raise ValueError('Outside frozen coordinates')
    cell = next((x for x in report['all_case_transitions'] if
        (x['person'], x['case'], x['budget']) == (person, case, budget)), None)
    if cell is None: raise ValueError('Unknown case')
    parents = [x for x in data['records'] if x['kind'] == 'extract' and
        (x['profile'], x['method'], x['budget'], x['generation']) == (person, method, budget, generation)]
    if len(parents) > 1: raise ValueError('Repeated parent')
    parent = parents[0] if parents else None
    graph, resolved, ledger, diagnostic = None, None, None, None
    if parent and parent['raw_present']:
        try:
            graph = r.e.parse_answer(parent['raw'])
            own = data['prepared_files']['sources.json'][person]
            resolved = p.candidate.base.resolve(graph, own)
            full = p.candidate.base.bind(graph, own, p.candidate.INTERMEDIATE_CEILING)
            ledger = full.get('source-order.private.json', {}).get('original_ledger')
        except (ValueError, KeyError, TypeError) as exc:
            diagnostic = dict(error_type=type(exc).__name__, detail=str(exc))
    source = data['prepared_files']['sources.json'][person]['sources']
    episodes = {s['episode_id'] for s in source if s['id'] in cell['source_ids_for_review']}
    row = next(x for x in data['prepared_files']['reference.private.json'] if (x['person'], x['case']) == (person, case))
    reads = [x for x in data['records'] if x['kind'] == 'read' and
        (x['profile'], x['method'], x['budget'], x['generation']) == (person, method, budget, generation)]
    card = parent['artifact']['prompt'] if parent and parent['artifact'] else None
    return dict(person=person, case=case, method=method, budget=budget, generation=generation,
        reference=cell['gold'], cohort=cell['cohort'], family=cell['family'],
        complete_related_source_episodes=[s for s in source if s['episode_id'] in episodes],
        source_links_are_author_navigation_not_independent_gold=True,
        public_queries=[q for q in data['prepared_files']['queries.public.json'][p.bank(person)] if q['id'] in row['query_ids']],
        parent_slot=parent['slot'] if parent else None,
        parent_state=parent['state'] if parent else 'not_attempted',
        original_raw_response=parent['raw'] if parent and parent['raw_present'] else None,
        original_raw_graph=graph, deterministically_resolved_graph=resolved, compiled_active_rows=ledger,
        graph_diagnostic=diagnostic, private_diagnostic_ceiling_not_reader_memory=p.candidate.INTERMEDIATE_CEILING,
        original_public_card=card,
        expanded_public_projection=p.candidate.dense.parse(p.candidate.restore(card)) if card is not None else None,
        parent_product_invalid=bool(parent['execution_record'].get('product_invalid', False)) if parent else False,
        original_read_slots=[x['slot'] for x in reads],
        answers_by_read_and_order=[cell[method]['answers_by_generation'][generation][:2],
                                   cell[method]['answers_by_generation'][generation][2:]],
        cell_loss_kind=cell[method]['loss_kind'], no_automatic_semantic_cause_claim=True,
        new_service_calls=0)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--evidence', type=Path, default=r.DEFAULT)
    cli.add_argument('--person', choices=r.p.PROFILES, required=True)
    cli.add_argument('--case', required=True)
    cli.add_argument('--method', choices=r.p.METHODS, required=True)
    cli.add_argument('--budget', type=int, choices=r.p.BUDGETS, required=True)
    cli.add_argument('--generation', type=int, choices=(0, 1), required=True)
    a = cli.parse_args(); report = r.check(a.evidence)
    print(json.dumps(trace(r.p.read(a.evidence), report, a.person, a.case, a.method, a.budget, a.generation), ensure_ascii=False, indent=2))
