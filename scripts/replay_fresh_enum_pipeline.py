"""Offline replay of the fresh-source45 pipeline;no model backend or grant."""
import argparse,importlib.util,json,tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
engine=load('fresh45_replay_engine',ROOT/'benchmarks/fresh-enum-pipeline-v1/engine.py');p=engine.plan
shared=load('fresh45_replay_shared',ROOT/'scripts/replay_compression_stability.py');require=shared.require
from runaway.constraint_extract import parse_answer
KIND='actual_fresh_enum_pipeline45'
INPUT='b27a444aca8e57a5027c75cd571e2e4161aede1836af489f38b472863967ae2f'
SOURCE_REF='fcf9c9799abcd8e18683602f31afd0fcbbdbbde3'
DEFAULT=ROOT/'benchmarks/fresh-enum-pipeline-v1/measured.synthetic.json'
FALSE_CLAIMS=('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
 'initial_generation_stability_verified','review_repetition_stability_verified','real_person_fidelity_verified','old_scopes_reopened',
 'old_scores_replaced','external_reader_decoder','token_matched_tail','optimal_tail_selection','source_reference_semantics_verified')

def replay(data):
 require(data['kind']==KIND and data['source_input_manifest_sha256']==INPUT and data['scientific_source_ref']==SOURCE_REF,'Scope/input/source differs')
 for key in FALSE_CLAIMS:require(data[key]is False,'Unsupported claim:'+key)
 for key in('all_sources_fictional','fresh_initial_drafts','pipeline_not_enum_only_ablation'):require(data[key]is True,'Design differs:'+key)
 expected=p.values()
 for key,file in(('intake_protocol','proposal.json'),('sources','sources.json'),('queries','queries.public.json'),
 ('reference_rows','reference.private.json'),('author_evidence','author-evidence.private.json'),('design','design.json'),('slots','slots.json'),('implementation_sha256','implementation-sha256.json')):
  require(data[key]==expected[file],'Reconstruction differs:'+key)
 state,records=data['status'],data['records']
 require(state['scope_closed']is True and state['simulated']is False,'Closed actual scope required')
 require(state['attempt_reservations']==len(records)<=45 and state['unused_slots_expire']==45-len(records),'Attempt ledger differs')
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
  root=Path(tmp)/'inputs';p.prepare(root);require(p.sha(root/'manifest.json')==INPUT,'Portable input manifest differs')
  destination=Path(tmp)/'replay';restored=engine.run(root,destination,invoke,before,simulated=True)
  require(not errors and position==len(records),'Archive not faithfully replayed:'+repr(errors))
  for key in('status','stop','control_gate','invalid_products','skipped','attempt_reservations','known_usage','missing_usage','scope_closed','unused_slots_expire','scores','old_scopes_reopened','production_default_changed'):
   require(restored[key]==state[key],'Controller/scorer differs:'+key)
  for old,new in zip(records,restored['records']):
   require(all(old[k]==new[k]for k in('slot','kind','profile','view','read_repeat','state','usage','request_sha256')),'Record differs')
   require(old.get('error_type')==new.get('error_type')and bool(old.get('product_invalid'))==bool(new.get('product_invalid')),'Failure/product differs')
   require(old.get('request_schema_conformant')==new.get('request_schema_conformant'),'Request schema conformance differs')
   file=destination/('attempt-%02d'%new['slot'])/'artifact.json'
   if file.exists():require(old.get('card')==p.read(file)and old['artifact_sha256']==p.sha(file),'Artifact differs')
   else:require('card'not in old and'artifact_sha256'not in old,'Unbound artifact inserted')
 responses={(r['profile'],r['view'],r['read_repeat']):parse_answer(r['raw'])for r in records if r['kind']=='read'and r['state']=='completed'}
 losses=[]
 for pid in p.PROFILES:
  for view in p.VIEWS:
   answers=[responses.get((pid,view,repeat),{})for repeat in(0,1)]
   for row in expected['reference.private.json']:
    if row['person']!=pid:continue
    values=[[a.get(q)for q in row['query_ids']]for a in answers];flat=[v for vs in values for v in vs]
    if any(v!=row['gold']for v in flat):losses.append({'person':pid,'view':view,'case':row['case'],'gold':row['gold'],
     'cohort':row['cohort'],'derived_known':row['derived_known'],'reads_orders':values,'missing':any(v is None for v in flat),
     'known_to_U_answers':sum(v=='U'for v in flat)if row['gold']!='U'else 0,
     'unknown_to_choice_answers':sum(v not in(None,'U')for v in flat)if row['gold']=='U'else 0})
 def summarize_cells(cells):
  endpoints={v:{'planned':len(cells),'correct':sum(c[v]['correct']for c in cells),'missing':sum(c[v]['missing']for c in cells)}for v in p.VIEWS}
  paired={}
  for stage in('draft','reviewed'):
   count=Counter()
   for c in cells:
    card,tail=c[stage],c[stage+'_tail']
    label='some_missing'if card['missing']or tail['missing']else'both_correct'if card['correct']and tail['correct']else'card_only_correct'if card['correct']else'tail_only_correct'if tail['correct']else'both_observed_error'
    count[label]+=1
   paired[stage]=dict(count)
  return {'endpoints':endpoints,'recovered_from_observed_draft_error':sum(not c['draft']['correct']and not c['draft']['missing']and c['reviewed']['correct']for c in cells),
   'observed_review_regressions':sum(c['draft']['correct']and not c['reviewed']['correct']and not c['reviewed']['missing']for c in cells),
   'correct_draft_to_missing_review':sum(c['draft']['correct']and c['reviewed']['missing']for c in cells),'paired_card_tail_cells':paired}
 cells=state['scores']['transitions']
 groups={'all':summarize_cells(cells),'known':summarize_cells([c for c in cells if c['known']]),'unknown':summarize_cells([c for c in cells if not c['known']]),'derived_known':summarize_cells([c for c in cells if c['derived_known']])}
 for name in sorted({c['cohort']for c in cells}):groups['cohort:'+name]=summarize_cells([c for c in cells if c['cohort']==name])
 stages={}
 for rec in records:
  name=rec['view']if rec['kind']=='read'else rec['kind'];value=stages.setdefault(name,Counter());value['attempts']+=1;value['missing_usage_records']+=rec['usage']is None
  if rec['usage']is not None:value.update(rec['usage'])
 availability={stage:{'planned':4,'attempted':sum(r['kind']==kind for r in records),'valid_cards':sum(r['kind']==kind and'card'in r for r in records),
  'invalid_products':sum(r['kind']==kind and bool(r.get('product_invalid'))for r in records),'public_characters':[r['card']['characters']for r in records if r['kind']==kind and'card'in r]}for stage,kind in(('draft','extract'),('reviewed','review'))}
 qualified=len(state['control_gate'])==4 and all(v['qualified']for v in state['control_gate'].values())
 return {'actual_original_attempts':len(records),'actual_original_children':state['local_cli_child_intents'],'original_status':state['status'],'original_stop':state['stop'],
  'known_original_usage':state['known_usage'],'missing_original_usage':state['missing_usage'],'invalid_products':state['invalid_products'],'skipped':state['skipped'],
  'controls_qualified':qualified,'compression_evidence_available':qualified and any(r['kind']=='read'and r['state']=='completed'for r in records),'scores':state['scores'],
  'summary':groups,'failed_or_missing_cases':losses,'product_availability':availability,'cards':[r['card']for r in records if'card'in r],
  'reported_usage_by_stage':{k:dict(v)for k,v in stages.items()},'new_model_calls':0,'old_scores_replaced':False,'production_default_changed':False,
  'initial_generation_stability_verified':False,'review_repetition_stability_verified':False,'independent_semantic_acceptance':False,'scientific_source_ref':SOURCE_REF}

def check(path=DEFAULT):
 path=Path(path);require(p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs');return replay(p.read(path))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT)
 print(json.dumps(check(parser.parse_args().input),ensure_ascii=False,indent=2))
