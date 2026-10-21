"""Reproduce the recorded long-history budget pilot without service calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('long_history_record_study',HERE/'study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from runaway.card import canonical,digest
from runaway.execution_ledger import summarize,usage


def validate(data):
 require=s.require;require(data['backend_kind'] in ('actual_codex_service','injected_fake_not_model_evidence'),'Unknown backend kind');real=data['backend_kind']=='actual_codex_service';f=s.w.fixtures();require(data['synthetic'] is True and data['world']==f,'Synthetic fixture differs');require(data['calls_max']==46 and data['planned_slots']==s.plan(),'Fixed plan differs')
 raw=data['raw_answers'];groups={g for g,p in s.plan()};require(not set(raw)-groups,'Unknown response group');products={};invalid={}
 for group,people in raw.items():
  prefix,arm,budget=s.descriptor(group)
  if arm!='extraction':continue
  for pid,value in people.items():
   require(pid in s.w.PEOPLE,'Unknown extractor person')
   try:s.h.validate_wire(value,s.h.extractor.SCHEMA)
   except ValueError:continue
   try:products.setdefault(str(budget),{})[pid]=s.h.extractor.bind(value,f['histories'][pid],budget)
   except ValueError as exc:invalid[str(budget)+':'+pid]={'error':str(exc),'no_repair':True}
 require(invalid==data['invalid_products'],'Invalid products differ');require(products==data['products'],'Production source/anchor/budget binding differs')
 executions=data['executions'];require(len(executions)<=46 and len({r['execution_id'] for r in executions})==len(executions),'Execution identities/cap differ')
 actual={(r['group'],r['person']):r for r in executions};require(len(actual)==len(executions),'Duplicate slot execution')
 skipped=[];completed=[];seen=[];failure=False
 for group,pid in s.plan():
  prefix,arm,budget=s.descriptor(group)
  if arm=='own' and pid not in products.get(str(budget),{}):
   if not failure:skipped.append([group,pid,'invalid_or_missing_extraction:'+str(budget)+':'+pid])
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
   try:
    s.h.validate_wire(answer,request['schema'])
    if arm!='extraction':s.decode(f,answer)
   except ValueError:failure=True
  else:
   checkpoint=data['failure_checkpoints'][record['execution_id']]
   require(checkpoint['sha256']==digest(canonical({k:v for k,v in checkpoint.items() if k!='sha256'}))==record['result_checkpoint_sha256'],'Failed checkpoint binding differs')
   require(checkpoint['request_id']==record['request_id'] and checkpoint['execution_id']==record['execution_id'] and checkpoint['provenance']==record['provenance'],'Failed checkpoint identity/provenance differs')
   require(usage(checkpoint['provenance'])==record['usage'],'Failed usage differs');failure=True
 require(set(data['failure_checkpoints'])=={r['execution_id'] for r in executions if r['outcome']=='failed'},'Failure checkpoint inventory differs')
 require(set(actual)=={tuple(slot) for slot in seen},'Unplanned execution');require(completed==data['completed_plan'] and skipped==data['skipped'],'Completion/skip order differs')
 require({(g,p) for g,people in raw.items() for p in people}=={tuple(slot) for slot in completed},'Unbound extra answer')
 ledger=summarize(executions);require(ledger==data['ledger'],'Ledger differs');analysis=s.analyze(f,raw);require(analysis==data['analysis'],'Scores or qualification differ')
 complete=len(completed)+len(skipped)==46 and not failure
 require((data['status']=='complete')==(complete and not invalid),'Completion claim differs')
 require((data['status']=='completed_with_invalid_products')==(complete and bool(invalid)),'Invalid product completion differs')
 if not complete:require(data['status']=='stopped' and data['stop_reason'] is not None,'Stopped run must remain stopped')
 return {'passed':True,'actual_calls':len(executions) if real else 0,'recorded_executions':len(executions),'backend_kind':data['backend_kind'],'unique_request_fingerprints':len({r['request_id'] for r in executions}),'groups_reproduced':len(analysis['groups']),'cases_per_arm':160,'known':43,'unknown':117,'unobserved_domain_unknowns':80,'quality':analysis['quality'],'model_calls':0,'real_person_fidelity_verified':False}



def verify_exports(data):
 count=0
 for budget,people in data['products'].items():
  for pid,bundle in people.items():
   s.require(s.read(HERE/'cards'/(pid+'-'+budget+'.portable.json'))==bundle['portable.json'],'Portable card export differs');count+=1
 return {'portable_cards_verified':count}


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'observed.synthetic.json');args=parser.parse_args()
 try:
  data=s.read(args.data);print(json.dumps({**validate(data),**verify_exports(data)},ensure_ascii=False,indent=2))
 except (ValueError,TypeError,KeyError,OSError) as exc:parser.exit(2,str(exc)+'\n')
