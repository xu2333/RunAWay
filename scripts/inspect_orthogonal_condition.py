"""Trace a fixed-card answer back to unchanged source and inherited graph; no service."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('orthogonal_trace_replay',HERE/'replay_orthogonal_condition.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def trace(data,report,person,case,method,generation):
    if person not in r.p.PROFILES or method not in r.p.METHODS+r.p.DIAGNOSTICS:
        raise ValueError('Outside fixed people/methods')
    diagnostic=method in r.p.DIAGNOSTICS
    if generation not in((0,)if diagnostic else(0,1))or(diagnostic and person!='otter'):
        raise ValueError('Outside fixed parent coordinates')
    cells=report['constructed_diagnostic_cases']if diagnostic else report['all_case_transitions']
    cell=next((x for x in cells if x['person']==person and x['case']==case),None)
    if cell is None:raise ValueError('Unknown case')
    view=next(v for v in data['prepared_files']['views.public.json']
              if (v['profile'],v['method'],v['generation'])==(person,method,generation))
    if diagnostic:
        inherited=r.p.damage.read_evidence();parent=next(x for x in inherited['records']if x['slot']==10)
        graph=json.loads(parent['raw'])if method==r.p.DIAGNOSTICS[0]else r.p.damage.diagnose(inherited)['damaged_graph']
        resolved=None
    else:
        inherited=r.p.read(r.p.MEASURED);parent=next(x for x in inherited['records']if x['slot']==view['parent_slot'])
        graph=json.loads(parent['raw'])
        resolved=r.p.old.factory(method).resolve(graph,r.p.inputs()['sources'][person])if method==r.p.METHODS[1]else None
    source=data['prepared_files']['sources.json'][person]['sources'];ids=set(cell['source_ids_for_review'])
    episodes={s['episode_id']for s in source if s['id']in ids}
    row=next(x for x in data['prepared_files']['reference.private.json']if x['person']==person and x['case']==case)
    queries=data['prepared_files']['queries.public.json'][r.p.old.bank(person)]
    reads=[x for x in data['records']if x['kind']=='read'and(x['profile'],x['method'],x['generation'])==(person,method,generation)]
    answers=cell[method]['answers_by_generation'][0 if diagnostic else generation]
    return dict(person=person,case=case,method=method,generation=generation,reference=cell['gold'],cohort=cell['cohort'],
        complete_related_source_episodes=[s for s in source if s['episode_id']in episodes],
        source_links_are_author_navigation_not_independent_gold=True,
        public_queries=[q for q in queries if q['id']in row['query_ids']],
        inherited_parent_slot=view['parent_slot'],inherited_original_raw_graph=graph,
        deterministically_resolved_graph=resolved,unchanged_public_card=view['prompt'],
        public_characters=view['characters'],constructed_damage=view['constructed_damage'],
        original_read_slots=[x['slot']for x in reads],answers_by_read_and_order=[answers[:2],answers[2:]],
        loss_kind=cell[method]['loss_kind'],no_automatic_semantic_cause_claim=True,new_service_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence',type=Path,default=r.DEFAULT)
    parser.add_argument('--person',choices=r.p.PROFILES,required=True);parser.add_argument('--case',required=True)
    parser.add_argument('--method',choices=r.p.METHODS+r.p.DIAGNOSTICS,required=True);parser.add_argument('--generation',type=int,choices=(0,1),required=True)
    args=parser.parse_args();report=r.check(args.evidence)
    print(json.dumps(trace(r.p.read(args.evidence),report,args.person,args.case,args.method,args.generation),ensure_ascii=False,indent=2))
