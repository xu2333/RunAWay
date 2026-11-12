"""Trace one fixed-view case to complete fictional episodes,public fields and observed answers;no services."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('template_trace_replay',HERE/'replay_guard_template.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)


def trace(data,report,case):
    cell=next((c for c in report['all_case_transitions']if c['case']==case),None)
    if cell is None:raise ValueError('Unknown case')
    prefix=case.split('_',1)[0]
    episode='project'+prefix
    queries=data['prepared_files']['queries.public.json']['task']
    return dict(case=cell,complete_related_source_episodes=[x for x in data['prepared_files']['sources.json']['quince']['sources']if x['episode_id']==episode],
        public_queries=[x for x in queries if x['id']in next(c['query_ids']for c in r.p.inputs()['rows']if c['case']==case)],
        full_source_control=[dict(slot=x['slot'],answers={q:r.e.parse_answer(x['raw']).get(q)for q in next(c['query_ids']for c in r.p.inputs()['rows']if c['case']==case)})for x in data['records']if x['kind']=='full'and x['state']=='completed'],
        unchanged_public_views=r.p.inputs()['views'],ordered_public_fields=r.p.up.template_restore(r.p.inputs()['views']['template768']),
        measured_new_generation=False,new_service_calls=0)


def domain_audit(data):
    """Literal source-to-public-field audit;not a model or semantic verdict."""
    import re
    sources=data['prepared_files']['sources.json']['quince']['sources']
    views=r.p.inputs()['views'];entries=[]
    for source in sources:
        match=re.search(r'余量按非负整数([^，。]+)计',source['text'])if source['role']=='user'else None
        if not match:continue
        unit=match.group(1)
        entries.append(dict(episode=source['episode_id'],source_id=source['id'],complete_user_message=source['text'],
            stated_domain='nonnegative integers',unit=unit,
            exact_domain_phrase_present={v:'非负整数'in text for v,text in views.items()},
            additional_unmeasured_probe=dict(scenario='Declared quantity observed as0.5'+unit,
                expected_contract='Outside the explicitly declared integer domain;requires separately frozen adjudication and full-source control before scoring.',
                model_response=None,semantic_loss_measured=False)))
    return dict(kind='literal_source_domain_coverage_audit',entries=entries,
        source_constraints=len(entries),new_model_calls=0,original_reference_changed=False,
        all82existing_cases_cover_outside_integer_domain=False,
        missing_literal_phrase_is_not_by_itself_a_measured_semantic_error=True,
        same_graph_roundtrip_does_not_certify_source_completeness=True)


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('case',nargs='?');a.add_argument('--domain-audit',action='store_true');a.add_argument('--archive',type=Path,default=r.DEFAULT);args=a.parse_args()
    report=r.check(args.archive)
    if not args.domain_audit and args.case is None:a.error('case or --domain-audit required')
    data=r.p.read(args.archive)
    print(json.dumps(domain_audit(data)if args.domain_audit else trace(data,report,args.case),ensure_ascii=False,indent=2))
