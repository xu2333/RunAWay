"""Offline reconstruction of the new13-slot frozen-card study."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen384_record_study',HERE/'study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from runaway.execution_ledger import summarize,usage


def validate(data):
 require=s.require;require(data['backend_kind'] in ('actual_codex_service','injected_fake_not_model_evidence'),'Unknown backend kind');real=data['backend_kind']=='actual_codex_service';f=s.w.fixtures();require(data['synthetic'] is True and data['world']==f,'Synthetic fixture differs');require(data['calls_max']==13 and data['planned_slots']==s.plan(),'Fixed plan differs');require(data['products']==s.cards(),'Frozen products differ')
 raw=data['raw_answers'];require(not set(raw)-set(s.GROUPS),'Unknown response group');executions=data['executions'];require(len(executions)<=13 and len({r['execution_id'] for r in executions})==len(executions),'Execution identities/cap differ');actual={(r['group'],r['person']):r for r in executions};require(len(actual)==len(executions),'Duplicate slot execution');completed=[];seen=[];failure=False
 for group,pid in s.plan():
  record=actual.get((group,pid))
  if record is None:failure=True;continue
  require(not failure,'Execution after a missing/failed slot');seen.append([group,pid]);request=s.request_for(f,group,pid,data['products']);require(record['request_id']==s.digest(s.canonical(request)),'Exact request binding differs')
  if record['outcome']=='completed':
   require(usage(record['provenance'])==record['usage'],'Provenance usage differs')
   if real:require(record['provenance'].get('backend')=='codex' and record['provenance'].get('model_requested')==s.MODEL,'Requested model provenance differs')
   require(group in raw and pid in raw[group],'Missing raw response');answer=raw[group][pid];require(record['answer_sha256']==s.digest(s.canonical(answer)),'Answer binding differs');body={'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']};require(s.digest(s.canonical(body))==record['result_checkpoint_sha256'],'Original checkpoint binding differs');completed.append([group,pid])
   try:s.h.validate_wire(answer,request['schema']);s.previous.decode(f,answer)
   except ValueError:failure=True
  else:
   require(record['outcome']=='failed','Unknown execution outcome');checkpoint=data['failure_checkpoints'][record['execution_id']];require(checkpoint['sha256']==s.digest(s.canonical({k:v for k,v in checkpoint.items() if k!='sha256'}))==record['result_checkpoint_sha256'],'Failed checkpoint binding differs');require(checkpoint['request_id']==record['request_id'] and checkpoint['execution_id']==record['execution_id'] and checkpoint['provenance']==record['provenance'],'Failed checkpoint identity/provenance differs');require(usage(checkpoint['provenance'])==record['usage'],'Failed usage differs');failure=True
 require(set(data['failure_checkpoints'])=={r['execution_id'] for r in executions if r['outcome']=='failed'},'Failure checkpoint inventory differs');require(set(actual)=={tuple(slot) for slot in seen},'Unplanned execution');require(completed==data['completed_plan'],'Completion order differs');require({(g,p) for g,people in raw.items() for p in people}=={tuple(slot) for slot in completed},'Unbound extra answer');require(summarize(executions)==data['ledger'],'Ledger differs');analysis=s.analyze(f,raw);require(analysis==data['analysis'],'Scores or qualification differ');complete=len(completed)==13 and not failure;require((data['status']=='complete')==complete,'Completion claim differs')
 if not complete:require(data['status']=='stopped' and data['stop_reason'] is not None,'Stopped run must remain stopped')
 return {'passed':True,'actual_calls':len(executions) if real else 0,'recorded_executions':len(executions),'backend_kind':data['backend_kind'],'unique_request_fingerprints':len({r['request_id'] for r in executions}),'groups_reproduced':4,'cases_per_arm':160,'known':43,'unknown':117,'quality':analysis['quality'],'repeat_disagreements':len(analysis['repeat_disagreements']),'model_calls':0,'real_person_fidelity_verified':False}


def verify_exports(data):
 for pid,bundle in data['products'].items():s.require(s.read(HERE.parent/'long-trajectory-v1/cards'/(pid+'-384.portable.json'))==bundle['portable.json'],'Original portable export differs')
 audit=s.read(HERE/'awake-guard-audit.json');s.require(audit['passed'] and audit['model_calls']==0 and audit['applied_to_recorded_model_calls'] is False and audit['released_after_command'] and audit['child_exit_code_preserved']==7,'Awake audit claim differs');s.require(audit['wrapper_sha256']==s.sha(HERE.parents[1]/'scripts/with_awake.py'),'Audited wrapper source differs')
 observation=s.read(HERE/'host-sleep-observation.json');failed=[r for r in data['executions'] if r['outcome']=='failed'];s.require(len(failed)==1 and failed[0]['provenance']['elapsed_seconds']==observation['failure_active_elapsed_seconds'] and failed[0]['provenance']['wall_elapsed_seconds']==observation['failure_wall_elapsed_seconds'],'Sleep observation failure timing differs')
 return {'unchanged_portable_cards_verified':len(data['products']),'audited_awake_wrapper_verified':True}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'observed.synthetic.json');args=parser.parse_args()
 try:
  data=s.read(args.data);print(json.dumps({**validate(data),**verify_exports(data)},ensure_ascii=False,indent=2))
 except (ValueError,TypeError,KeyError,OSError) as exc:parser.exit(2,str(exc)+'\n')
