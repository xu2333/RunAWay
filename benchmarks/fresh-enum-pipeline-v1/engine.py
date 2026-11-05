"""Finite injected45-slot fresh pipeline; contains no transport or human grant."""
import importlib.util
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fresh_pipeline_plan',HERE/'plan.py');plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
old=plan.load('fresh_pipeline_shared_io',plan.ROOT/'benchmarks/source-id-enum-repeat-v1/engine.py')
usage,write_new,score=old.usage,old.write_new,old.score
from runaway.constraint_extract import parse_answer,check

def summarize(rows,responses):
 profiles={};pooled={v:{k:Counter()for k in score.counts([], [{}])}for v in plan.VIEWS};transitions=[]
 for pid in plan.PROFILES:
  own=[r for r in rows if r['person']==pid];answers={v:[responses.get((pid,v,r),{})for r in(0,1)]for v in plan.VIEWS}
  profiles[pid]={v:score.counts(own,a)for v,a in answers.items()}
  for v,stats in profiles[pid].items():
   for k,c in stats.items():pooled[v][k].update(c)
  for row in own:
   endpoints={v:{'correct':all(a.get(q)==row['gold']for a in values for q in row['query_ids']),
    'missing':any(a.get(q)is None for a in values for q in row['query_ids'])}for v,values in answers.items()}
   transitions.append({'person':pid,'case':row['case'],'known':row['gold']!='U','derived_known':row['derived_known'],'cohort':row['cohort'],**endpoints})
 slices={}
 for label,condition in(('derived_known',lambda r:r['derived_known']),('withdrawal_unseen',lambda r:r['cohort']=='withdrawal_unseen'),('execution',lambda r:r['stratum']=='execution')):
  slices[label]={}
  for view in plan.VIEWS:
   total={k:Counter()for k in score.counts([], [{}])}
   for pid in plan.PROFILES:
    own=[r for r in rows if r['person']==pid and condition(r)]
    stats=score.counts(own,[responses.get((pid,view,repeat),{})for repeat in(0,1)])
    for metric,count in stats.items():total[metric].update(count)
   slices[label][view]={k:dict(count)for k,count in total.items()}
 return {'profiles':profiles,'views':{v:{k:dict(c)for k,c in stats.items()}for v,stats in pooled.items()},'transitions':transitions,
  'slices':slices,
  'planned_person_cases_per_view':64,'fictional_people':4,'answers_per_case_per_view':4,'independent_holdout':False,
  'initial_generation_stability_verified':False,'pipeline_not_enum_only_causal_ablation':True,'production_default_changed':False}

def run(root,destination,invoke,before,*,simulated):
 plan.verify(root);destination=Path(destination);destination.mkdir(exist_ok=False)
 data=plan.inputs();graphs={};responses={};records=[];controls={};none=None;invalid=[];skipped=[];stop=None
 for slot in plan.slots():
  pid=slot['profile'];kind=slot['kind'];stage='reviewed'if(kind=='review'or(slot['view']or'').startswith('reviewed'))else'draft'
  if kind in('extract','review','read')and not(len(controls)==4 and all(x['qualified']for x in controls.values())):stop='controls_not_qualified';break
  required=(pid,'draft')if kind=='review'else(pid,stage)if kind=='read'else None
  if required is not None and required not in graphs:skipped.append({**slot,'reason':'own_parent_product_invalid'});continue
  try:
   plan.verify(root);guard=before(slot)
   if not simulated and not guard.get('owned_active'):raise PermissionError('Owned temporary guard required')
   req=plan.request(slot,graphs)
   if req is None:raise ValueError('Missing planned material')
  except Exception as exc:stop='pre_call_failure:'+type(exc).__name__;break
  if len(records)>=plan.CAP:stop='attempt_cap';break
  folder=destination/('attempt-%02d'%slot['slot']);folder.mkdir();rec={**slot,'request_sha256':plan.digest(req),'state':'invocation_intent','usage':None,'simulated':simulated}
  write_new(folder/'request.json',req);write_new(folder/'intent.json',{**rec,'guard':guard});records.append(rec)
  try:
   raw,prov=invoke(req,folder,slot);write_new(folder/'raw-response.json',{'raw':raw,'provenance':prov});rec['raw_response_sha256']=plan.sha(folder/'raw-response.json');rec['usage']=usage(prov)
   if prov.get('model_requested')!=plan.MODEL or(not simulated and prov.get('backend')!='codex'):raise ValueError('Backend/model differs')
   if type(raw)is not str or len(raw.encode())>256000:raise ValueError('Raw type/size differs')
   answer=parse_answer(raw);check(answer,plan.reviewer.SCHEMA if kind=='review'else req['schema']);write_new(folder/'answer.json',answer)
   if kind in('extract','review'):
    if kind=='review':
     try:check(answer,req['schema']);rec['request_schema_conformant']=True
     except ValueError:rec['request_schema_conformant']=False
    try:
     prompt=plan.bind(pid,stage,answer)['prompt.md']
     if not 0<len(prompt)<=plan.BUDGET:raise ValueError('Budget differs')
    except(ValueError,KeyError,TypeError)as exc:rec['product_invalid']=True;invalid.append({**slot,'error_type':type(exc).__name__,'error':str(exc)})
    else:
     if kind=='review'and not rec['request_schema_conformant']:raise ValueError('Request enum differs from binding acceptance')
     artifact={'profile':pid,'stage':stage,'prompt':prompt,'characters':len(prompt),'answer_sha256':plan.digest(answer),'source_sha256':plan.digest(data['sources'][pid])}
     write_new(folder/'artifact.json',artifact);rec['artifact_sha256']=plan.sha(folder/'artifact.json');graphs[pid,stage]=answer
   else:
    plan.choice_reader.decode_response(data['queries']['all'],answer,answer_format='text',reader_mode='standard')
    if kind=='none':none=answer
    elif kind=='full':
     own=[r for r in data['rows']if r['person']==pid];f,n=score.counts(own,[answer]),score.counts(own,[none])
     controls[pid]={'qualified':f['joint']['correct']==16 and not f['joint']['missing']and f['personal_known']['correct']>n['personal_known']['correct'],'full':f,'none':n}
     write_new(folder/'control-gate.json',controls[pid])
     if not controls[pid]['qualified']:stop='full_control_not_qualified'
    else:responses[pid,slot['view'],slot['read_repeat']]=answer
   rec['state']='completed'
  except Exception as exc:
   rec.update(state='failed',error_type=type(exc).__name__,error=str(exc));stop='transport_wire_decode_usage_or_model_failure'
   prov=getattr(exc,'provenance',None)
   if prov:
    write_new(folder/'failure-provenance.json',prov)
    try:rec['usage']=usage(prov)
    except ValueError:pass
  write_new(folder/'result.json',rec)
  if stop:break
 total=Counter()
 for rec in records:
  if rec['usage']is not None:total.update(rec['usage'])
 state={'status':'stopped'if stop else'complete','stop':stop,'records':records,'control_gate':controls,'invalid_products':invalid,'skipped':skipped,
  'attempt_reservations':len(records),'local_cli_child_intents':len(list(destination.glob('attempt-*/backend-child-intent.json'))),
  'known_usage':dict(total),'missing_usage':sum(r['usage']is None for r in records),'unused_slots_expire':plan.CAP-len(records),
  'scope_closed':True,'simulated':simulated,'new_service_authority':False,'scores':summarize(data['rows'],responses),
  'old_scopes_reopened':False,'production_default_changed':False}
 write_new(destination/'result.json',state);return state
