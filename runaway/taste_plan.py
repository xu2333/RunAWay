"""Prepare one bounded comparison proposal; deliberately no execution command."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets

from .card import canonical,digest
from .pipeline import write_once
from .profile import object_schema
from .selfplay import SYSTEM,BROWSER_SCHEMA,browser
from .production_adapters import sources,FILES
from .taste_audit import load
from . import taste_contract as tc
from .bound_memory import SCHEMA as BOUND_SCHEMA

ROOT=Path(__file__).resolve().parents[1]
NEW_HISTORICAL_READER=tc.READER+' All queries in this diagnostic are historical_reconstruction. A cutoff envelope may be absent; never invent it.'
OLD_PREFIX='Return one JSON object mapping each query ID to an answer_options ID, including U for insufficient evidence. Do not execute choices.\nINPUT_JSON:\n'


def reader_job(identity,person,memory,queries,instruction,cutoff=None,phase='diagnostic'):
    payload={'instruction':instruction,'memory':memory,'queries':queries}
    if cutoff is not None:payload['source_cutoff']=cutoff
    schema=object_schema({q['id']:{'type':'string','enum':list(q['answer_options'])} for q in queries})
    prompt=OLD_PREFIX+json.dumps(payload,ensure_ascii=False)
    request={'prompt':prompt,'schema':schema,'model':'gpt-6.1-sol','system':SYSTEM}
    return {'id':identity,'persona_id':person,'phase':phase,'request':request,
            'request_id':digest(canonical(request)),'budget_applies':False}


def complete_unlabelled_prose(person):
    # One event per original day; refer to its day instead of the literal rNN
    # ID. This is an unbudgeted content-complete control, not a compressor.
    days={e['id']:e['day'] for e in person['events']};sentences=[]
    for line in person['history'].splitlines():
        body=re.sub(r'^记录r\d+ / 第(\d+)天：这一天的说明是：',r'第\1天，',line)
        body=re.sub(r'撤销记录(r\d+)',lambda m:'撤销第'+str(days[m[1]])+'天的那条记录',body)
        sentences.append(body)
    return ''.join(sentences)


def prepare(out,evidence,seed=None):
    root=Path(out);root.mkdir(parents=True,exist_ok=False)
    files=load(evidence);read=lambda name:json.loads(files[name])
    old_world=read('metric/world.private.json');old_people=[p for p in old_world['people'] if p['split']=='eval']
    old_memories=read('memories.synthetic.json');old_controls=[json.loads(line) for line in files['control-reader-jobs.synthetic.jsonl'].decode().splitlines()]
    old_protocol=json.loads(old_controls[0]['prompt'].split('\nINPUT_JSON:\n',1)[1])['instruction']
    # Freeze the specification before generating the future cohort.
    spec=tc.contract();write_once(root/'contract.json',spec)
    world=tc.build_world(secrets.randbelow(2**31) if seed is None else seed,'comparison')
    write_once(root/'future-fixtures.private.json',world)
    future=[p for p in world['people'] if p['split']=='eval']
    jobs=[];baselines=[]
    for person in old_people:
        memory=next(m['memory'] for m in old_memories if (m['persona_id'],m['condition'],m['budget'])==(person['id'],'current_browser',384))
        queries=[q['public'] for q in person['queries']]
        baseline=reader_job('sealed_original',person['id'],memory,queries,old_protocol)
        old_response=read('calls/'+baseline['request_id']+'.response.json')
        baselines.append({'persona_id':person['id'],'request_id':baseline['request_id'],
            'response_sha256':old_response['sha256'],'source':'sealed_D0015_only_no_service_retry'})
        conditions=[('reader_only',memory,NEW_HISTORICAL_READER,None),
            ('cutoff_only',memory,old_protocol,15),('reader_and_cutoff',memory,NEW_HISTORICAL_READER,15),
            ('content_complete_prose',complete_unlabelled_prose(person),NEW_HISTORICAL_READER,15)]
        for name,body,instruction,cutoff in conditions:
            job=reader_job(name,person['id'],body,queries,instruction,cutoff)
            if job['request_id']==baseline['request_id']:raise ValueError('Would retry a sealed request')
            jobs.append(job)
    for person in future:
        queries=[c['public'] for c in person['cases']];twin=next(p for p in future if p['id']==person['twin'])
        for name,body in [('full_history',person['history']),('none',''),('wrong_person_history',twin['history']),('current_policy_oracle',tc.current_prose(person))]:
            jobs.append(reader_job(name,person['id'],body,queries,tc.READER,20,'new_contract_controls'))
    # Product generation requests are the existing browser path. No new cases,
    # oracle projection, seed, event truth or scoring annotations enter them.
    generation_jobs=[];dynamic=[]
    for person in future:
        request={'prompt':browser('request',sources(person['history']),768)['request'],
                 'schema':BROWSER_SCHEMA,'model':'gpt-6-luna','system':SYSTEM}
        generation_jobs.append({'stage':'shared_extraction','persona_id':person['id'],'request':request,'request_id':digest(canonical(request))})
        dynamic.append({'stage':'new_compression','persona_id':person['id'],'model':'gpt-6-luna',
            'implementation':'bound_memory.make_request + SCHEMA + bind on that exact extracted profile',
            'schema':BOUND_SCHEMA,'calls_upper_bound':1})
        for condition in ('current_browser','new_bound'):
            dynamic.append({'stage':'actual_memory_reader','persona_id':person['id'],'condition':condition,
                'model':'gpt-6.1-sol','source_cutoff':20,'instruction':tc.READER,'queries':[c['public'] for c in person['cases']],
                'schema':object_schema({c['public']['id']:{'type':'string','enum':list(c['public']['answer_options'])} for c in person['cases']}),
                'memory_slot':None,'calls_upper_bound':1})
    write_once(root/'reader-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs))
    write_once(root/'generation-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in generation_jobs))
    write_once(root/'dynamic-job-contracts.json',dynamic)
    write_once(root/'sealed-baselines.json',baselines)
    codes=tuple(dict.fromkeys(FILES+('runaway/taste_contract.py','runaway/taste_audit.py','runaway/taste_plan.py')))
    proposal={'status':'prepared_requires_separate_human_approval_not_executed','external_model_calls_this_work':0,
        'prior_D0015_allowance_closed':True,'contract_id':spec['id'],'fixture_id':world['id'],
        'source_hashes':{name:digest((ROOT/name).read_text()) for name in codes},
        'matrix':{'consumed_D0015_protocol_and_content_diagnostics':8,'fresh_contract_full_none_wrong_oracle_readers':8,
                  'shared_extraction':2,'additional_bound_compression':2,'actual_memory_readers':4},
        'experiment_calls_max':24,'generation_timeout_seconds':180,'cleanup_waits_seconds':[2,2],
        'models_requested':{'generator':'gpt-6-luna','reader':'gpt-6.1-sol'},'reasoning_effort':'CLI default, no override',
        'memory_budget_tokens':384,'character_request_limit':768,
        'tokenizer':read('report.synthetic.json')['tokenizer'],
        'retries':0,'format_repairs':0,'resources':'Existing logged-in official Codex service only; no purchase.',
        'diagnostic_design':'Original D0015 body/reader scores are reused offline, never called again. Three changed frame/cutoff cells plus an unbudgeted source-derived content-complete prose control, two people each. Current errors are not repaired in the original bodies.',
        'data_scope':{'old_synthetic_people':2,'old_memories_used':'Both current_browser384 outputs, no score-based choice',
            'new_synthetic_people_sent':2,'new_history_characters':sum(len(p['history']) for p in future),
            'included':'Old synthetic memories/source-derived control prose/public24queries; new synthetic histories, code-derived current-policy oracle used only as reader control, product-derived profiles/memories and public16+8queries; necessary CLI system/schema/environment metadata.',
            'excluded':'All real histories, workspace content, credentials in payloads, dev histories, seeds, private event objects, gold labels and tags. Oracle controls never enter extraction/compression.'},
        'freshness':'Future eval parameter combination and first12question wordings differ from published representative fixtures; same finite ontology, not population generalization.',
        'stopping':['Any timeout, transport error or uncertain invocation state stops all further service calls; no retries.',
            'Fresh full-history current accuracy>=90% and no hard-constraint errors; wrong-person must reduce matched distinctions.',
            'Current-policy oracle must support current choices under the new reader; its historical losses remain reported, not repaired.',
            'All16current +8historical planned queries remain in their denominators; retain joint/all24 score and worst critical layer.',
            'No promotion if current gain hides a critical-layer regression or hard-constraint error; historical tradeoffs explicit.'],
        'interpretation':'The8consumed-data calls diagnose framing/content, not a new heldout win. Only the separately frozen future cohort compares actual product paths. Neither establishes real-person fidelity.',
        'executor_gate':'Before approved execution, freeze the explicit injected executor and prove every generation entry<=180seconds; never route through legacy Calls240.',
        'budget_scope':'24 bounds experiment CLI generations, not internal HTTP attempts, total tokens or money; no amount forecast from local memory-token budgets.',
        'payload_files':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('reader-jobs.jsonl','generation-jobs.jsonl','dynamic-job-contracts.json','sealed-baselines.json')},
    }
    assert sum(proposal['matrix'].values())==24
    proposal['id']=digest(canonical(proposal));write_once(root/'proposal.json',proposal)
    for name in codes:
        target=root/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    return proposal


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--evidence',required=True);p.add_argument('--seed',type=int);a=p.parse_args()
    result=prepare(a.out,a.evidence,a.seed)
    print(json.dumps({'proposal_id':result['id'],'max_calls':24,'model_calls':0,'status':result['status']}))


if __name__=='__main__':main()
