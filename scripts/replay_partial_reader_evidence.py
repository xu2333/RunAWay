"""Replay D-0031 with frozen source only; post-hoc completion analysis is separate."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys


def completion_analysis(s, world, jobs, memories, predictions, records):
    groups={k:{'planned':0,'strict_contract_correct':0,'missing':0} for k in (
        'decision_changing_missing','invariant_but_strict_unknown','known_action_despite_missing')}
    job_by_person={j['persona_id']:j for j in jobs};errors=[];scenarios=set()
    for p in world['people']:
        policy=s.codec.decode(memories[p['id']]['text'])
        for c in p['cases']:
            if c['public']['task']!='current_choice':continue
            observed={name:c['context'][key] for key,name in [('c0',s.stress.P),('c1',s.stress.Q)] if key in c['context']}
            missing=[name for name in (s.stress.P,s.stress.Q) if name not in observed]
            completions=[]
            for values in itertools.product((False,True),repeat=len(missing)):
                context={**observed,**dict(zip(missing,values))};r=s.codec.resolve(policy,s.stress.DOMAIN,context)
                action=str(s.stress.ACTIONS.index(r['action'])) if r['status']=='chosen' else 'U'
                completions.append({'context':context,'status':r['status'],'action':action})
            invariant=len({x['action'] for x in completions})==1 and all(x['status']=='chosen' for x in completions)
            prediction=predictions.get(p['id'],{}).get(c['public']['id'])
            if missing:
                category=('invariant_but_strict_unknown' if c['gold']=='U' else 'known_action_despite_missing') if invariant else 'decision_changing_missing'
                row=groups[category];row['planned']+=1;row['strict_contract_correct']+=prediction==c['gold'];row['missing']+=prediction is None
            if prediction!=c['gold']:
                key=job_by_person[p['id']]['request_id'];scenarios.add((p['id'],c['scenario']))
                errors.append({'person_id':p['id'],'query':c['public'],'scenario':c['scenario'],'order':c['order'],
                    'observed_context':observed,'gold':c['gold'],'gold_status':c['expected_status'],'prediction':prediction,
                    'predicted_action':c['options'].get(prediction),'action_invariant_across_missing_completions':invariant,
                    'completions':completions,'request_id':key,'execution_id':records[key]['execution_id'] if key in records else None})
    return {'status':'posthoc_structural_annotation_not_preregistered_or_a_new_score',
        'groups':groups,'failed_answers':errors,'unique_failed_person_scenarios':len(scenarios),
        'primary_scores_and_failure_target_unchanged':True,'model_reasoning_not_observed':True,
        'interpretation':'Completion enumeration describes supplied policy, not hidden model reasoning. An invariant action answer can violate the frozen strict unknown contract without identifying whether the reader assumed a missing condition false. These exploratory slices do not replace original denominators, prove state retention, or add independent samples.'}


def replay(base,count=None):
    if sys.flags.optimize:raise ValueError('Evidence replay requires assertions enabled')
    base=Path(base).resolve();frozen=base/'frozen-source';read=lambda n:json.loads((base/n).read_text())
    contract=read('contract.synthetic.json')
    for name,sha in contract['source_hashes'].items():assert hashlib.sha256((frozen/name).read_bytes()).hexdigest()==sha
    for name,sha in contract['input_hashes'].items():assert hashlib.sha256((base/contract['input_aliases'][name]).read_bytes()).hexdigest()==sha
    for name,input_name in contract['auxiliary_input_aliases'].items():assert hashlib.sha256((frozen/name).read_bytes()).hexdigest()==contract['input_hashes'][input_name]
    assert set(contract['withheld_private_input_hashes'])=={'executor-acceptance.json'}
    assert contract['calls_max']==2 and contract['stage_caps']=={'actual_memory_reader':2}
    assert contract['token_budget']==288 and contract['character_budget']==768
    sys.path.insert(0,str(frozen))
    spec=importlib.util.spec_from_file_location('frozen_partial_reader',frozen/'runs/temporal-partial-reader-v1/runner.py')
    s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
    import runaway
    assert Path(runaway.__file__).resolve().is_relative_to(frozen)
    from runaway.execution_ledger import collect,summarize,checked
    def forbidden(*args,**kwargs):raise AssertionError('Offline replay may never invoke model/runtime commands')
    s.generation.codex_generate=forbidden;s.generation.run_bounded=forbidden;s.runtime_check=forbidden
    report,world,jobs,gold=read('raw-report.synthetic.json'),read('world.synthetic.json'),read('jobs.json'),read('gold.synthetic.json')
    deliveries=read('deliveries.synthetic.json');baseline=s.semantics(world,jobs,gold,deliveries)
    assert baseline==contract['baseline_program_not_model_quality']
    design=read('design.original.synthetic.json')
    assert design['id']==contract['original_design_id']==s.digest(s.canonical({k:v for k,v in design.items() if k!='id'}))
    assert all(contract['input_hashes'][name]==design['input_hashes'][name] for name in ('jobs.json','gold.private.json'))
    if count is None:
        # Exact archived lookup: neither an estimate nor a real tokenizer recount.
        prior={v['text']:v['actual_tokens'] for v in deliveries['memories'].values()}
        prior.update({s.canonical(j['request']):deliveries['request_envelope_lengths'][j['request_id']]['actual_local_vocabulary_tokens'] for j in jobs})
        rebuilt=s.counted_deliveries(world,jobs,lambda text:prior[text])
    else:rebuilt=s.counted_deliveries(world,jobs,count)
    assert rebuilt==deliveries and deliveries['memories']==report['memories']
    assert not {j['request_id'] for j in jobs}.intersection(contract['forbidden_request_ids'])
    records=collect(base);ledger=summarize(records);lookup={r['request_id']:r for r in records};visited=set();predictions={};parse_failure=False
    assert report['backend_kind']=='actual_service' and report['proposal_id']==contract['id']
    assert report['status'] in ('complete','stopped') and (report['stop_reason'] is None)==(report['status']=='complete')
    assert report['paired_statistical_units']==1 and report['new_holdout'] is False and report['real_person_fidelity_verified'] is False
    assert report['calls']==ledger and report['external_model_calls']==len(records)<=2
    for job in jobs:
        key=job['request_id']
        if key not in lookup:break
        visited.add(key);assert read('calls/'+key+'.request.json')==job['request']
        record=lookup[key]
        if record['outcome']!='completed' or record['usage'] is None:parse_failure=True;break
        try:
            raw=checked(base/'calls'/(key+'.response.json'))['answer'];queries=json.loads(job['request']['prompt'].split('\nINPUT_JSON:\n',1)[1])['queries']
            predictions[job['persona_id']]=s.answers_checked(raw,queries)
        except ValueError:parse_failure=True;break
    assert visited==set(lookup) and predictions==read('answers.synthetic.json')
    scores=s.score(world,predictions);assert scores==report['scores'];c=scores['current_choice']
    passed=report['status']=='complete' and c['correct']==36 and c['matched_domain_contrasts']['correct']==1 and c['hard_constraints']['observed_violations']==0
    assert passed==report['strict_target_passed'] and report['stage_attempts']=={'actual_memory_reader':len(records)}
    if report['status']=='complete':assert len(records)==2 and ledger['executions_missing_usage']==0 and not parse_failure
    return {'decision':'D-0031','status':report['status'],'proposal_id':contract['id'],'strict_target_passed':passed,'stop_reason':report['stop_reason'],
        'scores':scores,'calls':ledger,'stage_costs':{'actual_memory_reader':ledger},'memories':report['memories'],
        'request_envelope_lengths':deliveries['request_envelope_lengths'],'program_proofs_not_model_quality':deliveries['proofs'],
        'posthoc_completion_analysis':completion_analysis(s,world,jobs,report['memories'],predictions,lookup),
        'actual_memory_token_recounts':2 if count else 0,'actual_request_envelope_recounts':2 if count else 0,
        'checks':{'frozen_inputs_and_51sources_verified':True,'auxiliary_world_alias_verified':True,'raw_calls_identities_usage_replayed':True,
            'authored_gold_and_original_requests_rebuilt':True,'scores_denominators_and_failure_target_rebuilt':True,'complete_deliveries_rebuilt':True,'actual_tokenizer_recounted':count is not None},
        'paired_statistical_units':1,'new_holdout':False,'real_person_fidelity_verified':False,'external_model_calls_by_replay':0,
        'interpretation':'One consumed published single-domain authored pair with explicitly instructed missing-condition handling. Historical planned0 and state preservation unmeasured. Primary frozen target is unchanged; completion analysis is posthoc and cannot reveal hidden reasoning, establish population/real-person/cross-provider fidelity, or causally compare D28.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True);p.add_argument('--tokenizer');a=p.parse_args();model=None
    try:
        count=None
        if a.tokenizer:
            import llama_cpp
            model=llama_cpp.Llama(model_path=a.tokenizer,vocab_only=True,n_gpu_layers=0,verbose=False)
            count=lambda text:len(model.tokenize(text.encode(),add_bos=False,special=False))
        print(json.dumps(replay(a.base,count),ensure_ascii=False))
    finally:
        if model is not None:model.close()
