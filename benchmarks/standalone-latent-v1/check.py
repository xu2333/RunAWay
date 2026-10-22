"""Offline reconstruction of the standalone decoder-removal19-slot study."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('standalone_latent_record_study',HERE/'study.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
from runaway.execution_ledger import summarize,usage


def validate(data):
 require=s.require;require(data['backend_kind'] in ('actual_codex_service','injected_fake_not_model_evidence'),'Unknown backend kind');real=data['backend_kind']=='actual_codex_service';f=s.w.fixtures();require(data['synthetic'] is True and data['world']==f,'Synthetic fixture differs');require(data['calls_max']==19 and data['planned_slots']==s.plan(),'Fixed plan differs');require(data['products']==s.cards(),'Frozen products differ')
 raw=data['raw_answers'];require(not set(raw)-set(s.GROUPS),'Unknown response group');executions=data['executions'];require(len(executions)<=19 and len({r['execution_id'] for r in executions})==len(executions),'Execution identities/cap differ');actual={(r['group'],r['person']):r for r in executions};require(len(actual)==len(executions),'Duplicate slot execution');completed=[];seen=[];failure=False
 for group,pid in s.plan():
  record=actual.get((group,pid))
  if record is None:failure=True;continue
  require(not failure,'Execution after a missing/failed slot');seen.append([group,pid]);request=s.request_for(f,group,pid,data['products']);require(record['request_id']==s.digest(s.canonical(request)),'Exact request binding differs')
  if record['outcome']=='completed':
   require(usage(record['provenance'])==record['usage'],'Provenance usage differs')
   if real:require(record['provenance'].get('backend')=='codex' and record['provenance'].get('model_requested')==s.MODEL,'Requested model provenance differs')
   require(group in raw and pid in raw[group],'Missing raw response');answer=raw[group][pid];require(record['answer_sha256']==s.digest(s.canonical(answer)),'Answer binding differs');body={'answer':answer,'provenance':record['provenance'],'request_id':record['request_id'],'execution_id':record['execution_id']};require(s.digest(s.canonical(body))==record['result_checkpoint_sha256'],'Original checkpoint binding differs');completed.append([group,pid])
   try:s.h.validate_wire(answer,request['schema']);s.base.decode(f,answer)
   except ValueError:failure=True
  else:
   require(record['outcome']=='failed','Unknown execution outcome');checkpoint=data['failure_checkpoints'][record['execution_id']];require(checkpoint['sha256']==s.digest(s.canonical({k:v for k,v in checkpoint.items() if k!='sha256'}))==record['result_checkpoint_sha256'],'Failed checkpoint binding differs');require(checkpoint['request_id']==record['request_id'] and checkpoint['execution_id']==record['execution_id'] and checkpoint['provenance']==record['provenance'],'Failed checkpoint identity/provenance differs');require(usage(checkpoint['provenance'])==record['usage'],'Failed usage differs');failure=True
 require(set(data['failure_checkpoints'])=={r['execution_id'] for r in executions if r['outcome']=='failed'},'Failure checkpoint inventory differs');require(set(actual)=={tuple(slot) for slot in seen},'Unplanned execution');require(completed==data['completed_plan'],'Completion order differs');require({(g,p) for g,people in raw.items() for p in people}=={tuple(slot) for slot in completed},'Unbound extra answer');require(summarize(executions)==data['ledger'],'Ledger differs');analysis=s.analyze(f,raw);require(analysis==data['analysis'],'Scores or qualification differ');complete=len(completed)==19 and not failure;require((data['status']=='complete')==complete,'Completion claim differs')
 if not complete:require(data['status']=='stopped' and data['stop_reason'] is not None,'Stopped run must remain stopped')
 return {'passed':True,'actual_calls':len(executions) if real else 0,'recorded_executions':len(executions),'backend_kind':data['backend_kind'],'unique_request_fingerprints':len({r['request_id'] for r in executions}),'groups_reproduced':4,'cases_per_arm':102,'known':55,'unknown':47,'quality':analysis['quality'],'donor_repeat_disagreements':len(analysis['donor_repeat_disagreements']),'model_calls':0,'real_person_fidelity_verified':False}


def verify_exports(data):
 for pid,bundle in data['products'].items():s.require(s.read(HERE.parent/'latent-transfer-v1/cards'/(pid+'.portable.json'))==bundle['portable.json'],'Original portable card differs')
 observations=data['guard_observations'];s.require([x['before_call'] for x in observations]==list(range(1,len(data['executions'])+1)),'Guard observation order/count differs');s.require(all(x['owned_active'] and x['platform']=='Darwin' and x['owner_pids'] for x in observations),'Owned guard missing');s.require(data['execution_guard']['wrapper_sha256']==s.sha(HERE.parents[1]/'scripts/with_awake.py') and data['execution_guard']['active_deadline_seconds']==180,'Guard source/deadline differs')
 old=s.read(HERE.parent/'latent-transfer-v1/observed.synthetic.json');s.require(data['prior_shared_decoder_ledger']==old['ledger'] and old['ledger']['execution_records']==31 and data['injected_decoder_characters']==0,'Prior/removed-decoder metadata differs')
 return {'unchanged_portable_cards_verified':len(data['products']),'owned_guard_observations_verified':len(observations),'injected_decoder_characters':0,'prior_actual_calls':31,'combined_actual_calls':31+len(data['executions'])}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'observed.synthetic.json');args=parser.parse_args()
 try:
  data=s.read(args.data);print(json.dumps({**validate(data),**verify_exports(data)},ensure_ascii=False,indent=2))
 except (ValueError,TypeError,KeyError,OSError) as exc:parser.exit(2,str(exc)+'\n')
