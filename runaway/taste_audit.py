"""Replay D-0015 evidence offline; curated semantic cases, no LLM judge.

The observed U is not itself classified as information loss or format refusal.
Specific annotations below are supported by quoted source/profile/memory spans
and executable event truth. They are consumed-data diagnostics, not new effects.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import zipfile

from .card import canonical,digest
from .selfplay import BROWSER_SCHEMA,SYSTEM,browser
from .bound_memory import SCHEMA,make_request,bind
from .production_adapters import sources
from .synthetic_metric_world import resolve
from .pipeline import write_once


def load(path):
    with zipfile.ZipFile(path) as archive:
        manifest=json.loads(archive.read('d0015/manifest.json'))
        data={name:archive.read('d0015/'+name) for name in manifest}
    if any(hashlib.sha256(data[name]).hexdigest()!=want for name,want in manifest.items()):
        raise ValueError('Sealed evidence changed')
    return data


def audit(path):
    files=load(path);read=lambda name:json.loads(files[name])
    world=read('metric/world.private.json');people={p['id']:p for p in world['people'] if p['split']=='eval'}
    memories=read('memories.synthetic.json');trials=read('trials.private.json')['trials'];predictions=read('decoder-answers.synthetic.json')
    cells={};stage_rows=[];traces=[]
    for person in people.values():
        for budget in (128,384):
            chars=budget*2;source=sources(person['history'])
            request=browser('request',source,chars)['request']
            key=digest(canonical({'prompt':request,'schema':BROWSER_SCHEMA,'model':'gpt-6-luna','system':SYSTEM}))
            response=read('calls/'+key+'.response.json');answer=response['answer']
            bundle=browser('validate',source,chars,answer)
            bound_request=make_request(bundle['profile'],chars)
            bound_key=digest(canonical({'prompt':bound_request,'schema':SCHEMA,'model':'gpt-6-luna','system':SYSTEM}))
            bound_response=read('calls/'+bound_key+'.response.json')
            new_text,_=bind(bound_response['answer'],bundle['profile'],chars)
            old_text=next(r['memory'] for r in memories if (r['persona_id'],r['budget'],r['condition'])==(person['id'],budget,'current_browser'))
            stored_new=next(r['memory'] for r in memories if (r['persona_id'],r['budget'],r['condition'])==(person['id'],budget,'new_bound'))
            if bundle['portable']['text']!=old_text or new_text!=stored_new:raise ValueError('Product replay differs')
            cells[(person['id'],budget)]={'person':person,'profile':bundle['profile'],'old':old_text,'new':new_text,
                'extraction_request_id':key,'bound_request_id':bound_key}
            stage_rows.append({'persona_id':person['id'],'budget':budget,'claims':len(answer['claims']),
                'profile_id':bundle['profile']['id'],'extraction_request_id':key,'bound_request_id':bound_key,
                'original_private_source_preserved':True,'actual_browser_and_bind_replay_equal':True,
                'portable_has_day_or_record_anchor':bool(re.search(r'第\d+天|r\d{2}',old_text+new_text))})
    for memory in memories:
        person=people[memory['persona_id']]
        trial=next(t for t in trials if (t['persona_id'],t['condition'],t['budget'])==(person['id'],memory['condition'],memory['budget']))
        cell=cells[(person['id'],memory['budget'])]
        for case in person['queries']:
            value=predictions[trial['trial_id']][case['public']['id']]
            traces.append({'trial_id':trial['trial_id'],'persona_id':person['id'],'condition':memory['condition'],
                'budget':memory['budget'],'query':case['public'],'allowed_answers':case['allowed_answers'],
                'observed_answer':value,'correct':value in case['allowed_answers'],'memory_sha256':digest(memory['memory']),
                'extraction_request_id':cell['extraction_request_id'],'bound_request_id':cell['bound_request_id'],
                'cause':'not_inferred_from_U; see specific curated cases'})
    ids=list(people);first,second=ids;small=cells[(first,128)];large=cells[(first,384)];other=cells[(second,384)]
    def event(person,identity):return next(e for e in person['events'] if e['id']==identity)
    def line(person,identity):return next(s for s in person['history'].splitlines() if s.startswith('记录'+identity+' /'))
    def query(person,key,at,context=None):
        return next(c for c in person['queries'] if c['public']['key']==key and c['public']['at']==at and (context is None or c['public']['context']==context))
    def case(identity,cell,condition,q,source_ids,classification,claim_ids=(),note='',proof=None):
        person=cell['person'];memory=cell['old' if condition=='current_browser' else 'new']
        selected=[c for c in cell['profile']['claims'] if c['id'] in claim_ids]
        return {'id':identity,'persona_id':person['id'],'condition':condition,'budget':128 if cell is small else 384,
            'classification':classification,'source_lines':[line(person,i) for i in source_ids],
            'extraction_claims':selected,'extraction_unknowns':cell['profile']['unknowns'],
            'memory':memory,'reader_query':q['public'],'gold':q['allowed_answers'],'observed':'U',
            'extraction_request_id':cell['extraction_request_id'],'bound_request_id':cell['bound_request_id'],
            'interpretation':note,'deterministic_witness':proof,'model_causal_effect_verified':False}
    # An omitted old marker: physically retained in private source, absent from
    # the claim projection and portable text. No assertion of source deletion.
    p=small['person'];q=query(p,'mark',2);alternate=copy.deepcopy(p['events'])
    next(e for e in alternate if e['id']=='r01')['value']='dot' if event(p,'r01')['value']=='line' else 'line'
    marker=event(p,'r01')['value'];word={'line':'短线','dot':'圆点'}[marker]
    if word in small['old']:raise ValueError('Marker-loss annotation no longer matches')
    cases=[case('old_marker_missing_from_portable',small,'current_browser',q,['r01','r10'],
        'observed_loss_for_historical_diagnostic',note='The private profile still archives the full source. Its claim projection and portable prompt do not retain this past marker value. A date-only wrapper cannot supply the missing value.',
        proof={'past_answers':[resolve(p['events'],q['public'])[0],resolve(alternate,q['public'])[0]],
               'both_have_cleared_current_marker':resolve(p['events'],{'key':'mark','at':16,'context':{}})[0]==resolve(alternate,{'key':'mark','at':16,'context':{}})[0]})]
    # Same current automation, different revocation time: the past answer is
    # non-identifying even if a perfect reader understands the current prose.
    q=query(p,'auto',14,{'irreversible':True});alternate=copy.deepcopy(p['events'])
    next(e for e in alternate if e['id']=='r15')['day']=8
    cases.append(case('revocation_time_lost',small,'new_bound',q,['r05','r06','r15'],
        'observed_loss_of_validity_interval',note='The retained current choice is compatible with two revocation times. Those histories disagree at day14; cutoff metadata alone cannot reconstruct the interval.',
        proof={'past_answers':[resolve(p['events'],q['public'])[0],resolve(alternate,q['public'])[0]],
               'current_answers':[resolve(p['events'],{'key':'auto','at':16,'context':{'irreversible':True}})[0],resolve(alternate,{'key':'auto','at':16,'context':{'irreversible':True}})[0]]}))
    q=query(p,'auto',16,{'irreversible':True})
    if '仍自动处理' not in small['new']:raise ValueError('Retained-action annotation no longer matches')
    cases.append(case('action_retained_reader_still_U',small,'new_bound',q,['r05','r15'],
        'retained_current_action_missing_envelope_or_reader_compatibility_unresolved',
        note='The prose explicitly retains automatic handling after revocation. D0015 supplied no source_cutoff envelope. U does not prove that date syntax caused refusal; a new framing/cutoff ablation is necessary.',
        proof={'retained_span':'仍自动处理','source_cutoff':15,'cutoff_was_not_a_decoder_payload_field':True}))
    # A real current-state error, not excused by reclassifying past queries.
    p=other['person'];q=query(p,'layout',14,{'repeated':False});claim=next(c for c in other['profile']['claims'] if c['id']=='entry_layout')
    target_types=[event(p,e['target'])['op'] for e in p['events'] if e['op']=='revoke']
    if '撤销其撤销记录' not in canonical(claim) or 'revoke' in target_types:raise ValueError('Second-order-revocation annotation no longer matches')
    cases.append(case('invented_second_order_revocation',other,'new_bound',q,['r11','r12','r13','r14'],
        'current_policy_content_error_already_in_extraction',['entry_layout'],
        note='The extraction asserts that revoking a revocation restored the replacement. There is no revocation-of-revocation event in this source. Default layout remains minimal; only the repeated-help exception chooses a prominent entry. The compiler repeats this false current policy.',
        proof={'current_default':resolve(p['events'],{'key':'layout','at':16,'context':{'repeated':False}})[0],
               'revoke_target_operation_types':target_types,'unsupported_claim_span':'撤销其撤销记录使该替代偏好恢复。'}))
    p=large['person'];q=query(p,'auto',16,{'irreversible':True})
    if '该情境当前选择未知' not in large['new']:raise ValueError('Unknown-substitution annotation no longer matches')
    cases.append(case('known_base_choice_replaced_with_unknown',large,'new_bound',q,['r05','r06','r15'],
        'current_policy_semantic_loss_in_claim_bounds',['sort_choice'],
        note='The source explicitly retains other records after revocation, so the base automatic preference remains. The extracted exception/unknown field instead marks the condition unknown; bound compression preserves that error.',
        proof={'current_choice':resolve(p['events'],q['public'])[0],'memory_span':'该情境当前选择未知'}))
    q=query(p,'film',16,{})
    cases.append(case('genuine_unknown_domain',large,'new_bound',q,[],
        'correct_abstention',note='No film preference occurs in source events. U is correct here; unknown is not automatically a failure.',
        proof={'film_events':sum(e.get('key')=='film' for e in p['events'])}))
    return {'origin':'fully_synthetic','stage':'consumed_D0015_offline_trace_audit','external_model_calls':0,
        'original_primary_correct_per_cell':4,'original_primary_planned_per_cell':48,'original_answers_unchanged':True,
        'replayed_cells':stage_rows,'trace_count':len(traces),'traces':traces,'representative_cases':cases,
        'findings':['Physical private sources survive; loss refers to claim projections and portable surfaces.',
            'There are both real historical information losses and current-policy errors before compression.',
            'Some current action content survives; 192 U alone cannot identify a format-refusal mechanism.',
            'Changing the task cannot excuse erroneous current updates/revocations.',
            'No LLM ablation was run; date-wrapper efficacy remains unverified.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    result=audit(a.evidence);write_once(Path(a.out),result)
    print(json.dumps({'traces':result['trace_count'],'cases':len(result['representative_cases']),'external_model_calls':0}))


if __name__=='__main__':main()
