"""Offline, oracle-scored compression-metric calibration and isolated job export.

Reference adapters are protocol fixtures, not measured product/LLM compressors.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import random
from pathlib import Path
import time

from .card import canonical,digest
from .pipeline import write_once
from .synthetic_metric_world import build_world,parse_history,render_event,resolve

ROOT=Path(__file__).resolve().parents[1]
CODE=('runaway/synthetic_metric.py','runaway/synthetic_metric_world.py','runaway/card.py','runaway/text_integrity.py')
CRITICAL=('hard_constraints','conditions','exceptions','updates','revocations','distinctions','strength')
CONDITIONS=('none','full_history','current_reference_naive','new_reference_codec','random_delete','shuffled_person','delete_exception','delete_hard','stale_updates','timeout')
PROTOCOL=('This is an explicit synthetic event protocol, not an inference about real people. '
          'Use events dated at or before the query date, irrespective of line order. A revoke removes its target; revoking a revoke restores its target effect. '
          'A clear removes earlier records for that key. Latest active facts win. For preferences, strongest active evidence wins, then latest on ties. '
          'An explicit replace resets earlier preferences; a later weak preference alone does not. Matching hard constraints override conditional exceptions; matching exceptions override base preferences. '
          'Unknown keys return U. Return the ID from answer_options, not a paraphrase. No seed, evaluation answers or personal hidden policy is part of this public protocol.')


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def freeze(out,seed=71317,pairs=4,budgets=(0,64,128,192,256,384,512,768,1024),gguf=None):
    if not budgets or sorted(set(budgets))!=list(budgets) or any(type(b) is not int or b<0 for b in budgets):raise ValueError('Budgets must be unique increasing nonnegative integers')
    root=Path(out);root.mkdir(parents=True,exist_ok=False)
    world=build_world(seed,pairs)
    tokenizer={'kind':'existing_local_gguf_tokenizer','model_sha256':file_hash(gguf)} if gguf else {'kind':'utf8_byte_units'}
    body={'schema_version':1,'stage':'metric_calibration_not_product_ranking','origin':'fully_synthetic','world_id':world['id'],'budgets':list(budgets),'tokenizer':tokenizer,
          'conditions':list(CONDITIONS),'code_hashes':{p:digest((ROOT/p).read_text()) for p in CODE},
          'external_model_call_limit':0,'quality_contract':'All predeclared queries, failure-inclusive. Strata and matched-person distinctions separate; token/cost not combined into one utility ratio.',
          'adapter_contract':'Protocol reference adapters parse visible history only; deliberately not claims about RunAWay old/new LLM compression quality.'}
    plan={**body,'id':digest(canonical(body))};write_once(root/'snapshot.json',plan);write_once(root/'world.private.json',world)
    write_once(root/'protocol.public.json',{'protocol':PROTOCOL})
    write_once(root/'histories.public.json',{'people':[{'id':p['id'],'history':p['history']} for p in world['people']]})
    jobs=[{'persona_id':p['id'],'history':p['history'],'budget_tokens':b,'instruction':PROTOCOL+' Compress only this history, preserving dates, conditions, hard limits, exceptions, strengths, updates and revoked choices. Unknowns remain unknown.'} for p in world['people'] for b in budgets if b]
    write_once(root/'compressor-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs))
    for p in CODE:
        target=root/'frozen-source'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/p).read_bytes())
    return plan


def byte_count(text):return len(text.encode('utf-8'))


def frozen_data(root):
    root=Path(root);plan=json.loads((root/'snapshot.json').read_text());world=json.loads((root/'world.private.json').read_text())
    if plan['id']!=digest(canonical({k:v for k,v in plan.items() if k!='id'})):raise ValueError('Frozen plan changed')
    if plan['code_hashes']!={p:digest((ROOT/p).read_text()) for p in CODE}:raise ValueError('Frozen metric implementation changed')
    if world['id']!=digest(canonical({k:v for k,v in world.items() if k!='id'})) or world['id']!=plan['world_id']:raise ValueError('World changed')
    return plan,world


def pack(lines,budget,count):
    result=[]
    for line in lines:
        if count('\n'.join(result+[line]))<=budget:result.append(line)
    return '\n'.join(result)


def memory_for(history,condition,budget,count):
    if condition=='none':return ''
    if condition=='full_history':return history
    if condition=='timeout':return None
    events=parse_history(history)
    if condition=='current_reference_naive':
        latest={}
        for event in events:
            if event.get('key'):latest[event['key']]=event
        events=list(latest.values())
    elif condition=='new_reference_codec':
        priority={'hard':0,'except':1,'revoke':2,'replace':3,'clear':4,'prefer':5,'fact':6}
        events=sorted(events,key=lambda e:(priority[e['op']],e['day']))
    elif condition=='random_delete':
        rng=random.Random(int(digest(history)[:16],16));events=rng.sample(events,len(events)//2)
    elif condition=='delete_exception':events=[e for e in events if e['op']!='except']
    elif condition=='delete_hard':events=[e for e in events if e['op']!='hard']
    elif condition=='stale_updates':events=[e for e in events if e['day']<8]
    elif condition!='shuffled_person':raise ValueError('Unknown condition')
    return pack([render_event(e,compact=True) for e in events],budget,count)


def decode_reference(memory,public_queries):
    if memory is None:return {}
    parsed=parse_history(memory)
    return {q['id']:resolve(parsed,q)[0] for q in public_queries}


def score(people,predictions):
    strata=defaultdict(lambda:Counter(planned=0,correct=0,available=0,abstentions=0,missing=0))
    per_person=[];hard=Counter(planned=0,incorrect=0,observed_violations=0,abstentions=0,missing=0)
    for person in people:
        correct=available=0
        for case in person['queries']:
            value=predictions.get(person['id'],{}).get(case['public']['id'])
            value='U' if value=='unknown' else value
            allowed=case['allowed_answers'];valid=isinstance(value,str);right=valid and value in allowed
            row=strata[case['stratum']];row['planned']+=1;row['correct']+=right;row['available']+=valid;row['missing']+=not valid;row['abstentions']+=value=='U'
            correct+=right;available+=valid
            if case['stratum']=='hard_constraints':
                hard['planned']+=1;hard['incorrect']+=not right;hard['missing']+=not valid;hard['abstentions']+=value=='U';hard['observed_violations']+=valid and value!='U' and not right
        per_person.append({'id':person['id'],'correct':correct,'planned':len(person['queries']),'available':available})
    by_id={p['id']:p for p in people};twins=Counter(planned=0,correct=0,missing=0)
    for person in people:
        twin=by_id.get(person['twin'])
        if twin is None or person['id']>=twin['id']:continue
        other={q['comparison_key']:q for q in twin['queries']}
        for case in person['queries']:
            mate=other[case['comparison_key']]
            if case['allowed_answers']==mate['allowed_answers']:continue
            a=predictions.get(person['id'],{}).get(case['public']['id']);b=predictions.get(twin['id'],{}).get(mate['public']['id'])
            twins['planned']+=1;twins['missing']+=a is None or b is None;twins['correct']+=a in case['allowed_answers'] and b in mate['allowed_answers']
    planned=sum(p['planned'] for p in per_person);correct=sum(p['correct'] for p in per_person);available=sum(p['available'] for p in per_person)
    layers={k:{**dict(v),'accuracy':v['correct']/v['planned'] if v['planned'] else None} for k,v in sorted(strata.items())}
    critical=[layers[k]['accuracy'] for k in CRITICAL if k in layers]
    return {'correct':correct,'planned':planned,'available':available,'missing':planned-available,'accuracy':correct/planned if planned else None,
            'strata':layers,'worst_critical_accuracy':min(critical) if critical else None,'hard_constraints':dict(hard),'matched_person_disagreements':dict(twins),'per_person':per_person}


def normalized_retention(value,none,history,epsilon=1e-9):
    denominator=history-none
    return (value-none)/denominator if denominator>epsilon else None


def evaluate(root,count=byte_count,tokenizer_metadata=None):
    root=Path(root);plan,world=frozen_data(root)
    metadata=tokenizer_metadata or {'kind':'utf8_byte_units','unit':'UTF8bytes','llm_token_counts':False}
    if any(metadata.get(k)!=v for k,v in plan['tokenizer'].items()):raise ValueError('Tokenizer changed after freeze')
    if (root/'report.json').exists():
        saved=json.loads((root/'report.json').read_text())
        if saved.get('plan_id')!=plan['id'] or saved.get('sha256')!=digest(canonical({k:v for k,v in saved.items() if k!='sha256'})):raise ValueError('Saved report changed')
        for name,expected in saved['artifacts'].items():
            if digest(canonical(json.loads((root/name).read_text())))!=expected:raise ValueError('Saved metric artifact changed')
        return saved
    rows=[];memory_rows=[];prediction_rows=[];decoder_jobs=[];t0=time.perf_counter()
    for split in ('dev','eval'):
        people=[p for p in world['people'] if p['split']==split];lookup={p['id']:p for p in people}
        for budget in plan['budgets']:
            for condition in CONDITIONS:
                predictions={};costs=[];failures=[]
                for p in people:
                    source=lookup[p['twin']]['history'] if condition=='shuffled_person' else p['history']
                    memory=memory_for(source,condition,budget,count)
                    predictions[p['id']]=decode_reference(memory,[q['public'] for q in p['queries']])
                    prediction_rows.append({'persona_id':p['id'],'split':split,'condition':condition,'budget':budget,'answers':predictions[p['id']]})
                    if memory is None:failures.append({'persona':p['id'],'stage':'simulated_timeout','scope':'deliberate missing-output control; no external call'})
                    else:costs.append(count(memory))
                    memory_rows.append({'persona_id':p['id'],'split':split,'condition':condition,'budget':budget,'memory':memory,'units':count(memory) if memory is not None else None})
                    if condition in ('current_reference_naive','new_reference_codec'):
                        decoder_jobs.append({'persona_id':p['id'],'condition':condition,'budget':budget,'instruction':PROTOCOL,'memory':memory,'queries':[q['public'] for q in p['queries']]})
                quality=score(people,predictions)
                rows.append({'split':split,'condition':condition,'budget':budget,'quality':quality,'mean_memory_units':sum(costs)/len(costs) if costs else None,
                             'memory_people':len(costs),'planned_people':len(people),'budget_applies':condition!='full_history','failures':failures})
    for row in rows:
        group=[r for r in rows if r['split']==row['split'] and r['budget']==row['budget']]
        baseline=next(r for r in group if r['condition']=='none');full=next(r for r in group if r['condition']=='full_history')
        q=row['quality'];q['degradation_vs_history']=full['quality']['accuracy']-q['accuracy'];q['normalized_retention']=normalized_retention(q['accuracy'],baseline['quality']['accuracy'],full['quality']['accuracy'])
        row['memory_ratio_to_full']=row['mean_memory_units']/full['mean_memory_units'] if row['mean_memory_units'] is not None and full['mean_memory_units'] else None
    checks=discrimination_checks(rows)
    report={'schema_version':1,'origin':'fully_synthetic','stage':'offline_metric_calibration','plan_id':plan['id'],'world_id':world['id'],'tokenizer':metadata,
            'budgets':plan['budgets'],'rows':rows,'discrimination_checks':checks,'passed':all(checks.values()),
            'adapters':{'current_reference_naive':'Protocol last-record-per-key baseline, not actual RunAWay compressor performance.','new_reference_codec':'Protocol event-preserving reference codec, not a measured LLM compressor.'},
            'external_model_calls':0,'product_compression_comparison_measured':False,'real_person_fidelity_verified':False,
            'limitations':['Shared finite event grammar and protocol reader; this calibrates scorer sensitivity, not model generalization.','Dev/eval parameter combinations and history templates are disjoint, but share the event ontology.','Published fixtures are development data for future model comparisons.','No single quality/token ratio; missing output stays in all planned denominators.']}
    report['artifacts']={'memories.json':digest(canonical(memory_rows)),'predictions.json':digest(canonical(prediction_rows))}
    report['sha256']=digest(canonical(report))
    write_once(root/'report.json',report);write_once(root/'memories.json',memory_rows);write_once(root/'predictions.json',prediction_rows)
    write_once(root/'decoder-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in decoder_jobs))
    write_once(root/'costs.json',{'external_model_calls':0,'external_model_usage':[],'reference_calibration_seconds':time.perf_counter()-t0,'tokenization_only_no_model_inference':True,'unit':metadata['unit'],'note':'Memory length is separate from generation/use/experiment service costs. No missing service cost is estimated here.'})
    return report


def discrimination_checks(rows):
    budget=max(r['budget'] for r in rows);lookup={r['condition']:r for r in rows if r['split']=='eval' and r['budget']==budget}
    def accuracy(condition,stratum):return lookup[condition]['quality']['strata'][stratum]['accuracy']
    full=lookup['full_history']['quality']
    return {'history_measured_above_no_memory':full['accuracy']>lookup['none']['quality']['accuracy'],
            'exception_deletion_detected':accuracy('delete_exception','exceptions')<accuracy('full_history','exceptions'),
            'hard_constraint_deletion_detected':lookup['delete_hard']['quality']['hard_constraints']['observed_violations']>0,
            'stale_updates_detected':accuracy('stale_updates','updates')<accuracy('full_history','updates'),
            'revocation_loss_detected':accuracy('current_reference_naive','revocations')<accuracy('full_history','revocations'),
            'shuffled_person_disagreements_detected':lookup['shuffled_person']['quality']['matched_person_disagreements']['correct']<full['matched_person_disagreements']['correct'],
            'random_deletion_detected':lookup['random_delete']['quality']['accuracy']<full['accuracy'],
            'missing_output_not_abstention_credit':lookup['timeout']['quality']['correct']==0 and lookup['timeout']['quality']['missing']==lookup['timeout']['quality']['planned']}


def score_external(root,predictions,split='eval'):
    _,world=frozen_data(root);people=[p for p in world['people'] if p['split']==split]
    known={p['id']:{q['public']['id']:q for q in p['queries']} for p in people};failures=[];valid={}
    if not isinstance(predictions,dict) or any(pid not in known for pid in predictions):failures.append({'scope':'all','reason':'Unknown persona or invalid payload shape'})
    else:
        for pid,values in predictions.items():
            if not isinstance(values,dict) or any(qid not in known[pid] or not isinstance(value,str) or ('U' if value=='unknown' else value) not in known[pid][qid]['public']['answer_options'] for qid,value in values.items()):
                failures.append({'persona':pid,'reason':'Unknown query or invalid categorical answer; this persona output is rejected'})
            else:valid[pid]=values
    result=score(people,valid);result['validation_failures']=failures;result['split']=split;return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--out',required=True);f.add_argument('--seed',type=int,default=71317);f.add_argument('--pairs',type=int,default=4);f.add_argument('--gguf')
    e=sub.add_parser('calibrate');e.add_argument('--run',required=True);e.add_argument('--gguf',help='Existing local tokenizer only; never runs inference')
    s=sub.add_parser('score');s.add_argument('--run',required=True);s.add_argument('--predictions',required=True);s.add_argument('--out',required=True)
    a=p.parse_args()
    if a.command=='freeze':result=freeze(a.out,a.seed,a.pairs,gguf=a.gguf)
    elif a.command=='score':
        result=score_external(a.run,json.loads(Path(a.predictions).read_text()));write_once(Path(a.out),result)
    elif a.gguf:
        import llama_cpp
        model=llama_cpp.Llama(model_path=a.gguf,vocab_only=True,n_gpu_layers=0,verbose=False)
        try:
            result=evaluate(a.run,lambda text:len(model.tokenize(text.encode('utf-8'),add_bos=False,special=False)),{'kind':'existing_local_gguf_tokenizer','unit':'model tokens','llm_token_counts':True,'model_sha256':file_hash(a.gguf),'model_name':model.metadata.get('general.name'),'inference':False})
        finally:model.close()
    else:result=evaluate(a.run)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','code_hashes')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
