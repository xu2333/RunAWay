"""Bind actual compressor outputs to isolated decoder jobs, then score all trials.

This tool makes no external calls. Missing/invalid/over-budget memories stay in
the predeclared cohort, but are never sent to a decoder as usable memories.
"""
import argparse
import json
from pathlib import Path
from .card import canonical,digest,string
from .pipeline import write_once
from .synthetic_metric import frozen_data,PROTOCOL,byte_count,file_hash,score_external


def prepare(run,outputs,out,conditions,budgets,count=byte_count,tokenizer=None,split='eval'):
    plan,world=frozen_data(run);expected=tokenizer or {'kind':'utf8_byte_units'}
    if expected!=plan['tokenizer']:raise ValueError('Actual-memory tokenizer must match frozen tokenizer')
    if not conditions or len(set(conditions))!=len(conditions) or not budgets or len(set(budgets))!=len(budgets) or any(type(b) is not int or b not in plan['budgets'] for b in budgets):raise ValueError('Predeclare unique conditions and frozen budgets')
    people=[p for p in world['people'] if p['split']==split];ids={p['id'] for p in people};indexed={}
    for row in outputs:
        key=(row['persona_id'],row['condition'],row['budget'])
        if key in indexed or key[0] not in ids or key[1] not in conditions or key[2] not in budgets:raise ValueError('Duplicate or out-of-scope compressor output')
        indexed[key]=row
    trials=[];jobs=[]
    for condition in conditions:
        for budget in budgets:
            for person in people:
                row=indexed.get((person['id'],condition,budget));memory=row.get('memory') if row else None;failure=None;units=None
                try:
                    if memory is None:raise ValueError('Missing or failed compressor output')
                    if memory!='':string(memory,'memory',128000)
                    units=count(memory)
                    if condition!='full_history' and units>budget:raise ValueError('Compressor output exceeds frozen token budget; no truncation')
                except ValueError as exc:failure=str(exc)
                memory_hash=digest(json.dumps(memory,ensure_ascii=True)) if isinstance(memory,str) else None
                identity=digest(canonical({'persona':person['id'],'condition':condition,'budget':budget,'memory_value_sha256':memory_hash}))
                trial={'trial_id':identity,'persona_id':person['id'],'condition':condition,'budget':budget,'units':units,'memory_value_sha256':memory_hash,'budget_applies':condition!='full_history','failure':failure}
                trials.append(trial)
                if failure is None:jobs.append({'trial_id':identity,'persona_id':person['id'],'condition':condition,'budget':budget,'instruction':PROTOCOL,'memory':memory,'queries':[q['public'] for q in person['queries']]})
    dest=Path(out);dest.mkdir(parents=True,exist_ok=False)
    manifest={'schema_version':1,'plan_id':plan['id'],'job_adapter_sha256':digest(Path(__file__).read_text()),'split':split,'conditions':conditions,'budgets':budgets,'planned_people':len(people),'trials':trials}
    manifest['sha256']=digest(canonical(manifest));write_once(dest/'trials.private.json',manifest)
    write_once(dest/'decoder-jobs.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs));return manifest


def score_trials(run,trials_path,answers):
    plan,_=frozen_data(run);manifest=json.loads(Path(trials_path).read_text())
    if manifest['plan_id']!=plan['id'] or manifest['job_adapter_sha256']!=digest(Path(__file__).read_text()) or manifest['sha256']!=digest(canonical({k:v for k,v in manifest.items() if k!='sha256'})):raise ValueError('Trial manifest changed')
    batch_failures=[]
    if not isinstance(answers,dict) or any(key not in {t['trial_id'] for t in manifest['trials']} for key in answers):
        batch_failures.append('Unknown trial or invalid batch; all model answers rejected');answers={}
    rows=[]
    for condition in manifest['conditions']:
        for budget in manifest['budgets']:
            group=[t for t in manifest['trials'] if t['condition']==condition and t['budget']==budget]
            predictions={t['persona_id']:answers[t['trial_id']] for t in group if t['failure'] is None and t['trial_id'] in answers}
            quality=score_external(run,predictions,manifest['split']);sizes=[t['units'] for t in group if t['failure'] is None]
            rows.append({'condition':condition,'budget':budget,'quality':quality,'planned_people':len(group),'usable_memories':len(sizes),
                         'mean_memory_units':sum(sizes)/len(sizes) if sizes else None,'compressor_failures':[t for t in group if t['failure'] is not None]})
    return {'schema_version':1,'plan_id':plan['id'],'split':manifest['split'],'tokenizer':plan['tokenizer'],'rows':rows,'batch_validation_failures':batch_failures,'model_calls_by_this_tool':0,
            'cost_note':'Actual generation/decoder service usage belongs to their executor ledger; this tool does not invent it.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--run',required=True);a.add_argument('--memories',required=True);a.add_argument('--out',required=True);a.add_argument('--conditions',required=True);a.add_argument('--budgets',required=True);a.add_argument('--gguf')
    s=sub.add_parser('score');s.add_argument('--run',required=True);s.add_argument('--trials',required=True);s.add_argument('--answers',required=True);s.add_argument('--out',required=True)
    args=p.parse_args()
    if args.command=='score':result=score_trials(args.run,args.trials,json.loads(Path(args.answers).read_text()));write_once(Path(args.out),result)
    else:
        outputs=json.loads(Path(args.memories).read_text());conditions=args.conditions.split(',');budgets=[int(v) for v in args.budgets.split(',')]
        if args.gguf:
            import llama_cpp
            model=llama_cpp.Llama(model_path=args.gguf,vocab_only=True,n_gpu_layers=0,verbose=False)
            try:result=prepare(args.run,outputs,args.out,conditions,budgets,lambda text:len(model.tokenize(text.encode(),add_bos=False,special=False)),{'kind':'existing_local_gguf_tokenizer','model_sha256':file_hash(args.gguf)})
            finally:model.close()
        else:result=prepare(args.run,outputs,args.out,conditions,budgets)
    print(json.dumps({k:v for k,v in result.items() if k!='trials'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
