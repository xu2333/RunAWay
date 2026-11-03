"""Nine fixed read slots with injected transport and no built-in service authority."""
import importlib.util,json
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixed_coverage9_plan',HERE/'plan.py')
plan=importlib.util.module_from_spec(spec);spec.loader.exec_module(plan)
p=plan.base.base
e=plan.load('fixed_coverage9_counts',plan.ROOT/'benchmarks/epistemic-transfer-v1/engine.py')
read,digest,sha=plan.read,plan.digest,plan.sha
write_new=e.base.write_new

def summarize(root,responses):
 rows=read(root/'reference.private.json')
 views={v:e.score.counts([row for row in rows if row['person']==v.split(':')[0]],[responses.get((v,r),{})for r in(0,1)])for v in plan.VIEWS}
 # Aggregate only like-for-like guided cards. Baseline a8r remains its own15.
 total={k:Counter()for k in e.score.counts([], [{}])}
 for v in ('a8r:guidance','c2v:guidance'):
  for k,value in views[v].items():total[k].update(value)
 return {'fixed_views':views,'guided30':{k:dict(v)for k,v in total.items()},'generation_stability_verified':False,'old43_scores_replaced':False}

def run(root,destination,invoke,before,*,simulated):
 from runaway.constraint_extract import parse_answer,check
 plan.verify(root);destination=Path(destination);destination.mkdir(exist_ok=False)
 records=[];responses={};none=None;gates={};stop=None
 rows=read(root/'reference.private.json');requests=read(root/'static-requests.json')
 for slot in read(root/'slots.json'):
  if slot['kind']=='read' and not(all(gates.get(pid,{}).get('qualified')for pid in plan.PROFILES)):stop='controls_not_qualified';break
  try:
   plan.verify(root);guard=before(slot)
   if not simulated and not guard.get('owned_active'):raise PermissionError('Owned temporary guard required')
  except Exception as exc:stop='pre_call_failure:'+type(exc).__name__;break
  if len(records)>=9:stop='attempt_cap';break
  folder=destination/('attempt-%02d'%slot['slot']);folder.mkdir();req=requests[str(slot['slot'])]
  rec={**slot,'request_sha256':digest(req),'state':'invocation_intent','usage':None,'simulated':simulated}
  write_new(folder/'request.json',req);write_new(folder/'intent.json',{**rec,'guard':guard});records.append(rec)
  try:
   raw,prov=invoke(req,folder,slot)
   write_new(folder/'raw-response.json',{'raw':raw,'provenance':prov});rec['raw_response_sha256']=sha(folder/'raw-response.json')
   rec['usage']=e.usage(prov)
   if prov.get('model_requested')!=p.MODEL or(not simulated and prov.get('backend')!='codex'):
    raise ValueError('Backend/model differs')
   if type(raw)is not str or len(raw.encode())>256000:raise ValueError('Raw type/size differs')
   answer=parse_answer(raw);check(answer,req['schema'])
   p.choice_reader.decode_response(p.inputs()['queries']['all'],answer,answer_format='text',reader_mode='standard')
   write_new(folder/'answer.json',answer)
   if slot['kind']=='none':none=answer
   elif slot['kind']=='full':
    own=[r for r in rows if r['person']==slot['profile']]
    f,n=e.score.counts(own,[answer]),e.score.counts(own,[none])
    gate={'qualified':f['joint']['correct']==15 and not f['joint']['missing'] and f['personal_known']['correct']>n['personal_known']['correct'],'full':f,'none':n}
    gates[slot['profile']]=gate
    write_new(destination/('control-gate-'+slot['profile']+'.json'),gate)
    if not gate['qualified']:stop='full_control_not_qualified'
   else:responses[slot['view'],slot['read_repeat']]=answer
   rec['state']='completed'
  except Exception as exc:
   rec.update(state='failed',error_type=type(exc).__name__,error=str(exc));stop='transport_wire_decode_usage_or_model_failure'
   prov=getattr(exc,'provenance',None)
   if prov:
    write_new(folder/'failure-provenance.json',prov)
    try:rec['usage']=e.usage(prov)
    except ValueError:pass
  write_new(folder/'result.json',rec)
  if stop:break
 total=Counter()
 for rec in records:
  if rec['usage']is not None:total.update(rec['usage'])
 result={'status':'stopped' if stop else 'complete','stop':stop,'records':records,'control_gates':gates,
  'attempt_reservations':len(records),'local_cli_child_intents':len(list(destination.glob('attempt-*/backend-child-intent.json'))),
  'known_usage':dict(total),'missing_usage':sum(r['usage']is None for r in records),'scope_closed':True,
  'unused_slots_expire':9-len(records),'simulated':simulated,'new_service_authority':False,'scores':summarize(root,responses),
  'new_extractions':0,'old_scopes_reopened':False,'generation_stability_verified':False,'independent_holdout':False}
 write_new(destination/'result.json',result);return result
