"""New19-call removal ablation; prior31-slot codebook study stays closed."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
base=load('standalone_latent_base',HERE.parent/'latent-transfer-v1/study.py');w=base.w;h=base.h;shared=base.shared
read=base.read;require=base.require;sha=base.sha;canonical=base.canonical;digest=base.digest;atomic=base.atomic;write_once=base.write_once
CAP=19;MODEL=base.MODEL;GROUPS=['none','full','own','wrong']


def plan():
 people=list(w.PEOPLE[1:])+[w.PEOPLE[0]];first=[['full' if i%2==0 else 'own',pid] for i,pid in enumerate(people)]
 return [['none','shared']]+first+[['own' if g=='full' else 'full',pid] for g,pid in reversed(first)]+[['wrong',pid] for pid in people[2:]+people[:2]]


def cards():
 old=read(HERE.parent/'latent-transfer-v1/observed.synthetic.json');products=old['products'];require(set(products)==set(w.PEOPLE),'All six original cards required')
 for pid,bundle in products.items():require(bundle==h.extractor.bind(bundle['profile.private.json']['answer'],w.fixtures()['histories'][pid],512),'Original production card binding')
 return products


def request_for(f,group,pid,products):
 request=base.request_for(f,group,pid,products);require(request['prompt'].startswith(f['decoder_contract']),'Decoder removal binding');return dict(request,prompt=request['prompt'][len(f['decoder_contract']):])


def source_names():return sorted(set(base.source_names()+['benchmarks/latent-transfer-v1/observed.synthetic.json','benchmarks/standalone-latent-v1/study.py','tests/test_standalone_latent.py']))


def prepare(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);f=w.fixtures();products=cards();static={g+':'+pid:request_for(f,g,pid,products) for g,pid in plan()}
 for n,v in [('world.synthetic.json',f),('cards.synthetic.json',products),('static-requests.synthetic.json',static),('plan.json',plan())]:write_once(out/n,v)
 p={'kind':'standalone_latent_codebook_removal_v1','directory':str(out),'calls_max':CAP,'model':MODEL,'source_hashes':{n:sha(ROOT/n) for n in source_names()},'input_hashes':{n:sha(out/n) for n in ['world.synthetic.json','cards.synthetic.json','static-requests.synthetic.json','plan.json']},'runtime':h.runtime_metadata(),'execution_guard':{'required':'owned macOS idle-sleep assertion before every invocation','wrapper_sha256':sha(ROOT/'scripts/with_awake.py'),'active_deadline_seconds':180,'permanent_settings_changed':False},
 'authorization':'Current human: 继续推进. Separately announced19-call ablation after completed31-call shared-decoder study; combined ceiling50physical calls this continuation. Synthetic-only selected inputs, no old slot balance, re-extraction, repair or retry.',
 'selection':'All six original512-budget products (actual296–387chars), not best-of selection. Same consumed17scenes/102cases/34questions and all gold. New intervention removes exactly619prefixcharacters from every reader request; all other request fields remain equal. Full source histories retain their original user-stated rule definitions; cards do not receive an appended decoder. A common absent-option instruction remains, so this is production request builder plus that generic instruction, not an assertion that every CLI default was tested.',
 'matrix':'none1+full6+own6+wrong6=19physical calls,13unique inputs expected. Two interleaved full/own waves across every person, then wrong-person donor repeats. Same requestedgpt-6-sol, no resolved identity. Earlier31responses are not reused as new outputs and their positive conditioned result remains public.',
 'quality':'Contemporary full must pass all102cases and positions withmissing0,personal-known(full-none)/43>=.25 before standalone retention is interpretable. Standalone gate additionally requires own and wrong-against-donor reads102/102. Identity specificity requires lower wrong-target personal-known than own. No best-draw or per-person selection. Report all paired losses and missing denominators; if full fails, do not attribute all card-minus-full differences to compression.',
 'stop':'Single use; no resume/retry/repair/deadline extension/replacement/re-extraction/fallback/replenishment. Transport, schema/decode, unknownusage, source/guard/binding failure stops all later calls. Valid quality errors do not stop otherwise valid fixed remaining slots. Earlier31-slot proposal is closed.',
 'limits':'Sequential, exploratory removal ablation on a consumed synthetic finite-family corpus, not independent external holdout or randomized causal estimate; sampling/service drift is not eliminated. Gold uses original source-stated family assumptions. The12family-invariant known cases are not free shared-decoder knowledge in this condition; only full history actually contains its definitions. The old59/102 uninformed reference does not apply here as a protocol/accuracy ceiling. No human fidelity, naturalistic trait inference, newpopulation accuracy, cross-vendor/runtime-harness portability, likelihoodRIG or invoice claim.19is a call cap, not a token/money cap.'}
 p['id']=digest(canonical(p));write_once(out/'proposal.json',p);return p


def preflight(out):
 out=Path(out).resolve();p=read(out/'proposal.json');require(p['id']==digest(canonical({k:v for k,v in p.items() if k!='id'})),'Proposal checksum');require(p['directory']==str(out) and p['calls_max']==CAP and p['model']==MODEL,'Scope drift');require(set(p['source_hashes'])==set(source_names()),'Source inventory')
 for n,hsh in p['source_hashes'].items():require(sha(ROOT/n)==hsh,'Frozen source drift:'+n)
 for n,hsh in p['input_hashes'].items():require(sha(out/n)==hsh,'Input drift:'+n)
 f=read(out/'world.synthetic.json');products=read(out/'cards.synthetic.json');static=read(out/'static-requests.synthetic.json');require(f==w.fixtures() and products==cards() and read(out/'plan.json')==plan(),'World/cards/plan reconstruction');require(static=={g+':'+pid:request_for(f,g,pid,products) for g,pid in plan()},'Exact removed-prefix binding');return p,f,products,static


def analyze(f,raw):
 a=base.analyze(f,raw);a['groups'].pop('tail');a['paired_losses']={k:v for k,v in a['paired_losses'].items() if 'tail' not in k};a['quality']['standalone_gate']=a['quality'].pop('strict_transport_pass');return a


def execute(out,backend=None):
 out=Path(out).resolve();p,f,products,static=preflight(out);real=backend is None
 if real:
  require(shared.guard_status()['owned_active'],'Owned idle-sleep guard required');acceptance=read(out/'offline-acceptance.json');require(acceptance['passed'] and acceptance['proposal_id']==p['id'] and acceptance['model_calls']==0,'Offline acceptance');require(h.runtime_metadata()==p['runtime'],'Runtime drift')
 with (out/'service-intent.json').open('x') as stream:json.dump({'proposal_id':p['id'],'calls_max':CAP,'human_source':p['authorization'],'real_service':real},stream);stream.flush();os.fsync(stream.fileno())
 service=out/'service';service.mkdir();raw={};completed=[];stop=None
 def guard():
  require(preflight(out)[0]['id']==p['id'] and len(h.records_checked(service))<CAP,'Binding/globalcap')
  if real:
   observation=shared.guard_status();require(observation['owned_active'],'Owned guard disappeared');observation['before_call']=len(h.records_checked(service))+1;path=out/'guard-observations.json';rows=read(path) if path.exists() else [];rows.append(observation);atomic(path,rows)
 by_group={}
 for group in GROUPS:
  folder=service/group;folder.mkdir();cap=sum(g==group for g,pid in plan());by_group[group]=h.StrictCalls(folder,{'calls_max':cap,'stage_caps':{group:cap},'models':{'reader':MODEL,'generator':MODEL},'forbidden_request_ids':[]},backend or h.generation.codex_generate,guard)
 for group,pid in plan():
  calls=by_group[group]
  try:
   request=static[group+':'+pid]
   with patch.object(h.fr,'SYSTEM',request['system']),patch.object(h.generation,'run_bounded',calls.observed_runner):value=calls.call(group,request)
   raw.setdefault(group,{})[pid]=value;atomic(service/'answers.synthetic.json',raw);completed.append([group,pid]);atomic(service/'completed-plan.json',completed);h.validate_wire(value,request['schema']);base.decode(f,value);print(json.dumps({'group':group,'person':pid,'actual_calls':len(h.records_checked(service))}),flush=True)
  except Exception as exc:
   if not calls.stopped:calls.stop('wire_or_local_validation_failure',error_type=type(exc).__name__,error=str(exc))
   stop={'group':group,'person':pid,'reason':calls.reason};break
 try:ledger=h.summarize(h.records_checked(service))
 except Exception as exc:ledger={'integrity_uncertain':True,'known_usage':None,'error_type':type(exc).__name__};stop=stop or {'reason':'ledger_integrity_uncertain'}
 result={'status':'stopped' if stop else 'complete','proposal_id':p['id'],'backend_kind':'actual_codex_service' if real else 'injected_fake_not_model_evidence','ledger':ledger,'stop_reason':stop,'completed_plan':completed,**analyze(f,raw)};write_once(service/'report.json',result);return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','run']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();value=prepare(args.out) if args.action=='prepare' else preflight(args.out)[0] if args.action=='preflight' else execute(args.out);print(json.dumps({k:value[k] for k in ['id','status','ledger'] if k in value}))
