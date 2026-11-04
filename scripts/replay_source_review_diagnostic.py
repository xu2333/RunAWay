"""Offline replay of a fixed-draft source-review diagnostic; no service capability."""
import argparse,importlib.util,json,tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
engine=load('review7_public_engine',ROOT/'benchmarks/source-review-diagnostic-v1/engine.py')
p=engine.plan
shared=load('review7_archive_shared',ROOT/'scripts/replay_compression_stability.py')
from runaway.constraint_extract import parse_answer
KIND='actual_source_review_fixed_draft7'
INPUT='cd5c7aa21640533e187476c7acf8fd3c02238bf21d274a6c3153d723f2408912'
DEFAULT=ROOT/'benchmarks/source-review-diagnostic-v1/measured.synthetic.json'
require=shared.require

def replay(data):
 require(data['kind']==KIND and data['source_input_manifest_sha256']==INPUT,'Scope/input differs')
 for key in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
  'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old66_scores_replaced',
  'external_reader_decoder','token_matched_tail','optimal_tail_selection'):
  require(data[key]is False,'Unsupported claim:'+key)
 require(data['all_sources_fictional']is True and data['posthoc_consumed_fixed_card']is True,'Design differs')
 expected=p.values()
 for key,file in(('intake_protocol','proposal.json'),('sources','sources.json'),('queries','queries.public.json'),
  ('reference_rows','reference.private.json'),('materials','materials.public.json'),('draft','draft.private.json'),
  ('origin','origin.public.json'),('slots','slots.json'),('implementation_sha256','implementation-sha256.json')):
  require(data[key]==expected[file],'Reconstruction differs:'+key)
 state,records=data['status'],data['records']
 require(state['scope_closed']is True and state['simulated']is False,'Closed actual scope required')
 require(state['attempt_reservations']==len(records)<=7 and state['unused_slots_expire']==7-len(records),'Attempt ledger differs')
 require(state['local_cli_child_intents']==sum(r['local_cli_child_intent']is True for r in records),'Child ledger differs')
 position=0;errors=[]
 def before(slot):
  if position==len(records)and state['stop']and state['stop'].startswith('pre_call_failure:'):raise shared.archived_error(state['stop'].split(':',1)[1])
  return {'offline_archive_fixture':True}
 def invoke(req,folder,slot):
  nonlocal position
  if position>=len(records):errors.append('Unrecorded call');raise ValueError(errors[-1])
  rec=records[position];position+=1
  try:
   require(all(rec[k]==v for k,v in slot.items()),'Reordered/foreign slot')
   require(req==rec['request']and p.digest(req)==rec['request_sha256'],'Exact request differs')
   if rec['raw_present']:
    require(p.digest(rec['raw'])==rec['raw_value_sha256'],'Raw differs')
    require(rec['backend']=='codex'and rec['local_cli_child_intent']is True,'Backend/child differs')
   else:require(rec['state']=='failed','Completed without raw')
  except(ValueError,KeyError)as exc:errors.append(str(exc));raise
  prov={'backend':rec['backend'],'model_requested':rec['requested_model'],'usage':rec['usage_rows']}
  if rec['raw_present']:return rec['raw'],prov
  exc=shared.archived_error(rec['error_type'])
  if rec['usage_rows']is not None:exc.provenance=prov
  raise exc
 with tempfile.TemporaryDirectory()as tmp:
  root=Path(tmp)/'inputs';p.prepare(root)
  require(p.sha(root/'manifest.json')==INPUT,'Portable input manifest differs')
  destination=Path(tmp)/'replay';restored=engine.run(root,destination,invoke,before,simulated=True)
  require(not errors and position==len(records),'Original archive not faithfully replayed:'+repr(errors))
  for key in('status','stop','control_gate','invalid_products','skipped','attempt_reservations','known_usage','missing_usage',
   'scope_closed','unused_slots_expire','scores','new_initial_extractions','old_scopes_reopened','generation_stability_verified','independent_holdout'):
   require(restored[key]==state[key],'Controller/scorer differs:'+key)
  for old,new in zip(records,restored['records']):
   require(all(old[k]==new[k]for k in('slot','kind','profile','view','read_repeat','state','usage','request_sha256')),'Record differs')
   require(old.get('error_type')==new.get('error_type')and bool(old.get('product_invalid'))==bool(new.get('product_invalid')),'Failure/product differs')
   file=destination/('attempt-%02d'%new['slot'])/'artifact.json'
   if file.exists():require(old.get('card')==p.read(file)and old['artifact_sha256']==p.sha(file),'Reviewed artifact differs')
   else:require('card'not in old and'artifact_sha256'not in old,'Unbound artifact inserted')
 responses={(r['view'],r['read_repeat']):parse_answer(r['raw'])for r in records if r['kind']=='read'and r['state']=='completed'}
 rows=expected['reference.private.json'];losses=[];per_read={};domains={}
 for view in('original','reviewed'):
  answers=[responses.get((view,r),{})for r in(0,1)]
  per_read[view]={str(r):engine.score.counts(rows,[answers[r]])for r in(0,1)}
  domains[view]={name:engine.score.counts([r for r in rows if r['case'].startswith(name+'_')],answers)for name in('notes','signup','outside')}
  for row in rows:
   values=[[a.get(q)for q in row['query_ids']]for a in answers];flat=[v for a in values for v in a]
   if any(v!=row['gold']for v in flat):losses.append({'view':view,'case':row['case'],'gold':row['gold'],'derived_known':row['derived_known'],
    'missing':any(v is None for v in flat),'reads_orders':values,'known_to_U_answers':sum(v=='U'for v in flat)if row['gold']!='U'else 0,
    'unknown_to_choice_answers':sum(v not in(None,'U')for v in flat)if row['gold']=='U'else 0})
 stages={}
 for r in records:
  label=r['kind']if r['kind']!='read'else r['view']+'_read';v=stages.setdefault(label,Counter());v['attempts']+=1;v['missing_usage_records']+=r['usage']is None
  if r['usage']is not None:v.update(r['usage'])
 return {'actual_original_attempts':len(records),'actual_original_children':state['local_cli_child_intents'],
  'original_status':state['status'],'original_stop':state['stop'],'known_original_usage':state['known_usage'],
  'missing_original_usage':state['missing_usage'],'invalid_products':state['invalid_products'],'skipped':state['skipped'],
  'scores':state['scores'],'per_read':per_read,'by_domain':domains,'failed_or_missing_cases':losses,
  'reviewed_cards':[r['card']for r in records if'card'in r],'reported_usage_by_stage':{k:dict(v)for k,v in stages.items()},
  'new_model_calls':0,'old66_scores_replaced':False,'new_initial_extractions':0,'production_default_changed':False,
  'generation_stability_verified':False,'independent_semantic_acceptance':False,'posthoc_fixed_draft':True}

def check(path=DEFAULT):
 path=Path(path);require(p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
 return replay(p.read(path))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT)
 print(json.dumps(check(parser.parse_args().input),ensure_ascii=False,indent=2))
