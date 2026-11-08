"""Print one source-to-card-to-answer trace from checked, closed fictional evidence."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('binding_trace_replay', HERE / 'replay_fresh_alias.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def trace(data, report, person, case, method, budget, generation):
    """Select original values only; the caller supplies the already checked replay."""
    if person not in r.p.PROFILES or method not in r.p.METHODS or budget not in r.p.BUDGETS or generation not in (0, 1):
        raise ValueError('Outside the frozen source/parent coordinates')
    cell = next((x for x in report['all_case_transitions']
                 if x['person'] == person and x['case'] == case and x['budget'] == budget), None)
    if cell is None:
        raise ValueError('Unknown original case')
    source = data['prepared_files']['sources.json'][person]['sources']
    ids = set(cell['source_ids_for_review'])
    # Include the whole source episode, including assistant/tool/context turns.
    # Author-selected evidence links are navigation aids, not accepted semantics.
    episodes = {s['episode_id'] for s in source if s['id'] in ids}
    parents = [x for x in data['records'] if x['kind'] == 'extract' and x['profile'] == person
               and x['method'] == method and x['budget'] == budget and x['generation'] == generation]
    if len(parents) > 1:
        raise ValueError('Repeated parent in checked evidence')
    parent = parents[0] if parents else None
    raw_graph = None
    if parent and parent['raw_present']:
        try:
            raw_graph = r.e.parse_answer(parent['raw'])
        except (ValueError, TypeError):
            # A recorded decode failure has raw text but no decoded graph.
            pass
    reads = [x for x in data['records'] if x['kind'] == 'read' and x['profile'] == person
             and x['method'] == method and x['budget'] == budget and x['generation'] == generation]
    row = next(x for x in data['prepared_files']['reference.private.json']
               if x['person'] == person and x['case'] == case)
    queries = data['prepared_files']['queries.public.json'][r.p.bank(person)]
    return {
        'person': person, 'case': case, 'method': method, 'budget': budget, 'generation': generation,
        'reference': cell['gold'], 'cohort': cell['cohort'],
        'source_links_are_author_navigation_not_independent_gold': True,
        'source_ids_for_review': cell['source_ids_for_review'],
        'complete_related_source_episodes': [s for s in source if s['episode_id'] in episodes],
        'public_queries': [q for q in queries if q['id'] in row['query_ids']],
        'parent_slot': parent['slot'] if parent else None,
        'parent_state': parent['state'] if parent else 'not_attempted',
        'original_raw_response': parent['raw'] if parent and parent['raw_present'] else None,
        'original_raw_graph': raw_graph,
        'original_public_card': parent['artifact']['prompt'] if parent and parent['artifact'] else None,
        'original_read_slots': [x['slot'] for x in reads],
        'answers_by_read_and_order': [cell[method]['answers_by_generation'][generation][:2],
                                     cell[method]['answers_by_generation'][generation][2:]],
        'cell_loss_kind': cell[method]['loss_kind'],
        'no_automatic_semantic_cause_claim': True, 'new_service_calls': 0,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=r.DEFAULT)
    parser.add_argument('--person', choices=r.p.PROFILES, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--method', choices=r.p.METHODS, required=True)
    parser.add_argument('--budget', type=int, choices=r.p.BUDGETS, required=True)
    parser.add_argument('--generation', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    report = r.check(args.evidence)
    print(json.dumps(trace(r.p.read(args.evidence), report, args.person, args.case,
                           args.method, args.budget, args.generation), ensure_ascii=False, indent=2))
