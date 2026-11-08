"""Trace a flat/factored reading to the same inherited source-ID parent."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('common_factor_trace_replay',HERE/'replay_common_condition.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def trace(data,report,person,case,method,generation):
    if person not in r.p.PROFILES or method not in r.p.METHODS or generation not in(0,1):raise ValueError('Outside frozen parent/layout coordinates')
    cell=next((x for x in report['all_case_transitions']if x['person']==person and x['case']==case),None)
    if cell is None:raise ValueError('Unknown case')
    view=next(v for v in data['prepared_files']['views.public.json']if(v['profile'],v['method'],v['generation'])==(person,method,generation))
    inherited=r.p.read(r.p.MEASURED);parent=next(x for x in inherited['records']if x['slot']==view['parent_slot'])
    graph=json.loads(parent['raw'])
    resolved=r.p.old.factory(view['parent_method']).resolve(graph,r.p.inputs()['sources'][person])
    source=data['prepared_files']['sources.json'][person]['sources'];ids=set(cell['source_ids_for_review'])
    episodes={s['episode_id']for s in source if s['id']in ids}
    row=next(x for x in data['prepared_files']['reference.private.json']if x['person']==person and x['case']==case)
    bank=data['prepared_files']['queries.public.json'][r.p.old.bank(person)]
    reads=[x for x in data['records']if x['kind']=='read'and(x['profile'],x['method'],x['generation'])==(person,method,generation)]
    answers=cell[method]['answers_by_generation'][generation]
    original=parent['artifact']['prompt'];restored=r.p.factor_codec.restore(view['prompt'])
    if restored!=r.p.factor_codec.dense.decode(original):raise ValueError('Inherited public projection differs')
    return dict(person=person,case=case,method=method,generation=generation,reference=cell['gold'],cohort=cell['cohort'],
        complete_related_source_episodes=[s for s in source if s['episode_id']in episodes],
        source_links_are_author_navigation_not_independent_gold=True,
        public_queries=[q for q in bank if q['id']in row['query_ids']],inherited_parent_slot=view['parent_slot'],
        inherited_original_raw_graph=graph,deterministically_resolved_graph=resolved,
        inherited_flat_public_card=original,public_view=view['prompt'],restored_public_projection=restored,
        program_projection_roundtrip_exact=True,public_characters=view['characters'],whole_character_ceiling=view['whole_character_ceiling'],
        original_read_slots=[x['slot']for x in reads],answers_by_read_and_order=[answers[:2],answers[2:]],
        loss_kind=cell[method]['loss_kind'],no_automatic_semantic_cause_claim=True,new_service_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence',type=Path,default=r.DEFAULT)
    parser.add_argument('--person',choices=r.p.PROFILES,required=True);parser.add_argument('--case',required=True)
    parser.add_argument('--method',choices=r.p.METHODS,required=True);parser.add_argument('--generation',type=int,choices=(0,1),required=True)
    a=parser.parse_args();report=r.check(a.evidence)
    print(json.dumps(trace(r.p.read(a.evidence),report,a.person,a.case,a.method,a.generation),ensure_ascii=False,indent=2))
