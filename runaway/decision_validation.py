"""Pre-frozen paired validation. Newly synthesized histories only, with a finite call cap."""
import argparse
import json
from pathlib import Path
import statistics
import time
from .card import canonical,digest
from .decision_experiment import LimitedCalls,MODEL
from .decision_memory import SCHEMA,make_request,validate,semantic_audit
from .decision_world import build_world,gold
from .pipeline import write_once
from .portable import make_expression
from .profile import export_profile
from .selfplay import ROOT,read,browser,BROWSER_SCHEMA,PREDICTION_SCHEMA,prediction_request,validate_predictions,GENERIC
from .selfplay_world import synthetic_sources,oracle_memory

CONDITIONS=('none','detailed','legacy','compact','oracle')
CODE=('runaway/decision_memory.py','runaway/decision_world.py','runaway/decision_validation.py',
      'runaway/decision_experiment.py','runaway/generation.py','web/dist/core.mjs','scripts/selfplay-browser.mjs')

def code_hashes():return {p:digest((ROOT/p).read_text()) for p in CODE}

def freeze(out):
 root=Path(out);root.mkdir(parents=True,exist_ok=False)
 body={'schema_version':1,'benchmark_version':3,'origin':'fully_synthetic','stage':'pre_frozen_holdout','created_at':time.time(),
       'world':build_world(),'model':MODEL,'decoder_model':MODEL,'conditions':list(CONDITIONS),'budget':1000,'candidate_budget_policy':'max(200, min(1000, floor(1.25 * legacy_characters)))','semantic_audit_policy':'diagnostic_only; all partial/missing facets remain reported, not a full-profile preservation certificate',
       'calls_limit':31,'development_calls_limit':14,'combined_limit':45,'code_hashes':code_hashes(),
       'decoder_gate':{'oracle_accuracy_min':.85,'oracle_order_consistency_min':.75,'oracle_constraint_violations_max':0,'reject_constant_oracle':True},
       'stopping':'Stop inference after a transport failure, frozen call limit, or failed decoder gate. At most one validation-only extraction repair across all four people before heldout decoding. One semantic audit per candidate, reported as a fallible diagnostic; structural failures produce no portable candidate. No candidate repair from heldout outcomes. No score-based repair.',
       'comparison':'Same newly extracted profile, same decoder and questions: original browser prompt vs condition/action candidate. All four people remain in denominators.',
       'quality_target':{'constraint_violations_not_greater_than_legacy':True,'key_twin_disagreements_improve':True,'accuracy_loss_max_cases':1,'token_ratio_to_legacy_max':1.25},
       'boundaries':['Prior six personas/cases are development data only.','Four new combinations and new wording/settings, same authored rule families.','No hidden policy or evaluation case enters extraction/compression.','All measurements become development data after inspection.','No real-person or cross-vendor generalization claim.']}
 plan={**body,'id':digest(canonical(body))};write_once(root/'snapshot.synthetic.json',plan)
 for name in CODE:
  p=root/'frozen-source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
 return plan


def predict(calls,memory,cases,model):
 return validate_predictions(calls.call(prediction_request(memory,cases),PREDICTION_SCHEMA,model),cases)


def normalize(v):return 'U' if v=='unknown' else v


def score(world,predictions,condition):
 primary=[c for c in world['test'] if c['kind']=='heldout'];rows=[]
 for p in world['personas']:
  values=predictions.get(p['id'],{}).get(condition,{})
  correct=sum(normalize(values.get(c['public']['id']))==gold(p['policy'],c) for c in primary)
  swaps=[c for c in world['test'] if c['kind']=='order_swap'];lookup={c['public']['id']:c for c in world['test']}
  order=[]
  for c in swaps:
   a=normalize(values.get(c['public']['id']));b=normalize(values.get(c['original_id']))
   order.append(a in ('A','B') and b in ('A','B') and c['actions'][a]==lookup[c['original_id']]['actions'][b])
  constraints=[c for c in world['test'] if c['kind']=='explicit_request'];cv=[normalize(values.get(c['public']['id']))!=gold(p['policy'],c) for c in constraints]
  unknown=[c for c in world['test'] if c['kind']=='unobserved']
  rows.append({'persona':p['id'],'correct':correct,'planned':len(primary),'available':sum(c['public']['id'] in values for c in primary),'constraint_violations':sum(cv),'constraint_cases':len(cv),'order_consistency':statistics.mean(order),'unknown_abstention':statistics.mean(normalize(values.get(c['public']['id']))=='U' for c in unknown),'constant_answer':len(set(values.values()))==1 if values else None})
 twins=[]
 for i in range(0,len(world['personas']),2):
  a,b=world['personas'][i:i+2]
  for c in primary:
   ga,gb=gold(a['policy'],c),gold(b['policy'],c)
   if ga==gb:continue
   cid=c['public']['id'];twins.append(normalize(predictions.get(a['id'],{}).get(condition,{}).get(cid))==ga and normalize(predictions.get(b['id'],{}).get(condition,{}).get(cid))==gb)
 return {'correct':sum(r['correct'] for r in rows),'planned':sum(r['planned'] for r in rows),'available':sum(r['available'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/sum(r['planned'] for r in rows),'constraint_violations':sum(r['constraint_violations'] for r in rows),'constraint_cases':sum(r['constraint_cases'] for r in rows),'order_consistency':statistics.mean(r['order_consistency'] for r in rows),'unknown_abstention':statistics.mean(r['unknown_abstention'] for r in rows),'twins_correct':sum(twins),'twins_cases':len(twins),'per_persona':rows}


def run(out,generate=None):
 root=Path(out);plan=read(root/'snapshot.synthetic.json')
 if plan['id']!=digest(canonical({k:v for k,v in plan.items() if k!='id'})) or plan['code_hashes']!=code_hashes():raise ValueError('Frozen plan/code changed')
 kwargs={} if generate is None else {'generate':generate}
 calls=LimitedCalls(root,plan['calls_limit'],**kwargs);world=plan['world'];cases=[c['public'] for c in world['test']]
 predictions={p['id']:{} for p in world['personas']};learned={};failures={};gate=None;extraction_repairs=0
 try:
  # Oracle is a separate diagnostic. It is never fed to an extractor/compressor.
  for p in world['personas']:
   print(p['id']+': oracle control',flush=True);predictions[p['id']]['oracle']=predict(calls,oracle_memory(p['policy']),cases,plan['decoder_model'])
  gate=score(world,predictions,'oracle');g=plan['decoder_gate']
  gate['passed']=gate['accuracy']>=g['oracle_accuracy_min'] and gate['order_consistency']>=g['oracle_order_consistency_min'] and gate['constraint_violations']<=g['oracle_constraint_violations_max'] and not any(r['constant_answer'] for r in gate['per_persona'])
  write_once(root/'decoder-gate.json',gate)
  if not gate['passed']:raise ValueError('Decoder control gate failed; no profile comparison run')
  print('shared training assistant proposals',flush=True)
  proposals=predict(calls,'',[c['public'] for c in world['training']],plan['model'])
  for p in world['personas']:
   pid=p['id'];directory=root/pid;directory.mkdir(exist_ok=True);sources=synthetic_sources(world,p,{0:proposals});write_once(directory/'trajectory.synthetic.json',sources)
   prompt=browser('request',sources,plan['budget'])['request'];first_error=None;answer=None
   for attempt in range(2):
    print(pid+': extract '+str(attempt),flush=True)
    value=calls.call(prompt,BROWSER_SCHEMA,plan['model'])
    try:bundle=browser('validate',sources,plan['budget'],value);answer=value;break
    except ValueError as exc:
     first_error=str(exc);write_once(directory/f'extraction-{attempt}.failure.json',{'error':str(exc),'answer':value})
     if attempt==0 and extraction_repairs<1:
      extraction_repairs+=1;prompt=prompt+'\nYour previous result failed STRUCTURAL validation. Repair only the returned result against the same sources. Do not add preferences.\nERROR: '+str(exc)+'\nPREVIOUS_JSON:\n'+json.dumps(value,ensure_ascii=False)
     else:break
   if answer is None:failures[pid+'/extract']=first_error;continue
   detailed,_=export_profile(bundle['profile']);record={'sources':sources,'answer':answer,'profile':bundle['profile'],'legacy_portable':bundle['portable'],'portable':None,'detailed':detailed,'decision':None,'first_pass_error':first_error,'tiny':None,'tiny_error':'Not run in this experiment.'}
   try:
    candidate_budget=max(200,min(plan['budget'],int(len(bundle['portable']['text'])*1.25)));record['candidate_budget']=candidate_budget
    print(pid+': condition/action candidate',flush=True);candidate=calls.call(make_request(bundle['profile'],candidate_budget),SCHEMA,plan['model']);text=validate(candidate,bundle['profile'],candidate_budget);record['decision']=candidate
    def reviewer(prompt,model,**kwargs):return json.dumps(calls.call(prompt,kwargs['schema'],model),ensure_ascii=False),{'backend':'cached_codex_call'}
    audit,metrics,_=semantic_audit(candidate,bundle['profile'],candidate_budget,reviewer,plan['model']);record['audit']={'audit':audit,'metrics':metrics}
    if not metrics['accepted']:record['audit_warning']='Model audit reported losses; retained as an explicitly unverified behavioral candidate, not a certified compact profile.'
    record['portable']=make_expression(text,bundle['profile']['id'],'condition_action_behavioral_candidate_v2')
   except Exception as exc:failures[pid+'/compress']=str(exc)
   learned[pid]=record;write_once(directory/'learned.synthetic.json',record)
  memories={}
  for p in world['personas']:
   pid=p['id'];item=learned.get(pid);twin=learned.get(p['twin']);source=root/pid/'trajectory.synthetic.json'
   memories[pid]={'none':'','generic':GENERIC,'trajectory':canonical(read(source)) if source.exists() else None,
    'detailed':item['detailed'] if item else None,'legacy':item['legacy_portable']['text'] if item else None,'compact':item['portable']['text'] if item and item['portable'] else None,
    'wrong_person':twin['portable']['text'] if twin and twin['portable'] else None,'oracle':oracle_memory(p['policy'])}
  write_once(root/'memories.synthetic.json',memories)
  for p in world['personas']:
   for condition,memory in memories[p['id']].items():
    if condition not in CONDITIONS or condition=='oracle' or memory is None:continue
    print(p['id']+': predict '+condition,flush=True);predictions[p['id']][condition]=predict(calls,memory,cases,plan['decoder_model'])
 except Exception as exc:
  failures['stopped']=str(exc)
 write_once(root/'predictions.synthetic.json',predictions)
 report={'schema_version':1,'snapshot_id':plan['id'],'origin':'fully_synthetic','stage':'pre_frozen_holdout_evaluated','conditions':{c:score(world,predictions,c) for c in CONDITIONS},'decoder_gate':gate,'failures':failures,'first_pass_profiles':sum(r['first_pass_error'] is None for r in learned.values()),'final_profiles':len(learned),'planned_profiles':len(world['personas']),'generator_model':plan['model'],'decoder_model':plan['decoder_model'],'completed_model_calls':len(list((root/'calls').glob('*.response.json'))),'calls_limit':plan['calls_limit'],'behavioral_fidelity_verified_for_real_people':False,'interpretation':'Paired new-person comparison; authored family only. Results are development data after inspection.'}
 write_once(root/'report.synthetic.json',report);return report


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['freeze','run']);p.add_argument('--out',required=True);a=p.parse_args()
 result=freeze(a.out) if a.command=='freeze' else run(a.out)
 print(json.dumps({k:v for k,v in result.items() if k not in ('world','code_hashes')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
