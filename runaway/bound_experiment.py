"""D-0011 pre-frozen two-person experiment, bounded to 24 new invocations."""
import argparse
import json
import os
from pathlib import Path
import time

from .bound_memory import SCHEMA,make_request,bind
from .bound_world import build_world
from .card import canonical,digest
from .compression import reference,audit_request,AUDIT_SCHEMA,validate_audit,metrics
from .decision_audit import audit_run
from .decision_experiment import LimitedCalls
from .decision_transfer import predict
from .pipeline import write_once
from .portable import make_expression
from .profile import export_profile
from .selfplay import ROOT,read,browser,BROWSER_SCHEMA
from .selfplay_world import oracle_memory,synthetic_sources

CONDITIONS=('trajectory','detailed','legacy','compact','wrong_person','oracle')


def sources():
    return [str(p.relative_to(ROOT)) for p in sorted((ROOT/'runaway').glob('*.py'))]+['web/dist/core.mjs','web/dist/text-integrity.mjs','web/dist/manual-core.mjs','scripts/read-stdin-json.mjs','scripts/selfplay-browser.mjs']


def hashes():return {p:digest((ROOT/p).read_text()) for p in sources()}


def freeze(out):
    root=Path(out);root.mkdir(parents=True,exist_ok=False)
    body={'schema_version':1,'benchmark_version':4,'origin':'fully_synthetic','stage':'pre_frozen_bound_memory','created_at':time.time(),
          'authorization':'D-0011','world':build_world(),'model':'gpt-6-luna','decoder_model':'gpt-6.1-sol','review_model':'gpt-6.1-sol',
          'conditions':list(CONDITIONS),'calls_limit':24,'budget':1000,'candidate_budget':'max(200, floor(0.90 * same-profile legacy characters))',
          'scope':'New24-call unit, no D-0010 leftovers. Synthetic trajectories only, same authored families, all old cohorts consumed.',
          'decoder_gate':{'primary_min':.95,'twins_all_correct':True,'order_perfect':True,'current_requests_all_correct':True,'unknown_all_correct':True},
          'promotion_gate':{'primary_and_counterfactual_not_below_legacy':True,'twins_all_correct':True,'all_planned_profiles_and_candidates':True,'current_requests_no_errors_or_missing':True,'unknowns_no_errors_or_missing':True,'order_no_errors_or_missing':True,'candidate_total_token_ratio_max':.90,'candidate_each_token_ratio_max':1.0,'all_model_reviewed_facets_retained_no_unsupported':True,'real_person_validity_required_for_general_claim':True},
          'stopping':'Oracle control gate fails, transport fails, unresolved prior attempt or24intent limit: stop further inference. Global limits:1 extraction repair for structural/text-integrity error,2 action FORMAT repairs,0 candidate or audit repairs. No score-based candidate selection. No policy/test information in extraction/compression.',
          'audit_policy':'Both old and new prompt use the same facet reviewer. Rejected behavioral candidates stay visibly unverified; full review gate required for experimental promotion.',
          'cost_policy':'Complete memory text counted by existing local Qwen tokenizer, same people, not Codex billing tokens. No probability/RIG estimate.',
          'code_hashes':hashes()}
    plan={**body,'id':digest(canonical(body))};write_once(root/'snapshot.synthetic.json',plan)
    for name in body['code_hashes']:
        p=root/'frozen-source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    return plan


def controls(world,predictions):
    # Same failure-aware metrics as the later comparison; no missing-as-observed-violation bookkeeping.
    from .decision_audit import readout
    score=readout(world,predictions,'oracle')
    score['passed']=(score['primary']['end_to_end_rate'] is not None and score['primary']['end_to_end_rate']>=.95 and
                     all(score[key]['missing']==0 and score[key].get('observed_incorrect',score[key].get('observed_violations',0))==0
                         for key in ['twins','order','current_instructions','unknown']))
    return score


def run(out,generate=None):
    root=Path(out)
    if (root/'report.synthetic.json').exists() or (root/'predictions.synthetic.json').exists():raise ValueError('Completed output exists; do not rerun a consumed experiment')
    lock=root/'.run.lock';fd=os.open(str(lock),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:return _run(root,generate)
    finally:lock.unlink()


def _run(root,generate=None):
    plan=read(root/'snapshot.synthetic.json')
    if plan['id']!=digest(canonical({k:v for k,v in plan.items() if k!='id'})) or plan['code_hashes']!=hashes():raise ValueError('Frozen plan/code changed')
    kwargs={} if generate is None else {'generate':generate}
    calls=LimitedCalls(root,plan['calls_limit'],**kwargs);world=plan['world'];cases=[c['public'] for c in world['test']]
    predictions={p['id']:{} for p in world['personas']};learned={};failures={};gate=None;repairs=0;memories={}
    try:
        for p in world['personas']:
            print(p['id']+': oracle',flush=True)
            predictions[p['id']]['oracle']=predict(calls,oracle_memory(p['policy']),cases,plan['decoder_model'])
        gate=controls(world,predictions);write_once(root/'decoder-gate.json',gate)
        if not gate['passed']:raise ValueError('Decoder control gate failed; no memory comparison')
        print('shared training proposals',flush=True)
        proposals=predict(calls,'',[c['public'] for c in world['training']],plan['model'])
        for p in world['personas']:
            pid=p['id'];directory=root/pid;directory.mkdir()
            original=synthetic_sources(world,p,{0:proposals});write_once(directory/'trajectory.synthetic.json',original)
            prompt=browser('request',original,plan['budget'])['request'];first_error=None;bundle=None;answer=None
            for attempt in range(2):
                print(pid+': extract '+str(attempt),flush=True)
                value=calls.call(prompt,BROWSER_SCHEMA,plan['model'])
                try:bundle=browser('validate',original,plan['budget'],value);answer=value;break
                except ValueError as exc:
                    first_error=str(exc);write_once(directory/f'extraction-{attempt}.failure.json',{'error':str(exc),'answer':value})
                    if attempt==0 and repairs<1:
                        repairs+=1;prompt+='\nRepair this invalid result against the SAME unchanged original sources. Restore generated damaged text only from those sources; never guess missing source text or add preferences.\nERROR: '+str(exc)+'\nPREVIOUS_JSON:\n'+json.dumps(value,ensure_ascii=False)
                    else:break
            if bundle is None:failures[pid+'/extract']=first_error;continue
            detailed,_=export_profile(bundle['profile']);record={'sources':original,'answer':answer,'profile':bundle['profile'],'legacy_portable':bundle['portable'],'portable':None,'detailed':detailed,'first_pass_error':first_error,'tiny':None,'tiny_error':'Not run.'}
            write_once(directory/'extracted.synthetic.json',record)
            candidate_budget=max(200,int(len(bundle['portable']['text'])*.90));record['candidate_budget']=candidate_budget
            try:
                print(pid+': bound compression',flush=True)
                value=calls.call(make_request(bundle['profile'],candidate_budget),SCHEMA,plan['model'])
                text,bindings=bind(value,bundle['profile'],candidate_budget);record['decision']=value;record['private_bindings']=bindings
                record['portable']=make_expression(text,bundle['profile']['id'],'program_bound_behavioral_candidate_v3')
            except Exception as exc:failures[pid+'/compress']=str(exc)
            if calls.backend_failed:raise ValueError('Backend failed; stop all further inference')
            write_once(directory/'candidate-stage.synthetic.json',record)
            for condition,text in [('legacy',record['legacy_portable']['text']),('compact',record['portable']['text'] if record['portable'] else None)]:
                if text is None:continue
                try:
                    print(pid+': audit '+condition,flush=True)
                    ref=reference(bundle['profile']);audit=calls.call(audit_request(ref,text),AUDIT_SCHEMA,plan['review_model']);validate_audit(audit,ref,text)
                    result=metrics(ref,audit,text,candidate_budget if condition=='compact' else plan['budget'],len(detailed))
                    key='audit' if condition=='compact' else 'audit_legacy';record[key]={'audit':audit,'metrics':result}
                    if condition=='compact' and not result['accepted']:record['audit_warning']='Facet review flagged losses; unverified behavioral candidate only.'
                except Exception as exc:
                    failures[pid+'/audit-'+condition]=str(exc)
                    if calls.backend_failed:raise
            learned[pid]=record;write_once(directory/'learned.synthetic.json',record)
        for p in world['personas']:
            pid=p['id'];record=learned.get(pid);twin=learned.get(p['twin']);path=root/pid/'trajectory.synthetic.json'
            memories[pid]={'trajectory':canonical(read(path)) if path.exists() else None,'detailed':record['detailed'] if record else None,
                           'legacy':record['legacy_portable']['text'] if record else None,'compact':record['portable']['text'] if record and record['portable'] else None,
                           'wrong_person':twin['portable']['text'] if twin and twin['portable'] else None,'oracle':oracle_memory(p['policy'])}
        write_once(root/'memories.synthetic.json',memories)
        for p in world['personas']:
            for condition,memory in memories[p['id']].items():
                if condition=='oracle' or memory is None:continue
                print(p['id']+': predict '+condition,flush=True)
                predictions[p['id']][condition]=predict(calls,memory,cases,plan['decoder_model'])
    except Exception as exc:failures['stopped']=str(exc)
    write_once(root/'predictions.synthetic.json',predictions)
    audit=audit_run(root);write_once(root/'fidelity-audit.json',audit)
    # Keep conventional keys for existing dashboard, but metrics are explicitly failure-aware.
    report={'schema_version':1,'snapshot_id':plan['id'],'origin':'fully_synthetic','stage':'pre_frozen_evaluated','decoder_gate':gate,'conditions':audit['conditions'],
            'failures':failures,'first_pass_profiles':sum(r['first_pass_error'] is None for r in learned.values()),'final_profiles':len(learned),'planned_profiles':len(world['personas']),
            'completed_model_calls':len(list((root/'calls').glob('*.response.json'))),'calls_limit':24,'generator_model':plan['model'],'decoder_model':plan['decoder_model'],
            'extraction_repairs_used':repairs,'format_repairs_used':getattr(calls,'action_repairs',0),'promotion':'pending_offline_token_and_quality_readout','real_person_fidelity_verified':False}
    write_once(root/'report.synthetic.json',report);return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze','run']);p.add_argument('--out',required=True);a=p.parse_args()
    result=freeze(a.out) if a.command=='freeze' else run(a.out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('world','code_hashes')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
