"""Inspect complete source,graph,card and answers at a frozen method/generation/case;zero services."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('domain_revision_trace',HERE/'replay_domain_revision.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)


def trace(data,report,case,method,generation):
    if method not in r.p.METHODS or type(generation)is not int or generation not in(0,1):raise ValueError('Foreign method/generation')
    cell=next((c for c in report['all_case_transitions']if c['case']==case),None)
    if cell is None:raise ValueError('Foreign case')
    rows=data['prepared_files']['reference.private.json'];row=next(x for x in rows if x['case']==case)
    source=data['prepared_files']['sources.json']['rivet'];episode='project'+case.split('_',1)[0]
    parent=next((x for x in data['records']if x['kind']=='extract'and x['method']==method and x['generation']==generation),None)
    raw,resolved,ledger,projection,error=None,None,None,None,None
    if parent and parent['raw_present']:
        try:
            raw=r.e.parse_answer(parent['raw']);encoder=r.p.encoder(method)
            resolved=encoder.resolve(raw,source)if method=='condition_revision'else encoder.base.resolve(raw,source)
            diagnostic=encoder.bind(raw,source,16000)
            ledger=diagnostic.get('condition-revision.private.json',{}).get('ledger')
            if ledger is None:ledger=diagnostic.get('source-order.private.json',{}).get('original_ledger')
            projection=r.p.old.candidate.dense.parse(r.p.old.candidate.restore(diagnostic['prompt.md']))
        except(ValueError,KeyError,TypeError)as exc:error=dict(error_type=type(exc).__name__,detail=str(exc))
    full=[]
    for rec in data['records']:
        if rec['kind']=='full'and rec['state']=='completed':
            answer=r.e.parse_answer(rec['raw']);full.append(dict(slot=rec['slot'],answers=[answer[q]for q in row['query_ids']]))
    return dict(person='rivet',case=case,method=method,generation=generation,reference=cell['gold'],
        complete_related_source_episodes=[s for s in source['sources']if s['episode_id']==episode],
        public_queries=[q for q in data['prepared_files']['queries.public.json']['rivet']if q['id']in row['query_ids']],
        source_derived_domain_review=[e for e in data['prepared_files']['domain-evidence.private.json']if e['case']==case],
        full_source_answers=full,original_parent_slot=parent['slot']if parent else None,
        original_raw_graph=raw,resolved_graph=resolved,diagnostic_active_ledger=ledger,diagnostic_projection=projection,
        diagnostic_ceiling_not_reader_memory=16000,graph_diagnostic_error=error,
        original_public_card=parent['artifact']['prompt']if parent and parent['artifact']else None,
        planned_answers_this_generation=cell[method]['answers'][4*generation:4*generation+4],
        planned_answers_all_generations=cell[method]['answers'],loss_kind=cell[method]['loss_kind'],
        source_links_are_author_navigation_not_independent_semantic_gold=True,new_service_calls=0)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('case',nargs='?');a.add_argument('--domain-layout-slot',type=int);a.add_argument('--method',choices=r.p.METHODS,default='condition_revision');a.add_argument('--generation',type=int,choices=(0,1),default=0);a.add_argument('--archive',type=Path,default=r.DEFAULT);args=a.parse_args()
    report=r.check(args.archive)
    data=r.p.read(args.archive)
    if args.domain_layout_slot is None and args.case is None:a.error('case or --domain-layout-slot required')
    value=r.domain_layout_probe(data,args.domain_layout_slot)if args.domain_layout_slot is not None else trace(data,report,args.case,args.method,args.generation)
    print(json.dumps(value,ensure_ascii=False,indent=2))
