"""Replay closed nine-call fixed-card evidence without a service backend."""
import argparse,importlib.util,json,tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
engine=load('fixed_coverage9_public',ROOT/'benchmarks/coverage-fixed-views-v1/engine.py')
p=engine.plan
shared=load('fixed_coverage9_archive',ROOT/'scripts/replay_compression_stability.py')
from runaway.constraint_extract import parse_answer
KIND='actual_coverage_fixed_views_readonly9'
INPUT='c80f6e3e6340c5ab794c7846dbb5541c12abf6f2a87801a3273713bda1bf6800'
DEFAULT=ROOT/'benchmarks/coverage-fixed-views-v1/measured.synthetic.json'
require=shared.require

def replay(data):
 require(data['kind']==KIND and data['source_input_manifest_sha256']==INPUT,'Scope/input differs')
 for key in('new_service_authority','production_default_changed','independent_holdout','independent_semantic_acceptance',
  'generation_stability_verified','real_person_fidelity_verified','old_scopes_reopened','old43_scores_replaced',
  'external_reader_decoder','token_matched_tail','optimal_tail_selection'):
  require(data[key]is False,'Unsupported claim:'+key)
 require(data['all_sources_fictional']is True and data['posthoc_consumed_fixed_cards']is True,'Design differs')
 expected=p.values()
 require(data['intake_protocol']==expected['proposal.json']and data['slots']==expected['slots.json'],'Protocol/slots differ')
 for key,file in(('sources','sources.json'),('queries','queries.public.json'),('reference_rows','reference.private.json'),
                  ('materials','materials.public.json'),('origin','origin.public.json'),('implementation_sha256','implementation-sha256.json')):
  require(data[key]==expected[file],'Reconstructed evidence differs:'+key)
 state,records=data['status'],data['records']
 require(state['scope_closed']is True and state['simulated']is False,'Closed actual scope required')
 require(state['attempt_reservations']==len(records)<=9 and state['unused_slots_expire']==9-len(records),'Call ledger differs')
 require(state['local_cli_child_intents']==sum(r['local_cli_child_intent']is True for r in records),'Child ledger differs')
 position=0;errors=[]
 def before(slot):
  if position==len(records)and state['stop']and state['stop'].startswith('pre_call_failure:'):
   raise shared.archived_error(state['stop'].split(':',1)[1])
  return {'offline_archive_fixture':True}
 def invoke(request,folder,slot):
  nonlocal position
  if position>=len(records):errors.append('Unrecorded call');raise ValueError(errors[-1])
  rec=records[position];position+=1
  try:
   require(all(rec[k]==v for k,v in slot.items()),'Reordered/foreign slot')
   require(request==rec['request']and p.digest(request)==rec['request_sha256'],'Exact request differs')
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
 with tempfile.TemporaryDirectory()as temp:
  root=Path(temp)/'inputs';p.prepare(root)
  require(p.sha(root/'manifest.json')==INPUT,'Portable input manifest differs')
  restored=engine.run(root,Path(temp)/'replay',invoke,before,simulated=True)
  require(not errors and position==len(records),'Original records not faithfully replayed:'+repr(errors))
  for key in('status','stop','control_gates','attempt_reservations','known_usage','missing_usage','scope_closed',
   'unused_slots_expire','scores','new_extractions','old_scopes_reopened','generation_stability_verified','independent_holdout'):
   require(restored[key]==state[key],'Controller/scorer differs:'+key)
  require(len(restored['records'])==len(records),'Attempt count differs')
  for old,new in zip(records,restored['records']):
   require(all(old[k]==new[k]for k in('slot','kind','profile','view','read_repeat','state','usage','request_sha256')),'Record differs')
   require(old.get('error_type')==new.get('error_type'),'Failure category differs')
 responses={(r['view'],r['read_repeat']):parse_answer(r['raw'])for r in records if r['kind']=='read'and r['state']=='completed'}
 rows=expected['reference.private.json'];losses=[];domains={};per_read={};variation={};paired=[]
 for view in p.VIEWS:
  own=[r for r in rows if r['person']==view.split(':')[0]];answers=[responses.get((view,i),{})for i in(0,1)]
  per_read[view]={'first':engine.e.score.counts(own,[answers[0]]),'second':engine.e.score.counts(own,[answers[1]])}
  variation[view]=engine.e.score.disagreement(own,[answers[0]],[answers[1]])
  domains[view]={name:engine.e.score.counts([r for r in own if r['case'].startswith(name+'_')],answers)for name in('notes','signup','outside')}
  for row in own:
   observed=[[a.get(q)for q in row['query_ids']]for a in answers];flat=[v for a in observed for v in a]
   if any(v!=row['gold']for v in flat):
    losses.append({'view':view,'case':row['case'],'gold':row['gold'],'reads_orders':observed,
      'missing':any(v is None for v in flat),'all_answers_unknown_instead_of_known':row['gold']!='U'and all(v=='U'for v in flat)})
 for row in rows:
  if row['person']!='a8r':continue
  correct={v:all(responses.get((v,i),{}).get(q)==row['gold']for i in(0,1)for q in row['query_ids'])for v in('a8r:baseline','a8r:guidance')}
  paired.append({'case':row['case'],'baseline_correct':correct['a8r:baseline'],'guided_correct':correct['a8r:guidance']})
 stages={}
 for rec in records:
  name=rec['kind']if rec['kind']!='read'else rec['view'];s=stages.setdefault(name,Counter())
  s['attempts']+=1;s['missing_usage_records']+=rec['usage']is None
  if rec['usage']is not None:s.update(rec['usage'])
 controls={}
 for kind in('full','none'):
  totals={}
  for gate in state['control_gates'].values():
   for cohort,counts in gate[kind].items():totals.setdefault(cohort,Counter()).update(counts)
  controls[kind]={k:dict(v)for k,v in totals.items()}
 # Separate, consumed scopes: bind the unchanged producer request, not a causal experiment.
 old_path=ROOT/'benchmarks/extraction-readiness-v1/measured.synthetic.json'
 old_reads_path=ROOT/'benchmarks/fixed-card-fidelity-v1/measured.synthetic.json'
 for path in(old_path,old_reads_path):
  require(p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Historical archive checksum differs')
 old=p.read(old_path);old_reads=p.read(old_reads_path)
 fresh=p.read(p.ARCHIVE);origin=next(r for r in fresh['records']if r['slot']==4)
 require(old_reads['materials']['card']==old['record']['card']['prompt'],'Historical card binding differs')
 require(data['materials']['a8r:baseline']==origin['card']['prompt'],'Fresh baseline binding differs')
 comparison={'same_exact_producer_request':old['record']['request']==origin['request'],
  'old_card_characters':len(old_reads['materials']['card']),'fresh_baseline_characters':len(origin['card']['prompt']),
  'old_fixed_card_result':old_reads['status']['scores']['card']['joint'],
  'fresh_fixed_card_result':state['scores']['fixed_views']['a8r:baseline']['joint'],
  'same_public_questions':old_reads['queries']==data['queries']['all'],
  'cross_scope_not_randomized':True,'causal_guidance_effect_established':False,
  'generation_stability_estimated':False,'old_results_replaced':False}
 return {'actual_original_attempts':len(records),'actual_original_children':state['local_cli_child_intents'],
  'original_status':state['status'],'original_stop':state['stop'],'known_original_usage':state['known_usage'],
  'missing_original_usage':state['missing_usage'],'unused_slots_expire':state['unused_slots_expire'],
  'scores':state['scores'],'full_control_strict':controls['full'],'no_memory_strict_reused':controls['none'],'no_memory_reuse_is_independent':False,'per_read':per_read,'read_disagreement':variation,'by_domain':domains,
  'failed_or_missing_cases':losses,'a8r_paired_cases':paired,'reported_usage_by_stage':{k:dict(v)for k,v in stages.items()},
  'new_model_calls':0,'new_extractions':0,'old43_scores_replaced':False,'generation_stability_verified':False,
  'method_causal_advantage_verified':False,'historical_baseline_comparison':comparison,'independent_semantic_acceptance':False,'production_default_changed':False}

def check(path=DEFAULT):
 path=Path(path);require(p.sha(path)==path.with_suffix('.sha256').read_text().strip(),'Snapshot checksum differs')
 return replay(p.read(path))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT)
 print(json.dumps(check(parser.parse_args().input),ensure_ascii=False,indent=2))
