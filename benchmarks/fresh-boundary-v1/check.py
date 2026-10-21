"""Reproduce the recorded fresh synthetic pilot without service calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fresh_boundary_record_study',HERE/'study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from runaway.card import canonical,digest
from runaway.execution_ledger import summarize,usage


def validate(data):
 require=s.require;require(data['backend_kind'] in ('actual_codex_service','injected_fake_not_model_evidence'),'Unknown backend kind');real=data['backend_kind']=='actual_codex_service';f=s.w.fixtures();require(data['synthetic'] is True and data['world']==f,'Synthetic fixture differs');require(data['calls_max']==56 and data['planned_slots']==s.plan(),'Fixed plan differs')
 raw=data['raw_answers'];groups={g for g,p in s.plan()};require(not set(raw)-groups,'Unknown response group');products={};invalid={}
 for pid,value in raw.get('extraction',{}).items():
  require(pid in s.w.PEOPLE,'Unknown extractor person')
  try:s.validate_wire(value,s.extractor.SCHEMA)
  except ValueError:continue
  try:products[pid]=s.extractor.bind(value,f['histories'][pid],s.BUDGET)
  except ValueError as exc:invalid[pid]={'error':str(exc),'no_repair':True}
 require(invalid==data['invalid_products'],'Invalid products differ');require(products==data['products'],'Production source/anchor/budget binding differs')
 executions=data['executions'];require(len(executions)<=56 and len({r['execution_id'] for r in executions})==len(executions),'Execution identities/cap differ')
 actual={(r['group'],r['person']):r for r in executions};require(len(actual)==len(executions),'Duplicate slot execution')
 skipped=[];completed=[];seen=[];failure=False
 for group,pid in s.plan():
  arm=s.descriptor(group)[2];donor=pid if arm=='own' else f['donors'].get(pid)
  if arm in ('own','wrong') and donor not in products:
   if not failure:skipped.append([group,pid,'invalid_or_missing_extraction:'+str(donor)])
   continue
  record=actual.get((group,pid))
  if record is None:failure=True;continue
  require(not failure,'Execution after a missing/failed slot');seen.append([group,pid]);request=s.request_for(f,group,pid,products);require(record['request_id']==digest(canonical(request)),'Exact request binding differs')
  if record['outcome']=='completed':
   require(usage(record['provenance'])==record['usage'],'Provenance usage differs')
   if real:require(record['provenance'].get('backend')=='codex' and record['provenance'].get('model_requested')==request['model'],'Requested model provenance differs')
   require(group in raw and pid in raw[group],'Missing raw response');answer=raw[group][pid];require(record['answer_sha256']==digest(canonical(answer)),'Answer binding differs')
   body={'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']};require(digest(canonical(body))==record['result_checkpoint_sha256'],'Original checkpoint binding differs')
   completed.append([group,pid])
   try:s.validate_wire(answer,request['schema'])
   except ValueError:failure=True
  else:failure=True
 require(set(actual)=={tuple(slot) for slot in seen},'Unplanned execution');require(completed==data['completed_plan'] and skipped==data['skipped'],'Completion/skip order differs')
 require({(g,p) for g,people in raw.items() for p in people}=={tuple(slot) for slot in completed},'Unbound extra answer')
 ledger=summarize(executions);require(ledger==data['ledger'],'Ledger differs');analysis=s.analyze(f,raw);require(analysis==data['analysis'],'Scores or qualification differ')
 complete=len(completed)+len(skipped)==56 and not failure
 require((data['status']=='complete')==(complete and not invalid),'Completion claim differs')
 require((data['status']=='completed_with_invalid_products')==(complete and bool(invalid)),'Invalid product completion differs')
 if not complete:require(data['status']=='stopped' and data['stop_reason'] is not None,'Stopped run must remain stopped')
 return {'passed':True,'actual_calls':len(executions) if real else 0,'recorded_executions':len(executions),'backend_kind':data['backend_kind'],'unique_request_fingerprints':len({r['request_id'] for r in executions}),'groups_reproduced':len(analysis['groups']),'cases_per_arm':128,'known':40,'unknown':88,'unobserved_domain_unknowns':64,'quality':analysis['quality'],'model_calls':0,'real_person_fidelity_verified':False}


def verify_exports(data):
 for pid,bundle in data['products'].items():s.require(s.read(HERE/'cards'/(pid+'.portable.json'))==bundle['portable.json'],'Portable card export differs')
 frontier=s.read(HERE/'packing-frontier.synthetic.json');s.require(frontier['posthoc_offline_only'] is True and frontier['model_calls']==0 and frontier['behavior_at_smaller_budgets_tested'] is False,'Packing claim differs')
 s.require(frontier['budgets']==[768,512,400,384,320,300],'Packing budgets differ');expected={}
 for pid,bundle in data['products'].items():
  expected[pid]={}
  for budget in frontier['budgets']:
   try:
    packed=s.extractor.bind(bundle['profile.private.json']['answer'],data['world']['histories'][pid],budget);summary=packed['summary.private.json'];expected[pid][str(budget)]={'status':'fits','characters':len(packed['prompt.md']),'dictionary_entries':summary['dictionary_entries'],'roundtrip_exact':summary['roundtrip_exact'],'prompt_sha256':digest(packed['prompt.md'])}
   except ValueError as exc:expected[pid][str(budget)]={'status':'rejected','error':str(exc)}
 s.require(frontier['profiles']==expected,'Post-hoc packing results differ')
 return {'portable_cards_verified':len(data['products']),'posthoc_budgets_verified':6,'smaller_budget_behavior_verified':False}


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'observed.synthetic.json');args=parser.parse_args()
 try:
  data=s.read(args.data);print(json.dumps({**validate(data),**verify_exports(data)},ensure_ascii=False,indent=2))
 except (ValueError,TypeError,KeyError,OSError) as exc:parser.exit(2,str(exc)+'\n')
