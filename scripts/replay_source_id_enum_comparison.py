"""Offline replay of the same-batch source-ID enum comparison; no service capability."""
import argparse,importlib.util,json,tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
engine=load('enum59_public_engine',ROOT/'benchmarks/source-id-enum-repeat-v1/engine.py')
p=engine.plan
shared=load('enum59_archive_shared',ROOT/'scripts/replay_compression_stability.py')
from runaway.constraint_extract import parse_answer
KIND='actual_source_id_enum_repeat59'
INPUT='e2d286558b07fb34c7c70c0cd7f7a4f753d8b5bd4cb633b93499a79ceeedd94e'
DEFAULT=ROOT/'benchmarks/source-id-enum-repeat-v1/measured.synthetic.json'
require=shared.require

def replay(data):
 require(data['kind']==KIND and data['source_input_manifest_sha256']==INPUT,'Scope/input differs')
 for key in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
  'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old_scores_replaced',
  'external_reader_decoder','token_matched_tail','optimal_tail_selection'):
  require(data[key]is False,'Unsupported claim:'+key)
 require(data['all_sources_fictional']is True and data['posthoc_consumed_fixed_parents']is True,'Design differs')
 expected=p.values()
 for key,file in(('intake_protocol','proposal.json'),('sources','sources.json'),('queries','queries.public.json'),
  ('reference_rows','reference.private.json'),('parents','parents.public.json'),('slots','slots.json'),('implementation_sha256','implementation-sha256.json')):
  require(data[key]==expected[file],'Reconstruction differs:'+key)
 state,records=data['status'],data['records']
 require(state['scope_closed']is True and state['simulated']is False,'Closed actual scope required')
 require(state['attempt_reservations']==len(records)<=59 and state['unused_slots_expire']==59-len(records),'Attempt ledger differs')
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
   'scope_closed','unused_slots_expire','scores','new_initial_extractions','old_scopes_reopened','source_reference_semantics_verified','independent_holdout','production_default_changed'):
   require(restored[key]==state[key],'Controller/scorer differs:'+key)
  for old,new in zip(records,restored['records']):
   require(all(old[k]==new[k]for k in('slot','kind','profile','parent','method','review_repeat','view','read_repeat','state','usage','request_sha256')),'Record differs')
   require(old.get('error_type')==new.get('error_type')and bool(old.get('product_invalid'))==bool(new.get('product_invalid')),'Failure/product differs')
   require(old.get('request_schema_conformant')==new.get('request_schema_conformant'),'Request schema conformance differs')
   file=destination/('attempt-%02d'%new['slot'])/'artifact.json'
   if file.exists():require(old.get('card')==p.read(file)and old['artifact_sha256']==p.sha(file),'Reviewed artifact differs')
   else:require('card'not in old and'artifact_sha256'not in old,'Unbound artifact inserted')
 responses={(r['parent'],r['view'],r['method'],r['review_repeat'],r['read_repeat']):parse_answer(r['raw'])for r in records if r['kind']=='read'and r['state']=='completed'}
 rows=expected['reference.private.json'];parents=expected['parents.public.json'];losses=[];invalid_refs=[]
 for key,parent in parents.items():
  own=[r for r in rows if r['person']==parent['profile']]
  endpoints=[('original',None,None)]+[('reviewed',method,generation)for method in p.METHODS for generation in(0,1)]
  for view,method,generation in endpoints:
   answers=[responses.get((key,view,method,generation,r),{})for r in(0,1)]
   for row in own:
    values=[[answer.get(q)for q in row['query_ids']]for answer in answers];flat=[v for valueset in values for v in valueset]
    if any(v!=row['gold']for v in flat):losses.append({'parent':key,'person':parent['profile'],'view':view,'method':method,'review_repeat':generation,
     'case':row['case'],'gold':row['gold'],'derived_known':row['derived_known'],'missing':any(v is None for v in flat),
     'reads_orders':values,'known_to_U_answers':sum(v=='U'for v in flat)if row['gold']!='U'else 0,
     'unknown_to_choice_answers':sum(v not in(None,'U')for v in flat)if row['gold']=='U'else 0})
 for record in records:
  if record['kind']!='review'or not record.get('product_invalid'):continue
  answer=parse_answer(record['raw']);ids={s['id']for s in data['sources'][record['profile']]['sources']}
  def walk(value,path='$'):
   if isinstance(value,list):
    for i,v in enumerate(value):walk(v,path+'['+str(i)+']')
   elif isinstance(value,dict):
    if set(value)=={'source_id'}and value['source_id']not in ids:
     invalid_refs.append({'slot':record['slot'],'parent':record['parent'],'method':record['method'],'review_repeat':record['review_repeat'],'path':path,'source_id':value['source_id']})
    for key,v in value.items():walk(v,path+'.'+key)
  walk(answer)
 transitions=state['scores']['transitions']
 def summarize_cells(cells):
  original={'planned':len(cells),'correct':sum(c['original']['correct']for c in cells),'missing':sum(c['original']['missing']for c in cells)}
  methods={}
  for method in p.METHODS:
   endpoints={name:{'planned':len(cells),'correct':sum(c['methods'][method][name]['correct']for c in cells),'missing':sum(c['methods'][method][name]['missing']for c in cells)}for name in('review0','review1','both_reviews')}
   methods[method]={'endpoints':endpoints,
    'recovered_from_observed_error':sum(not c['original']['correct']and not c['original']['missing']and c['methods'][method]['both_reviews']['correct']for c in cells),
    'observed_regressions':sum(c['original']['correct']and not c['methods'][method]['both_reviews']['correct']and not c['methods'][method]['both_reviews']['missing']for c in cells),
    'review_missing':sum(c['methods'][method]['both_reviews']['missing']for c in cells)}
  paired={}
  for c in cells:
   def label(v):return 'missing'if v['missing']else'correct'if v['correct']else'observed_error'
   left=label(c['methods']['existing']['both_reviews']);right=label(c['methods']['enumerated']['both_reviews'])
   name=left+'__to__'+right;paired[name]=paired.get(name,0)+1
  return {'original':original,'methods':methods,'paired_joint_cells_existing_to_enumerated':paired}
 groups={'all':summarize_cells(transitions),'known':summarize_cells([c for c in transitions if c['known']]),
  'unknown':summarize_cells([c for c in transitions if not c['known']]),'derived_known':summarize_cells([c for c in transitions if c['derived_known']])}
 for band in('previously_complete','previously_incomplete'):groups[band]=summarize_cells([c for c in transitions if c['prior_band']==band])
 stages={}
 for record in records:
  name=record['kind']if record['kind']!='read'else record['view']+'_read'
  if record['method']is not None:name+=':'+record['method']
  value=stages.setdefault(name,Counter())
  value['attempts']+=1;value['missing_usage_records']+=record['usage']is None
  if record['usage']is not None:value.update(record['usage'])
 availability={}
 for method in p.METHODS:
  planned=[s for s in data['slots']if s['kind']=='review'and s['method']==method]
  attempted=[r for r in records if r['kind']=='review'and r['method']==method]
  cards=[r['card']for r in attempted if'card'in r]
  availability[method]={'planned_reviews':len(planned),'attempted_reviews':len(attempted),
   'completed_review_responses':sum(r['state']=='completed'for r in attempted),'valid_bound_cards':len(cards),
   'binding_or_budget_invalid':sum(bool(r.get('product_invalid'))for r in attempted),
   'request_schema_violations':sum(r.get('request_schema_conformant')is False for r in attempted),
   'unavailable_planned_cards':len(planned)-len(cards),'public_characters':[c['characters']for c in cards]}
 return {'actual_original_attempts':len(records),'actual_original_children':state['local_cli_child_intents'],
  'original_status':state['status'],'original_stop':state['stop'],'known_original_usage':state['known_usage'],'missing_original_usage':state['missing_usage'],
  'invalid_products':state['invalid_products'],'skipped':state['skipped'],'review_product_availability':availability,'scores':state['scores'],'summary':groups,
  'failed_or_missing_cases':losses,'undefined_reference_occurrences':invalid_refs,
  'reviewed_cards':[r['card']for r in records if'card'in r],
  'request_schema_violations':[{'slot':r['slot'],'parent':r['parent'],'method':r['method'],'review_repeat':r['review_repeat'],'product_invalid':r.get('product_invalid',False)}for r in records if r['kind']=='review'and r.get('request_schema_conformant')is False],'reported_usage_by_stage':{k:dict(v)for k,v in stages.items()},
  'new_model_calls':0,'old_scores_replaced':False,'new_initial_extractions':0,'production_default_changed':False,
  'generation_stability_verified':False,'independent_semantic_acceptance':False,'posthoc_fixed_parents':True}

def check(path=DEFAULT):
 path=Path(path);require(p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
 return replay(p.read(path))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT)
 print(json.dumps(check(parser.parse_args().input),ensure_ascii=False,indent=2))
