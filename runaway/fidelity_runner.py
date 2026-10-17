"""Single-use stress comparison. Real invocation requires separately verified approval.

Offline tests inject a fake backend. Never automatically resumes, repairs or
retries a call. Reuses the existing180-second CLI/isolation observer unchanged.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

from . import fidelity_plan as fp, fidelity_stress as fs, generation, bound_memory
from .card import canonical, digest, parse_answer
from .execution_ledger import collect, summarize, start_attempt, checked, validate_attempt
from .pipeline import write_once
from .selfplay import browser, SYSTEM
from .taste_plan import reader_job
from .taste_executor import FrozenCalls, ORIGINAL_RUN_BOUNDED, answers_checked, runtime_check, atomic

now=lambda:datetime.now(timezone.utc).isoformat()


class DirectCalls:
    observed_runner=FrozenCalls.observed_runner

    def __init__(self, out, config, backend):
        self.out=Path(out);(self.out/'calls').mkdir()
        self.config=config;self.backend=backend;self.cli=shutil.which('codex')
        self.counts=Counter();self.stopped=False;self.reason=None;self.current=None;self.trace=None
        self.reused=[]
        self.update()

    def update(self):
        self.ledger=summarize(collect(self.out))
        atomic(self.out/'status.json',{'updated_at':now(),'attempts':self.ledger['execution_records'],
              'stage_attempts':dict(self.counts),'current':self.current,'stopped':self.stopped,
              'stop_reason':self.reason,'cap':self.config['calls_max'],'ledger':self.ledger})

    def stop(self, reason, **extra):
        self.stopped=True;self.reason={'kind':reason,**extra};self.current=None
        try:self.update()
        except Exception:
            self.ledger={'integrity_uncertain':True,'known_usage':None,'execution_records':None}
            atomic(self.out/'status.json',{'stopped':True,'stop_reason':self.reason,'ledger':self.ledger})

    def call(self, stage, request):
        if self.stopped:raise ValueError('Batch stopped')
        try:
            records=collect(self.out)
            if any(r['outcome'] != 'completed' or r['usage'] is None for r in records):raise ValueError('Unresolved prior state or usage')
            if stage not in self.config['stage_caps'] or len(records)>=self.config['calls_max'] or self.counts[stage]>=self.config['stage_caps'][stage]:raise ValueError('Stage/global call cap')
            if set(request)!={'prompt','schema','model','system'} or request['system']!=SYSTEM:raise ValueError('Unexpected request envelope')
            model=self.config['models']['generator' if stage in ('shared_extraction','new_compression') else 'reader']
            if request['model']!=model:raise ValueError('Unexpected model')
            key=digest(canonical(request));path=self.out/'calls'/key
            if key in self.config['forbidden_request_ids']:raise ValueError('Sealed prior request is forbidden')
            if path.with_suffix('.response.json').exists():
                response=checked(path.with_suffix('.response.json'))
                validate_attempt(path.with_suffix('.attempt.json'),response['execution_id'],key)
                self.reused.append({'stage':stage,'request_id':key,'execution_id':response['execution_id'],
                                    'meaning':'Identical planned input reuses one completed response; not an independent read or extra invocation.'})
                return response['answer']
            if path.with_suffix('.attempt.json').exists():raise ValueError('Existing attempt; no resume/retry')
            write_once(path.with_suffix('.request.json'),request)
            attempt=start_attempt(path.with_suffix('.attempt.json'),key)
            self.counts[stage]+=1;self.current={'stage':stage,'request_id':key,'execution_id':attempt['execution_id']};self.update()
            # Check the durable intent again immediately before the only backend entry.
            current=collect(self.out)
            if len(current)!=len(records)+1 or sum(r['outcome']=='unresolved_invocation_intent' for r in current)!=1:raise ValueError('Invocation intent became uncertain')
        except Exception:
            self.stop('checkpoint_or_policy_failure');raise
        provenance=None;self.trace=None
        try:
            raw,provenance=self.backend(request['prompt'],request['model'],timeout=180,schema=request['schema'],system=SYSTEM)
            value={'answer':parse_answer(raw),'provenance':provenance,'request_id':key,'execution_id':attempt['execution_id']}
            value['sha256']=digest(canonical(value));write_once(path.with_suffix('.response.json'),value)
        except Exception as exc:
            failure={'error_type':type(exc).__name__,'error':str(exc),'request_id':key,'execution_id':attempt['execution_id'],
                     'provenance':provenance or getattr(exc,'provenance',None) or self.trace or {}}
            if getattr(exc,'backend_invoked',True) is False:failure['backend_invoked']=False
            failure['sha256']=digest(canonical(failure));write_once(path.with_suffix('.failure.json'),failure)
            self.stop('model_or_format_failure',stage=stage);raise
        self.current=None;self.update()
        if self.ledger['executions_missing_usage']:
            self.stop('usage_unknown');raise ValueError('Usage unknown; no further invocation')
        return value['answer']


def scores(world, values):return {task:fs.score(world,values,task) for task in ('current_choice','historical_reconstruction','joint')}


def execute(root, out, backend=None, count=None, approval=None):
    root=Path(root);out=Path(out);proposal=fp.preflight(root);real=backend is None
    if real:
        if not approval or approval.get('proposal_id')!=proposal['id'] or approval.get('status')!='approved' or not approval.get('human_source'):
            raise ValueError('Caller must independently verify separate human approval for this exact proposal')
        evidence=json.loads((root/'executor-acceptance.json').read_text())
        if proposal.get('offline_acceptance_sha256')!=__import__('hashlib').sha256((root/'executor-acceptance.json').read_bytes()).hexdigest() or not evidence['all_checks_passed']:
            raise ValueError('Offline acceptance missing/changed')
        if runtime_check(proposal)!=evidence['runtime_local_only']:raise ValueError('Frozen runtime drifted')
        fd=os.open(str(root/'execution-intent.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:json.dump({'proposal_id':proposal['id'],'output':str(out.resolve()),'human_source':approval['human_source'],'at':now()},stream)
        backend=generation.codex_generate
    out.mkdir(parents=True,exist_ok=False)
    world=json.loads((root/'fixtures.private.json').read_text());calls=DirectCalls(out,proposal,backend)
    values={};memories={};failures={};gates={};tokenizer=None;complete=False
    generation.run_bounded=calls.observed_runner
    try:
        jobs=[json.loads(x) for x in (root/'reader-jobs.jsonl').read_text().splitlines()]
        for condition in ('full_history','wrong_person_history','current_policy_oracle','none'):
            predictions=values.setdefault(condition,{})
            for job in jobs:
                if job['id']!=condition:continue
                query=json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n',1)[1])['queries']
                predictions[job['persona_id']]=answers_checked(calls.call(condition,job['request']),query)
                atomic(out/'answers.json',values)
            result=scores(world,predictions);full=scores(world,values.get('full_history',{}))
            gates[condition]=fp.gates(condition,result,full);atomic(out/'gates.json',gates)
            if not gates[condition]['passed']:calls.stop('reader_gate_failed',gate=condition);break
        if not calls.stopped:
            if count is None:
                import llama_cpp
                tokenizer=llama_cpp.Llama(model_path=proposal['tokenizer_path'],vocab_only=True,n_gpu_layers=0,verbose=False)
                count=lambda text:len(tokenizer.tokenize(text.encode(),add_bos=False,special=False))
            gen=[json.loads(x) for x in (root/'generation-jobs.jsonl').read_text().splitlines()]
            people={p['id']:p for p in world['people']}
            for job in gen:
                pid=job['persona_id'];budget=job['budget'];limit=job['character_limit'];bundle=None
                try:
                    answer=calls.call('shared_extraction',job['request'])
                    bundle=browser('validate',fp.history_sources(people[pid]),limit,answer)
                    text=bundle['portable']['text'];units=count(text)
                    if units>budget:raise ValueError('Actual token budget exceeded; no truncation')
                    memories[(pid,'current_browser',budget)]={'text':text,'units':units}
                except Exception as exc:
                    if calls.stopped:raise
                    failures[f'{pid}:current_browser:{budget}']=str(exc)
                if bundle is None:
                    failures[f'{pid}:new_bound:{budget}']='No valid shared extraction';continue
                try:
                    request={'prompt':bound_memory.make_request(bundle['profile'],limit),'schema':bound_memory.SCHEMA,
                             'model':proposal['models']['generator'],'system':SYSTEM}
                    answer=calls.call('new_compression',request)
                    text,_=bound_memory.bind(answer,bundle['profile'],limit);units=count(text)
                    if units>budget:raise ValueError('Actual token budget exceeded; no truncation')
                    memories[(pid,'new_bound',budget)]={'text':text,'units':units}
                except Exception as exc:
                    if calls.stopped:raise
                    failures[f'{pid}:new_bound:{budget}']=str(exc)
            for (pid,condition,budget),memory in memories.items():
                public=[c['public'] for c in people[pid]['cases']]
                job=reader_job('actual_memory',pid,memory['text'],public,fs.READER,12,'actual_memory')
                predictions=values.setdefault(condition+':'+str(budget),{})
                predictions[pid]=answers_checked(calls.call('actual_memory_reader',job['request']),public)
                atomic(out/'answers.json',values)
            complete=True
    except Exception as exc:
        if not calls.stopped:calls.stop('local_or_format_failure',error_type=type(exc).__name__,error=str(exc))
    finally:
        generation.run_bounded=ORIGINAL_RUN_BOUNDED
        if tokenizer is not None:tokenizer.close()
    conditions=['full_history','wrong_person_history','current_policy_oracle','none']+[
        name+':'+str(b) for b in fp.BUDGETS for name in ('current_browser','new_bound')]
    try:calls.update()
    except Exception:calls.stop('uncertain_checkpoint_state')
    report={'status':'complete' if complete and not calls.stopped else 'stopped',
            'proposal_id':proposal['id'],'calls':calls.ledger,'stage_attempts':dict(calls.counts),
            'stop_reason':calls.reason,'gates':gates,'scores':{name:scores(world,values.get(name,{})) for name in conditions},
            'memories':[{'persona_id':pid,'condition':name,'budget':b,**m} for (pid,name,b),m in memories.items()],
            'local_validation_failures':failures,'real_person_fidelity_verified':False,
            'identical_requests_reused_offline':calls.reused,
            'interpretation':'Small paired synthetic pilot; current/history and all denominators retained. No population significance or likelihood information gain.',
            'external_model_calls':calls.ledger.get('execution_records') if real else 0,
            'backend_kind':'actual_service' if real else 'injected_fake_not_model_quality'}
    write_once(out/'report.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proposal',required=True)
    p.add_argument('--run',action='store_true');p.add_argument('--out');p.add_argument('--approval');a=p.parse_args()
    if a.run:
        if not a.out or not a.approval:p.error('--run needs --out and separately verified --approval receipt')
        r=execute(a.proposal,a.out,approval=json.loads(Path(a.approval).read_text()))
        print(json.dumps({'status':r['status'],'calls':r['calls']['execution_records']}))
    else:print(json.dumps({'proposal_id':fp.preflight(a.proposal)['id'],'external_model_calls':0}))
