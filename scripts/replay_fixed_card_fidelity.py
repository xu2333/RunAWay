"""Offline replay of six fixed-card diagnostic slots; no service backend."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
readiness=load('fixed_card_origin_archive',ROOT/'scripts/replay_extraction_readiness.py')
p,e=readiness.p,readiness.engine
shared=load('fixed_card_archived_failures',ROOT/'scripts/replay_compression_stability.py')
read,sha,digest,write_new=p.read,p.sha,p.digest,e.base.write_new
from runaway.constraint_extract import parse_answer
HERE=ROOT/'benchmarks/fixed-card-fidelity-v1'
DEFAULT=HERE/'measured.synthetic.json'
INPUT='bd04d6be08ee37750a8532bed72c062e9bf9327c947bc2a9b5e210e421642e7b'
PROTOCOL_SHA='1eebcf853a6205f2911e9d279efd3408f2b883f6f8484a5608869cfc0df2ff7a'
KIND='actual_epistemic_fixed_card_fidelity6'

def require(value,message):
 if not value:raise ValueError(message)

def values():
 require(sha(HERE/'protocol.json')==PROTOCOL_SHA,'Frozen protocol differs')
 readiness.check()
 card=p.read(readiness.DEFAULT)['record']['card']['prompt']
 materials={'card':card,'tail':p.material('a8r',card,'tail')}
 slots=[{'slot':1,'kind':'none','profile':'a8r','view':None,'read_repeat':None},
  {'slot':2,'kind':'full','profile':'a8r','view':None,'read_repeat':None}]+[
  {'slot':i+3,'kind':'read','profile':'a8r','view':v,'read_repeat':r}
  for i,(v,r)in enumerate((('card',0),('tail',0),('tail',1),('card',1)))]
 requests={'1':p.request(p.slots()[0]),'2':p.request(p.slots()[1])}
 for slot in slots[2:]:
  req=p.choice_reader.make_request(materials[slot['view']],p.inputs()['queries']['all'],
   as_of=p.AS_OF,answer_format='text',reader_mode='standard')
  requests[str(slot['slot'])]={'model':p.MODEL,'system':p.base.old.old.grouped_support.SYSTEM,**req,
   'prompt':p.base.old.old.COMMON+req['prompt']}
 return {'proposal.json':read(HERE/'protocol.json'),'slots.json':slots,'static-requests.json':requests,
  'reference.private.json':[r for r in p.inputs()['rows']if r['person']=='a8r'],
  'implementation-sha256.json':p.implementation(),'materials.public.json':materials}

def prepare(destination):
 contents=values();destination.mkdir(exist_ok=False)
 files={}
 for name,value in contents.items():
  text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
  (destination/name).write_text(text,encoding='utf8');files[name]=sha(destination/name)
 (destination/'manifest.json').write_text(json.dumps({'files':files,'new_model_calls':0},indent=2),encoding='utf8')
 require(sha(destination/'manifest.json')==INPUT,'Reconstructed portable input differs')

def verify_inputs(root):
 require(sha(root/'manifest.json')==INPUT,'Input manifest differs')
 for name,expected in read(root/'manifest.json')['files'].items():
  path=Path(name)
  require(not path.is_absolute()and'..'not in path.parts and not(root/path).is_symlink()and sha(root/path)==expected,'Frozen input drift')
 require(all(read(root/name)==value for name,value in values().items()),'Reconstructed input drift')

def summarize(root,responses):
 rows=read(root/'reference.private.json')
 return {view:e.score.counts(rows,[responses.get((view,r),{}) for r in (0,1)]) for view in ('card','tail')}

def run(root,destination,invoke,before,*,simulated):
 from runaway.constraint_extract import parse_answer,check
 verify_inputs(root);destination=Path(destination);destination.mkdir(exist_ok=False)
 records=[];responses={};none=None;gate=None;stop=None
 rows=read(root/'reference.private.json');requests=read(root/'static-requests.json')
 for slot in read(root/'slots.json'):
  if slot['kind']=='read' and not(gate and gate['qualified']):stop='controls_not_qualified';break
  try:
   verify_inputs(root);guard=before(slot)
   if not simulated and not guard.get('owned_active'):raise PermissionError('Owned temporary guard required')
  except Exception as exc:stop='pre_call_failure:'+type(exc).__name__;break
  if len(records)>=6:stop='attempt_cap';break
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
    f,n=e.score.counts(rows,[answer]),e.score.counts(rows,[none])
    gate={'qualified':f['joint']['correct']==15 and not f['joint']['missing'] and f['personal_known']['correct']>n['personal_known']['correct'],'full':f,'none':n}
    write_new(destination/'control-gate.json',gate)
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
 result={'status':'stopped' if stop else 'complete','stop':stop,'records':records,'control_gate':gate,
  'attempt_reservations':len(records),'local_cli_child_intents':len(list(destination.glob('attempt-*/backend-child-intent.json'))),
  'known_usage':dict(total),'missing_usage':sum(r['usage']is None for r in records),'scope_closed':True,
  'unused_slots_expire':6-len(records),'simulated':simulated,'new_service_authority':False,'scores':summarize(root,responses),
  'new_extractions':0,'old_scopes_reopened':False,'generation_stability_verified':False,'independent_holdout':False}
 write_new(destination/'result.json',result);return result

def replay(data):
 require(data['kind']==KIND and data['source_input_manifest_sha256']==INPUT,'Scope/input differs')
 for key in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
  'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old49_scores_replaced',
  'external_reader_decoder','token_matched_tail','optimal_tail_selection'):
  require(data[key]is False,'Unsupported claim:'+key)
 require(data['all_sources_fictional']is True and data['posthoc_consumed_fixed_card']is True,'Design boundary differs')
 expected=values()
 require(data['intake_protocol']==expected['proposal.json']and data['slots']==expected['slots.json'],'Protocol/slots differ')
 require(data['sources']=={'a8r':p.inputs()['sources']['a8r']}and data['queries']==p.inputs()['queries']['all'],'Source/questions differ')
 require(data['reference_rows']==expected['reference.private.json']and data['materials']==expected['materials.public.json'],'Reference/material differs')
 require(data['implementation_sha256']==expected['implementation-sha256.json'],'Implementation differs')
 state,records=data['status'],data['records']
 require(state['scope_closed']is True and state['simulated']is False,'Closed actual scope required')
 require(state['attempt_reservations']==len(records)<=6 and state['unused_slots_expire']==6-len(records),'Call ledger differs')
 require(state['local_cli_child_intents']==sum(r['local_cli_child_intent']is True for r in records),'Child ledger differs')
 position=0;errors=[]
 def before(slot):
  if position==len(records)and state['stop']and state['stop'].startswith('pre_call_failure:'):
   raise shared.archived_error(state['stop'].split(':',1)[1])
  return {'offline_archive_fixture':True}
 def invoke(request,folder,slot):
  nonlocal position
  if position>=len(records):
   errors.append('Replay tried an unrecorded call');raise ValueError(errors[-1])
  rec=records[position];position+=1
  try:
   require(all(rec[k]==v for k,v in slot.items()),'Reordered/foreign slot')
   require(request==rec['request']and digest(request)==rec['request_sha256'],'Exact fixed request differs')
   if rec['raw_present']:
    require(digest(rec['raw'])==rec['raw_value_sha256'],'Raw differs')
    require(rec['backend']=='codex'and rec['local_cli_child_intent']is True,'Original backend/child differs')
   else:require(rec['state']=='failed','Completed without raw')
  except(ValueError,KeyError)as exc:errors.append(str(exc));raise
  prov={'backend':rec['backend'],'model_requested':rec['requested_model'],'usage':rec['usage_rows']}
  if rec['raw_present']:return rec['raw'],prov
  exc=shared.archived_error(rec['error_type'])
  if rec['usage_rows']is not None:exc.provenance=prov
  raise exc
 with tempfile.TemporaryDirectory()as temp:
  root=Path(temp)/'inputs';prepare(root)
  restored=run(root,Path(temp)/'replay',invoke,before,simulated=True)
  require(not errors,'Archive validation failed:'+repr(errors))
  require(position==len(records),'Records not all replayed')
  for key in('status','stop','control_gate','attempt_reservations','known_usage','missing_usage','scope_closed',
   'unused_slots_expire','scores','new_extractions','old_scopes_reopened','generation_stability_verified','independent_holdout'):
   require(restored[key]==state[key],'Controller/scorer differs:'+key)
  require(len(restored['records'])==len(records),'Attempt count differs')
  for old,new in zip(records,restored['records']):
   require(all(old[k]==new[k]for k in('slot','kind','profile','view','read_repeat','state','usage','request_sha256')),'Record differs')
   require(old.get('error_type')==new.get('error_type'),'Failure category differs')
 responses={(r['view'],r['read_repeat']):parse_answer(r['raw'])for r in records if r['kind']=='read'and r['state']=='completed'}
 rows=expected['reference.private.json'];losses=[];domains={};stages={};per_read={};variation={}
 for view in('card','tail'):
  answers=[responses.get((view,i),{})for i in(0,1)]
  per_read[view]={'first':e.score.counts(rows,[answers[0]]),'second':e.score.counts(rows,[answers[1]])}
  variation[view]=e.score.disagreement(rows,[answers[0]],[answers[1]])
  domains[view]={name:e.score.counts([r for r in rows if r['case'].startswith(name+'_')],answers)
   for name in('notes','signup','outside')}
  for row in rows:
   observed=[[answer.get(q)for q in row['query_ids']]for answer in answers]
   flat=[v for group in observed for v in group]
   if any(v!=row['gold']for v in flat):
    losses.append({'view':view,'case':row['case'],'cohort':row['cohort'],'gold':row['gold'],
     'reads_orders':observed,'missing':any(v is None for v in flat),
     'all_answers_unknown_instead_of_known':row['gold']!='U'and all(v=='U'for v in flat)})
 for record in records:
  name=record['kind']if record['kind']!='read'else record['view']+'_read'
  stage=stages.setdefault(name,Counter());stage['attempts']+=1;stage['missing_usage_records']+=record['usage']is None
  if record['usage']is not None:stage.update(record['usage'])
 return {'actual_original_attempts':len(records),'actual_original_children':state['local_cli_child_intents'],
  'original_status':state['status'],'original_stop':state['stop'],'known_original_usage':state['known_usage'],
  'missing_original_usage':state['missing_usage'],'unused_slots_expired':state['unused_slots_expire'],
  'control_gate':state['control_gate'],'scores':state['scores'],'primary_cases_per_view':15,
  'answers_per_case_per_view':4,'fixed_card_characters':len(expected['materials.public.json']['card']),
  'per_domain':domains,'per_read':per_read,'within_view_read_disagreement':variation,'failed_or_missing_cases':losses,'reported_usage_by_stage':{k:dict(v)for k,v in stages.items()},
  'new_model_calls':0,'new_extractions':0,'old49_missing_cases_filled':False,
  'independent_holdout':False,'generation_stability_verified':False,'independent_semantic_acceptance':False,
  'replay_is_simulated_not_new_inference':True}

def check(path=DEFAULT):
 path=Path(path);require(sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
 return replay(read(path))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT)
 args=parser.parse_args();print(json.dumps(check(args.input),ensure_ascii=False,indent=2))
