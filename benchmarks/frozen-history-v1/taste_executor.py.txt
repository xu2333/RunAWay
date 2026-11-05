"""Frozen runner for the proposed24-call comparison. Preflight is offline.

Reuses D-0015's single injected180-second call/observer implementation and the
UNCHANGED generation.run_bounded cleanup (2-second drain +2-second wait).
No legacy selfplay.Calls, retry layer, automatic repair or implicit execution.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from . import generation,bound_memory,taste_contract as tc
from .card import canonical,digest,parse_answer
from .execution_ledger import collect,summarize,start_attempt,checked,validate_attempt
from .pipeline import write_once
from .profile import object_schema
from .production_adapters import sources
from .selfplay import SYSTEM,browser
from .synthetic_metric import score as old_score
from .taste_audit import load as load_old_evidence
from .taste_plan import reader_job

ROOT=Path(__file__).resolve().parents[1]
TIMEOUT=180
CAP=24
ORIGINAL_RUN_BOUNDED=generation.run_bounded
STAGE_CAPS={'full_history':2,'wrong_person_history':2,'current_policy_oracle':2,'none':2,
            'shared_extraction':2,'new_compression':2,'actual_memory_reader':4,'diagnostic':8}
CRITICAL=('strength','conditions','exceptions','hard_constraints','updates','revocations','current_instruction','unknowns')
READER_GATES={
    'full_history':{'current_accuracy_min':.90,'hard_constraint_errors_max':0,
        'required_layer_accuracy_min':.90,'required_layers':list(CRITICAL),
        'matched_correct_fraction_min':1.0,'option_consistency_min':.90},
    'wrong_person_history':{'matched_planned_positive':True,'matched_planned_equals_full':True,
        'matched_correct_strictly_less_than_full':True},
    'current_policy_oracle':{'current_accuracy_min':.90,'hard_constraint_errors_max':0,
        'required_layer_accuracy_min':.90,'required_layers':list(CRITICAL),
        'matched_correct_fraction_min':1.0,'option_consistency_min':.90},
    'on_any_gate_failure':'Stop all later calls, including compression, actual-memory reads and all8old-data diagnostics.',
    'historical':'Never used to relax current thresholds; always score and retain all8per person and joint/all24.',
}
ORDER=('full_history','wrong_person_history','current_policy_oracle','none','products','actual_memory_reader','diagnostic')
now=lambda:datetime.now(timezone.utc).isoformat()


def atomic(path,value):
    temp=path.with_name('.'+path.name+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(temp,path)


def gate(name,current,full=None,criteria=READER_GATES):
    wanted=criteria[name];checks={}
    if name=='wrong_person_history':
        checks={'positive_matched_denominator':current['matched_distinctions']['planned']>0,
            'same_matched_denominator_as_full':current['matched_distinctions']['planned']==full['matched_distinctions']['planned'],
            'matched_correct_lower_than_full':current['matched_distinctions']['correct']<full['matched_distinctions']['correct']}
    else:
        checks={'current_accuracy':current['accuracy']>=wanted['current_accuracy_min'],
            'zero_hard_errors':current['hard_constraint_errors']<=wanted['hard_constraint_errors_max'],
            'all_matched_distinctions':current['matched_distinctions']['planned']>0 and current['matched_distinctions']['correct']/current['matched_distinctions']['planned']>=wanted['matched_correct_fraction_min'],
            'option_consistency':current['option_order_pairs']['planned']>0 and current['option_order_pairs']['consistent']/current['option_order_pairs']['planned']>=wanted['option_consistency_min']}
        for tag in wanted['required_layers']:
            row=current['layers'].get(tag,{'correct':0,'planned':0})
            checks['layer_'+tag]=row['planned']>0 and row['correct']/row['planned']>=wanted['required_layer_accuracy_min']
    return {'passed':all(checks.values()),'checks':checks,'criteria':wanted,'on_failure':criteria['on_any_gate_failure']}


def score_rows(world,answers):
    return {task:tc.score(world,answers,task) for task in ('current_choice','historical_reconstruction','joint')}


class Stopped(ValueError):
    backend_invoked=False


class FrozenCalls:
    """Direct reuse of D-0015 checkpoint/deadline logic, parameterized once."""
    def __init__(self,out,config,slots,backend,publish=None):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True);(self.out/'calls').mkdir(exist_ok=False)
        self.config=config;self.slots=slots;self.backend=backend;self.publish=publish
        self.counts=Counter();self.stopped=False;self.reason=None;self.current=None;self.trace=None
        self.cli=shutil.which('codex');self.started_at=now();self.update()

    def stop(self,kind,**detail):
        self.stopped=True;self.reason={'kind':kind,**detail};self.current=None;self.update()

    def update(self):
        try:
            records=collect(self.out);ledger=summarize(records);attempts=len(records)
            if any(r['outcome']=='unresolved_invocation_intent' and (self.current is None or r['request_id']!=self.current['request_id']) for r in records):
                self.stopped=True;self.reason={'kind':'uncertain_prior_invocation'}
        except (ValueError,OSError,KeyError):
            self.stopped=True;self.reason={'kind':'uncertain_checkpoint_state'};attempts=None
            ledger={'integrity_uncertain':True,'known_usage':None,'execution_records':None,
                    'interpretation':'Cannot authenticate accounting; no further invocation. Costs are unknown, not zero.'}
        self.ledger=ledger
        state={'started_at':self.started_at,'updated_at':now(),'attempts':attempts,'cap':CAP,
            'timeout_seconds':TIMEOUT,'cleanup_waits_seconds':[2,2],'stage_attempts':dict(self.counts),
            'current':self.current,'stopped':self.stopped,'stop_reason':self.reason,'ledger':ledger}
        atomic(self.out/'status.json',state)
        if self.publish:self.publish(state)

    def observed_runner(self,args,prompt,timeout):
        if timeout!=TIMEOUT:raise Stopped('Generation subprocess deadline must be180seconds')
        if Path(args[0]).resolve()!=Path(self.cli).resolve() or args[1]!='exec':raise Stopped('Unexpected CLI')
        for flag in ('--ignore-user-config','--ephemeral','--skip-git-repo-check','--json'):
            if flag not in args:raise Stopped('Missing approved isolation flag')
        if args[args.index('--sandbox')+1]!='read-only':raise Stopped('Unexpected sandbox')
        if args[args.index('-m')+1] not in self.config['models'].values():raise Stopped('Unexpected model')
        directory=Path(args[args.index('-C')+1])
        if {p.name for p in directory.iterdir()}!={'system.txt','schema.json'}:raise Stopped('CLI working directory must contain only request metadata')
        configs=[args[i+1] for i,v in enumerate(args) if v=='-c']
        for required in ('project_doc_max_bytes=0','memories.use_memories=false','memories.generate_memories=false','web_search="disabled"','mcp_servers={}'):
            if required not in configs:raise Stopped('Missing approved data isolation config')
        if any('reasoning_effort' in v for v in configs):raise Stopped('No reasoning override approved')
        disabled=[args[i+1] for i,v in enumerate(args) if v=='--disable']
        if not {'shell_tool','multi_agent','multi_agent_v2','apps','plugins','hooks','browser_use','computer_use','memories','skill_search','image_generation','view_image'}.issubset(disabled):raise Stopped('Missing disabled feature')
        if '--enable' not in args or args[args.index('--enable')+1]!='skip_host_skill_discovery':raise Stopped('Host skill discovery must be skipped')
        start=time.monotonic()
        try:result=ORIGINAL_RUN_BOUNDED(args,prompt,timeout)
        except generation.GenerationTimeout as exc:self.trace=exc.provenance;raise
        self.trace={'backend':'codex','returncode':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),
            'progress':generation.progress_metadata(result.stdout,result.stderr)}
        self.trace['usage']=self.trace['progress']['usage'];return result

    def call(self,slot,request=None):
        if self.stopped:raise Stopped('Batch stopped; no further invocation')
        try:
            records=collect(self.out)
            if any(r['outcome'] in ('unresolved_invocation_intent','failed') for r in records):
                self.stop('uncertain_or_failed_prior_invocation');raise Stopped('Unknown/failed invocation; stop globally')
        except Stopped:raise
        except Exception:
            self.stopped=True;self.reason={'kind':'uncertain_checkpoint_state'}
            raise Stopped('Checkpoint integrity uncertain; no invocation') from None
        if slot not in self.slots:self.stop('unknown_slot');raise Stopped('Unknown slot')
        descriptor=self.slots[slot];stage=descriptor['stage']
        request=request if request is not None else descriptor.get('request')
        if (not isinstance(request,dict) or set(request)!={'prompt','schema','model','system'}
                or request['system']!=SYSTEM):self.stop('invalid_request');raise Stopped('Invalid request')
        if descriptor.get('request') is not None and request!=descriptor['request']:
            self.stop('changed_static_request');raise Stopped('Static request changed')
        if descriptor.get('schema') is not None and request['schema']!=descriptor['schema']:
            self.stop('changed_dynamic_schema');raise Stopped('Dynamic schema changed')
        model=self.config['models']['generator' if stage in ('shared_extraction','new_compression') else 'reader']
        if request['model']!=model:self.stop('wrong_model');raise Stopped('Wrong stage model')
        key=digest(canonical(request))
        if key in self.config['forbidden_sealed_request_ids']:
            self.stop('sealed_request_forbidden');raise Stopped('Sealed original body/reader must be referenced offline')
        previous=descriptor.get('bound_request_id')
        if previous is not None and previous!=key:self.stop('dynamic_request_changed');raise Stopped('Bound request changed')
        descriptor['bound_request_id']=key
        req=self.out/'calls'/(key+'.request.json');response=self.out/'calls'/(key+'.response.json')
        failure=self.out/'calls'/(key+'.failure.json');attempt=self.out/'calls'/(key+'.attempt.json')
        write_once(req,request)
        if response.exists():
            value=checked(response);validate_attempt(attempt,value['execution_id'],key);return value['answer']
        if failure.exists() or attempt.exists():self.stop('unresolved_request');raise Stopped('Existing attempt; no retry')
        if len(records)>=CAP or self.counts[stage]>=STAGE_CAPS[stage]:self.stop('call_cap');raise Stopped('Frozen call cap reached')
        intent=start_attempt(attempt,key);self.counts[stage]+=1
        self.current={'slot':slot,'stage':stage,'request_id':key,'execution_id':intent['execution_id'],'started_at':now()}
        self.trace=None;self.update();provenance=None
        try:
            if self.stopped:raise Stopped('Invocation state became uncertain before backend entry')
            raw,provenance=self.backend(request['prompt'],model,timeout=TIMEOUT,schema=request['schema'],system=SYSTEM)
            value={'answer':parse_answer(raw),'provenance':provenance,'request_id':key,'execution_id':intent['execution_id']}
            value['sha256']=digest(canonical(value));write_once(response,value)
        except Exception as exc:
            failed={'error_type':type(exc).__name__,'error':str(exc),'request_id':key,'execution_id':intent['execution_id'],
                'provenance':provenance or getattr(exc,'provenance',None) or self.trace or {}}
            if getattr(exc,'backend_invoked',True) is False:failed['backend_invoked']=False
            failed['sha256']=digest(canonical(failed));write_once(failure,failed)
            self.stop('model_call_failure',slot=slot,error_type=type(exc).__name__);raise
        self.current=None;self.update()
        if self.stopped:raise Stopped('An invocation state became uncertain; stop globally')
        return value['answer']


def slots_from(root):
    root=Path(root);slots={}
    for line in (root/'reader-jobs.jsonl').read_text().splitlines():
        job=json.loads(line);stage=job['id'] if job['phase']=='new_contract_controls' else 'diagnostic'
        slot=job['phase']+':'+job['id']+':'+job['persona_id']
        slots[slot]={'stage':stage,'request':job['request'],'job':job}
    for line in (root/'generation-jobs.jsonl').read_text().splitlines():
        job=json.loads(line);slots['shared_extraction:'+job['persona_id']]={'stage':'shared_extraction','request':job['request'],'job':job}
    for job in json.loads((root/'dynamic-job-contracts.json').read_text()):
        slot=job['stage']+':'+job['persona_id']+(':'+job['condition'] if 'condition' in job else '')
        slots[slot]={'stage':job['stage'],'schema':job['schema'],'job':job}
    if len(slots)!=24 or dict(Counter(s['stage'] for s in slots.values()))!=STAGE_CAPS:raise ValueError('Matrix differs from frozen24stage caps')
    return slots


def runtime_check(config):
    if str(Path(sys.executable).absolute())!=config['python_executable']:
        raise ValueError('Use the frozen Python runtime: '+config['python_executable'])
    versions={}
    for command in ('node','codex'):
        executable=shutil.which(command)
        if not executable:raise ValueError('Missing local runtime: '+command)
        versions[command]=subprocess.check_output([executable,'--version'],text=True,timeout=5).strip()
    if int(versions['node'].lstrip('v').split('.')[0])<22:raise ValueError('Node22+ required')
    gguf=Path(config['tokenizer_path'])
    if hashlib.sha256(gguf.read_bytes()).hexdigest()!=config['tokenizer']['model_sha256']:raise ValueError('Frozen tokenizer missing or changed')
    import llama_cpp
    if llama_cpp.__version__!='0.3.36':raise ValueError('Use the frozen tokenizer implementation llama-cpp-python0.3.36')
    model=llama_cpp.Llama(model_path=str(gguf),vocab_only=True,n_gpu_layers=0,verbose=False)
    try:probe=len(model.tokenize('Offline tokenizer probe'.encode(),add_bos=False,special=False))
    finally:model.close()
    if probe<=0:raise ValueError('Tokenizer probe failed')
    return {'versions':versions,'python_executable':config['python_executable'],
        'llama_cpp_version':llama_cpp.__version__,
        'tokenizer_sha256':config['tokenizer']['model_sha256'],'tokenization_only_no_model_inference':True,'external_model_calls':0}


def preflight(root,require_evidence=True,check_runtime=False):
    root=Path(root);proposal=json.loads((root/'proposal.json').read_text());config=json.loads((root/'executor-config.json').read_text())
    if proposal['id']!=digest(canonical({k:v for k,v in proposal.items() if k!='id'})):raise ValueError('Proposal changed')
    if config['id']!=digest(canonical({k:v for k,v in config.items() if k!='id'})):raise ValueError('Executor config changed')
    if config['proposal_directory']!=str(root.resolve()):raise ValueError('Proposal moved/copied; do not bypass single-use intent')
    if hashlib.sha256((root/'executor-config.json').read_bytes()).hexdigest()!=proposal['executor']['config_sha256']:raise ValueError('Executor config file hash differs')
    if (proposal['executor']['config_id']!=config['id'] or proposal['reader_gates']!=config['reader_gates']
            or config['reader_gates']!=READER_GATES or config['stage_caps']!=STAGE_CAPS
            or config['timeout_seconds']!=TIMEOUT or config['cleanup_waits_seconds']!=[2,2]
            or config['order']!=list(ORDER)):raise ValueError('Runner policy mismatch')
    if config['global_cap']!=CAP or sum(config['stage_caps'].values())!=CAP:raise ValueError('Global call cap differs')
    if hashlib.sha256((ROOT/'examples/pilot-evidence.synthetic.zip').read_bytes()).hexdigest()!=config['old_evidence_sha256']:raise ValueError('Sealed baseline archive changed')
    for name,want in config['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=want:raise ValueError('Frozen runner/source changed: '+name)
        snapshot=root/proposal['executor']['source_snapshot']/name
        if hashlib.sha256(snapshot.read_bytes()).hexdigest()!=want:raise ValueError('Frozen source snapshot changed: '+name)
    for name,want in config['input_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=want:raise ValueError('Frozen input changed: '+name)
    if json.loads((root/'contract.json').read_text())!=tc.contract():raise ValueError('Task contract or its evaluator dependencies changed')
    if require_evidence:
        info=proposal['executor'].get('evidence')
        if not info:raise ValueError('Offline executor acceptance is not bound yet')
        if hashlib.sha256((root/info['path']).read_bytes()).hexdigest()!=info['sha256']:raise ValueError('Executor evidence changed')
        evidence=json.loads((root/info['path']).read_text())
        if evidence['config_id']!=config['id'] or not evidence['all_checks_passed'] or evidence['external_model_calls']!=0:raise ValueError('Missing offline executor acceptance')
    if check_runtime:
        current=runtime_check(config)
        if require_evidence and current!=evidence['runtime_local_only']:raise ValueError('Local runtime drifted since offline evidence; recheck before approval')
    return proposal,config,slots_from(root)


def answers_checked(value,queries):
    if not isinstance(value,dict) or set(value)!={q['id'] for q in queries} or any(not isinstance(value[q['id']],str) or value[q['id']] not in q['answer_options'] for q in queries):
        raise ValueError('Invalid/incomplete reader answer; no repair')
    return value


def claim_execution(root,proposal,approval,out):
    """One durable real-execution intent per proposal, even across output dirs."""
    value={'proposal_id':proposal['id'],'config_id':proposal['executor']['config_id'],
        'human_source':approval['human_source'],'output':str(Path(out).resolve()),'at':now(),
        'meaning':'Invocation intent, not proof the service ran. Never automatically retry this proposal.'}
    fd=os.open(str(Path(root)/'execution-intent.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)


def execute(root,out,backend=None,approval=None,count=None,publish=None,require_evidence=True):
    """Explicit fake backend for offline tests; real CLI needs an approval receipt.

    The receipt is operator bookkeeping, not cryptographic authentication of a
    human. The calling agent must independently verify direct human approval.
    """
    root=Path(root);out=Path(out);proposal,config,slots=preflight(root,require_evidence)
    real_execution=backend is None
    if real_execution:
        if not require_evidence:raise ValueError('Real execution requires bound offline evidence')
        if not approval or approval.get('proposal_id')!=proposal['id'] or approval.get('status')!='approved' or not approval.get('human_source'):
            raise ValueError('No separate verified human approval for this proposal')
        preflight(root,require_evidence=True,check_runtime=True)
        backend=generation.codex_generate
        claim_execution(root,proposal,approval,out)
        if publish is None:
            def publish(state):
                path=ROOT/'runs/real-adapters-offline-v1/readiness.json'
                if path.exists():
                    ready=json.loads(path.read_text());ready['pending_comparison_execution']=state;atomic(path,ready)
    out.mkdir(parents=True,exist_ok=False)
    world=json.loads((root/'future-fixtures.private.json').read_text());people=[p for p in world['people'] if p['split']=='eval']
    files=load_old_evidence(ROOT/'examples/pilot-evidence.synthetic.zip')
    old_people=[p for p in json.loads(files['metric/world.private.json'])['people'] if p['split']=='eval']
    calls=FrozenCalls(out,config,slots,backend,publish);fresh={};legacy={};memories={};failures={};gates={};completed=False
    generation.run_bounded=calls.observed_runner
    tokenizer=None
    try:
        for condition in ORDER[:4]:
            predictions=fresh.setdefault(condition,{})
            for slot,desc in slots.items():
                if desc['stage']!=condition:continue
                job=desc['job'];payload=json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n',1)[1])
                predictions[job['persona_id']]=answers_checked(calls.call(slot),payload['queries'])
                atomic(out/'fresh-answers.json',fresh)
            if condition!='none':
                q=tc.score(world,predictions,'current_choice')
                full=tc.score(world,fresh.get('full_history',{}),'current_choice')
                gates[condition]=gate(condition,q,full,config['reader_gates']);atomic(out/'gates.json',gates)
                if not gates[condition]['passed']:calls.stop('reader_gate_failed',gate=condition);break
        if not calls.stopped:
            if count is None:
                import llama_cpp
                gguf=Path(config['tokenizer_path'])
                if hashlib.sha256(gguf.read_bytes()).hexdigest()!=config['tokenizer']['model_sha256']:raise ValueError('Frozen tokenizer mismatch')
                tokenizer=llama_cpp.Llama(model_path=str(gguf),vocab_only=True,n_gpu_layers=0,verbose=False)
                count=lambda text:len(tokenizer.tokenize(text.encode(),add_bos=False,special=False))
            for person in people:
                pid=person['id'];bundle=None
                try:
                    answer=calls.call('shared_extraction:'+pid)
                    bundle=browser('validate',sources(person['history']),config['character_limit'],answer)
                    text=bundle['portable']['text'];units=count(text)
                    if units>config['memory_budget_tokens']:raise ValueError('Actual token budget exceeded; no truncation')
                    memories[(pid,'current_browser')]={'text':text,'units':units}
                except Exception as exc:
                    if calls.stopped:raise
                    failures[pid+':current_browser']=str(exc)
                if bundle is None:
                    failures[pid+':new_bound']='No valid shared profile';continue
                try:
                    request={'prompt':bound_memory.make_request(bundle['profile'],config['character_limit']),
                        'schema':bound_memory.SCHEMA,'model':config['models']['generator'],'system':SYSTEM}
                    value=calls.call('new_compression:'+pid,request)
                    text,_=bound_memory.bind(value,bundle['profile'],config['character_limit']);units=count(text)
                    if units>config['memory_budget_tokens']:raise ValueError('Actual token budget exceeded; no truncation')
                    memories[(pid,'new_bound')]={'text':text,'units':units}
                except Exception as exc:
                    if calls.stopped:raise
                    failures[pid+':new_bound']=str(exc)
            for condition in ('current_browser','new_bound'):
                predictions=fresh.setdefault(condition,{})
                for person in people:
                    memory=memories.get((person['id'],condition))
                    if memory is None:continue
                    queries=[c['public'] for c in person['cases']]
                    job=reader_job('actual_memory',person['id'],memory['text'],queries,tc.READER,20,'actual_memory')
                    slot='actual_memory_reader:'+person['id']+':'+condition
                    predictions[person['id']]=answers_checked(calls.call(slot,job['request']),queries)
                    atomic(out/'fresh-answers.json',fresh)
            for slot,desc in slots.items():
                if desc['stage']!='diagnostic':continue
                job=desc['job'];queries=json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n',1)[1])['queries']
                legacy.setdefault(job['id'],{})[job['persona_id']]=answers_checked(calls.call(slot),queries)
                atomic(out/'legacy-answers.json',legacy)
            completed=True
    except Exception as exc:
        if not calls.stopped:calls.stop('local_or_format_failure',error_type=type(exc).__name__,error=str(exc))
    finally:
        generation.run_bounded=ORIGINAL_RUN_BOUNDED
        if tokenizer is not None:tokenizer.close()
    # Predeclared denominators are unconditional, including every unreached
    # control/method and every old-data diagnostic group after any stop.
    fresh_scores={name:score_rows(world,fresh.get(name,{})) for name in ('full_history','wrong_person_history','current_policy_oracle','none','current_browser','new_bound')}
    old_scores={name:old_score(old_people,legacy.get(name,{})) for name in ('reader_only','cutoff_only','reader_and_cutoff','content_complete_prose')}
    calls.update()
    report={'status':'complete' if completed and not calls.stopped else 'stopped','proposal_id':proposal['id'],'config_id':config['id'],
        'calls':calls.ledger,'gates':gates,'stop_reason':calls.reason,'fresh_scores':fresh_scores,'legacy_diagnostic_scores':old_scores,
        'memories':[{'persona_id':pid,'condition':condition,**value} for (pid,condition),value in memories.items()],
        'local_validation_failures':failures,'sealed_original_baselines':'offline only; never invoked',
        'comparison_interpretable':completed and not calls.stopped and all(g['passed'] for g in gates.values()),
        'legacy_interpretation':'Consumed-data mechanism diagnostics only, not a new heldout compression win.',
        'real_person_fidelity_verified':False}
    write_once(out/'report.json',report);calls.update();return report


def freeze_config(root,proposal):
    """Bind the actual runner and fixed gate policy before service approval."""
    root=Path(root)
    code=tuple(dict.fromkeys(tuple(proposal['source_hashes'])+('runaway/taste_executor.py','runaway/synthetic_metric.py','runaway/synthetic_metric_world.py','tests/test_taste_executor.py','tests/test_taste_contract.py')))
    source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in code}
    inputs=('contract.json','future-fixtures.private.json','reader-jobs.jsonl','generation-jobs.jsonl','dynamic-job-contracts.json','sealed-baselines.json')
    body={'runner':'runaway.taste_executor.execute','call_implementation':'FrozenCalls.call',
        'proposal_directory':str(root.resolve()),
        'python_executable':str(Path(sys.executable).absolute()),
        'models':proposal['models_requested'],'timeout_seconds':TIMEOUT,'cleanup_waits_seconds':[2,2],
        'global_cap':CAP,'stage_caps':STAGE_CAPS,'order':list(ORDER),'reader_gates':READER_GATES,
        'memory_budget_tokens':proposal['memory_budget_tokens'],'character_limit':proposal['character_request_limit'],
        'tokenizer':proposal['tokenizer'],'tokenizer_path':str(Path.home()/'.ollama/models/blobs'/('sha256-'+proposal['tokenizer']['model_sha256'])),
        'forbidden_sealed_request_ids':[b['request_id'] for b in json.loads((root/'sealed-baselines.json').read_text())],
        'source_hashes':source_hashes,'input_hashes':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in inputs},
        'old_evidence_sha256':hashlib.sha256((ROOT/'examples/pilot-evidence.synthetic.zip').read_bytes()).hexdigest(),
        'proposal_invocation_intent':'execution-intent.json, created exclusively before the first real generation; forbids rerun under another output directory.',
        'reuse':'D0015 injected180sec checkpoint/observer logic; unchanged generation.run_bounded 2+2cleanup; no Calls240 or extra retry layer.',
        'answer_bearing_controls':'Source-complete prose and current-policy oracle intentionally carry reference-choice information only as reader controls. Never generation inputs.'}
    config={**body,'id':digest(canonical(body))};atomic(root/'executor-config.json',config)
    snapshot=Path('executor-frozen-source')/config['id']
    for name,want in source_hashes.items():
        target=root/snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
        write_once(target,(ROOT/name).read_text())
    proposal['source_hashes']=source_hashes;proposal['reader_gates']=READER_GATES
    proposal['executor']={'entry':'runaway.taste_executor.execute','config_path':'executor-config.json','config_id':config['id'],
        'config_sha256':hashlib.sha256((root/'executor-config.json').read_bytes()).hexdigest(),'source_snapshot':str(snapshot),'evidence':None}
    proposal['executor_gate']={'status':'runner_frozen_offline_tests_required','definition':'No real execution until the separately approved proposal and bound offline evidence pass preflight.'}
    proposal['execution_order']=list(ORDER)
    proposal['data_scope']['answer_bearing_controls']=body['answer_bearing_controls']
    proposal['data_scope']['excluded']='Real histories, workspace content, credentials in payloads, dev histories, seeds, literal scoring gold-option labels and private event/parameter/tag objects. Explicit source-derived reader controls DO contain reference-choice information, by design; they are isolated from generation.'
    return proposal


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proposal',required=True)
    p.add_argument('--run',action='store_true');p.add_argument('--approval');p.add_argument('--out');a=p.parse_args()
    if not a.run:
        proposal,config,slots=preflight(a.proposal,check_runtime=True)
        print(json.dumps({'preflight':'passed','proposal_id':proposal['id'],'config_id':config['id'],'slots':len(slots),'external_model_calls':0}));return
    if not a.approval or not a.out:raise ValueError('Explicit approval receipt and new output directory required')
    report=execute(a.proposal,a.out,approval=json.loads(Path(a.approval).read_text()))
    print(json.dumps({'status':report['status'],'calls':report['calls']['execution_records']}))


if __name__=='__main__':main()
