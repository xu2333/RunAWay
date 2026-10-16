"""Bounded development/held-out experiment for condition/action memory candidates."""
import argparse
import json
from pathlib import Path
import time
from .card import canonical,digest
from .decision_memory import SCHEMA,make_request,validate,semantic_audit
from .generation import codex_generate
from .pipeline import write_once
from .selfplay import Calls,PREDICTION_SCHEMA,prediction_request,validate_predictions,read,ROOT,SYSTEM

MODEL='gpt-6-luna'

def hashes():
    return {p:digest((ROOT/p).read_text()) for p in ['runaway/decision_memory.py','runaway/decision_experiment.py','runaway/generation.py','runaway/selfplay.py','runaway/execution_ledger.py']}


def development(out,audited=False):
    path=Path(out);path.mkdir(parents=True,exist_ok=False)
    inputs={}
    for pid in ['p02','p05']:
        d=read(ROOT/f'runs/selfplay-v1/amended/{pid}/learned.synthetic.json');inputs[pid]={'profile':d['profile'],'legacy':d['portable']['text']}
    snapshot=read(ROOT/'runs/selfplay-v1/amended/snapshot.synthetic.json')
    plan={'stage':'development','origin':'fully_synthetic','model':MODEL,'budget':1000,'inputs':inputs,'world':snapshot['world'],
          'audit':audited,'calls_limit':8 if audited else 6,'stopping':'One candidate per profile, paired legacy/new decoding, no silent repairs or transport retries.',
          'acceptance':'Measure behavior, failures and length on previously inspected development data; no held-out/generalization claim.',
          'code_hashes':hashes(),'created_at':time.time()}
    plan['id']=digest(canonical(plan));write_once(path/'plan.json',plan);return plan


class LimitedCalls(Calls):
    def __init__(self,out,limit,generate=codex_generate):
        self.limit=limit;self.backend_failed=False;self.attempts=0
        def limited(*a,**kw):
            used=list((Path(out)/'calls').glob('*.response.json'))+list((Path(out)/'calls').glob('*.failure.json'))
            if len(used)>=limit:raise ValueError('Frozen model call limit reached')
            if self.backend_failed:raise ValueError('Backend previously failed; no further network attempt')
            self.attempts+=1
            try:return generate(*a,**kw)
            except Exception:
                self.backend_failed=True
                raise
        super().__init__(Path(out),limited)

    def call(self,prompt,schema,model):
        key=digest(canonical({'prompt':prompt,'schema':schema,'model':model,'system':SYSTEM}))
        directory=self.out/'calls'
        if not any((directory/(key+suffix)).exists() for suffix in ('.response.json','.failure.json')):
            used={p.name.split('.')[0] for p in directory.glob('*.json') if p.name.endswith(('.attempt.json','.response.json','.failure.json'))}
            if len(used)>=self.limit:raise ValueError('Frozen model call limit reached, including unresolved attempts')
        return super().call(prompt,schema,model)


def run_development(out,generate=codex_generate):
    out=Path(out);plan=read(out/'plan.json')
    if plan['code_hashes']!=hashes():raise ValueError('Code changed after freeze')
    calls=LimitedCalls(out,plan['calls_limit'],generate);results={};cases=[c['public'] for c in plan['world']['test']]
    for pid,item in plan['inputs'].items():
        record={'legacy':item['legacy'],'decision':None,'candidate':None,'predictions':{},'failures':{}}
        try:
            candidate=calls.call(make_request(item['profile'],plan['budget']),SCHEMA,plan['model']);record['candidate']=candidate
            record['decision']=validate(candidate,item['profile'],plan['budget'])
            if plan.get('audit'):
                def reviewer(prompt,model,**kwargs):return json.dumps(calls.call(prompt,kwargs['schema'],model),ensure_ascii=False),{'backend':'cached_codex_call'}
                audit,metrics,provenance=semantic_audit(candidate,item['profile'],plan['budget'],reviewer,plan['model'])
                record['audit']={'audit':audit,'metrics':metrics}
                if not metrics['accepted']:record['decision']=None;raise ValueError('Semantic audit rejected candidate')
        except Exception as exc:record['failures']['compress']=str(exc)
        for condition in ['legacy','decision']:
            if record[condition] is None:continue
            try:
                value=calls.call(prediction_request(record[condition],cases),PREDICTION_SCHEMA,plan['model'])
                record['predictions'][condition]=validate_predictions(value,cases)
            except Exception as exc:record['failures'][condition]=str(exc)
        results[pid]=record;write_once(out/(pid+'.json'),record)
    from .selfplay_world import gold
    scores={}
    for condition in ['legacy','decision']:
        correct=total=available=0
        for p in plan['world']['personas']:
            if p['id'] not in results:continue
            values=results[p['id']]['predictions'].get(condition,{})
            for c in plan['world']['test']:
                if c['kind']!='heldout':continue
                total+=1;available+=c['public']['id'] in values;correct+=values.get(c['public']['id'])==gold(p['policy'],c)
        scores[condition]={'correct':correct,'planned':total,'available':available}
    report={'stage':'development','plan_id':plan['id'],'scores':scores,'failures':{p:r['failures'] for p,r in results.items()},'completed_calls':len(list((out/'calls').glob('*.response.json'))),'no_heldout_claim':True}
    write_once(out/'report.json',report);return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze-dev','run-dev']);p.add_argument('--out',required=True);p.add_argument('--audited',action='store_true');a=p.parse_args()
    print(json.dumps(development(a.out,a.audited) if a.command=='freeze-dev' else run_development(a.out),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
