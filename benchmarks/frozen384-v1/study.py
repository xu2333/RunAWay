"""New13-call frozen-card revalidation; never resumes the interrupted proposal."""
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
previous=load('frozen384_previous_study',HERE.parent/'long-trajectory-v1/study.py');oldcheck=load('frozen384_previous_check',HERE.parent/'long-trajectory-v1/check.py');h=previous.h;w=previous.w
CAP=13;MODEL='gpt-6-sol';GROUPS=['none','full','card','repeat']
read=previous.read;require=previous.require;sha=previous.sha;canonical=previous.canonical;digest=previous.digest;atomic=previous.atomic;write_once=previous.write_once


def plan():
 people=list(w.PEOPLE[1:])+[w.PEOPLE[0]];first=[['full' if i%2==0 else 'card',pid] for i,pid in enumerate(people)]
 return [['none','shared']]+first+[['card' if g=='full' else 'full',pid] for g,pid in reversed(first)]+[['repeat',pid] for pid in people[2:]+people[:2]]


def cards():
 data=read(HERE.parent/'long-trajectory-v1/observed.synthetic.json');oldcheck.validate(data);selected=data['products']['384'];require(set(selected)==set(w.PEOPLE),'All four cards required')
 for pid,bundle in selected.items():require(bundle==h.extractor.bind(bundle['profile.private.json']['answer'],w.fixtures()['histories'][pid],384),'Frozen card source binding')
 return selected


def request_for(f,group,pid,products):
 oldgroup='sol_none' if group=='none' else 'sol_full' if group=='full' else 'sol_384'
 request=previous.request_for(f,oldgroup,pid,{'384':products});require(request['model']==MODEL,'Requested model drift');return request


def source_names():
 return sorted(set(previous.source_names()+['benchmarks/long-trajectory-v1/check.py','benchmarks/long-trajectory-v1/observed.synthetic.json','benchmarks/frozen384-v1/study.py','tests/test_frozen384.py']))


def prepare(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);f=w.fixtures();products=cards();static={g+':'+pid:request_for(f,g,pid,products) for g,pid in plan()}
 for n,v in [('world.synthetic.json',f),('cards.synthetic.json',products),('static-requests.synthetic.json',static),('plan.json',plan())]:write_once(out/n,v)
 p={'kind':'frozen384_revalidation_v1','directory':str(out),'calls_max':CAP,'model':MODEL,'budget':384,'source_hashes':{n:sha(ROOT/n) for n in source_names()},'input_hashes':{n:sha(out/n) for n in ['world.synthetic.json','cards.synthetic.json','static-requests.synthetic.json','plan.json']},'runtime':h.runtime_metadata(),
 'authorization':'Current direct human: 继续验证. New synthetic-only13-call unit via existing Codex service. No prior unused balance, real-person data, retries or extractor calls.',
 'selection':'All four previously extracted384-budget cards, byte-identical production products. Budget/pool selected before new outcomes; not best-of card selection. One card had two completed old reads, explicitly not a fresh holdout. No old answer reused as a new draw.',
 'matrix':'13 physical executions: shared none1, full4, card4, repeat4. First wave alternates full/card across rotatedpeople; second wave uses complementary arms in reversepersonorder; repeats only after every person has both full/card. Requests are the unchanged standard production116question contracts, asof2026-09-30, shared absent-option instruction. Same requested model; resolved identity unavailable.',
 'quality':'Each arm160 planned person/scene cases43known117unknown; every cyclic position must match. New-study full qualifies only strict160/160,missing0,known(full-none)/43>=.25. Stable384 gate also requires both card/repeat strict160/160 withmissing0. Old longfull control cannot substitute for new full. Report missing cases, actual disagreements and every paired lost/recovered ID separately; repeated cases/personas are dependent, not population estimates.',
 'stop':'Exclusive intent. No resume, retry, repair, fallback, re-extraction, replacement person, deadline extension or replenishment. Transport/wire/schema/decode/unknownusage/binding failure stops all later calls. Valid quality errors do not stop fixed remaining slots. Old interrupted46slot proposal remains closed.',
 'limits':'Same four consumed synthetic policies and40derived scenes, not new people or independent holdout.90message histories deliberately redundant with6latest supported decisions/person. Tests current-state reconstruction, not all biography, latent-rule induction, real-person fidelity, cross-vendor or runtime-harness portability, likelihoodRIG, population confidence intervals or invoices. 13 is a call cap, not a token/money cap; previous failed usage stays unknown.'}
 p['id']=digest(canonical(p));write_once(out/'proposal.json',p);return p


def preflight(out):
 out=Path(out).resolve();p=read(out/'proposal.json');require(p['id']==digest(canonical({k:v for k,v in p.items() if k!='id'})),'Proposal checksum');require(p['directory']==str(out) and p['calls_max']==CAP and p['model']==MODEL and p['budget']==384,'Scope drift');require(set(p['source_hashes'])==set(source_names()),'Source inventory')
 for n,hsh in p['source_hashes'].items():require(sha(ROOT/n)==hsh,'Frozen source drift:'+n)
 for n,hsh in p['input_hashes'].items():require(sha(out/n)==hsh,'Input drift:'+n)
 f=read(out/'world.synthetic.json');products=read(out/'cards.synthetic.json');static=read(out/'static-requests.synthetic.json');require(f==w.fixtures() and products==cards() and read(out/'plan.json')==plan(),'World/card/plan reconstruction');require(static=={g+':'+pid:request_for(f,g,pid,products) for g,pid in plan()},'Exact request binding');return p,f,products,static


def analyze(f,raw):
 scores={};rejected={};decoded={}
 for group in GROUPS:
  answers={}
  for pid,value in raw.get(group,{}).items():
   try:labels=previous.decode(f,value)
   except ValueError as exc:rejected[group+':'+pid]={'error':str(exc),'raw_sha256':digest(canonical(value))};continue
   for target in (w.PEOPLE if group=='none' else [pid]):answers[target]=labels
  decoded[group]=answers;scores[group]=w.evaluate(f,answers)
 qualified=scores['full']['strict_choice_pass'] and (scores['full']['known']['correct']-scores['none']['known']['correct'])/43>=.25
 quality={'contemporaneous_full_qualified':qualified,'retention_interpretable':qualified,'stable384_pass':qualified and scores['card']['strict_choice_pass'] and scores['repeat']['strict_choice_pass']}
 pairs={}
 for left,right in [('full','card'),('full','repeat'),('card','repeat')]:
  le={(e['person'],e['case']) for e in scores[left]['errors']};re={(e['person'],e['case']) for e in scores[right]['errors']};delta={}
  for kind in ['known','unknown']:
   ids={(p,c['id']) for c in f['cases'] for p in w.PEOPLE if (c['gold'][p]!='U')==(kind=='known')};delta[kind]={'lost':sorted([list(x) for x in (re-le)&ids]),'recovered':sorted([list(x) for x in (le-re)&ids])}
  pairs[left+'->'+right]=delta
 disagreements=[]
 for case in f['cases']:
  for pid in w.PEOPLE:
   qids=[o['public']['id'] for o in case['orders']]
   if all(q in decoded[g].get(pid,{}) for g in ['card','repeat'] for q in qids) and any(decoded['card'][pid][q]!=decoded['repeat'][pid][q] for q in qids):disagreements.append({'person':pid,'case':case['id'],'gold':case['gold'][pid],'card':[decoded['card'][pid][q] for q in qids],'repeat':[decoded['repeat'][pid][q] for q in qids]})
 return {'groups':scores,'quality':quality,'paired_losses':pairs,'repeat_disagreements':disagreements,'rejected_answers':rejected,'real_person_fidelity_verified':False}


def execute(out,backend=None):
 out=Path(out).resolve();p,f,products,static=preflight(out);real=backend is None
 if real:
  acceptance=read(out/'offline-acceptance.json');require(acceptance['passed'] and acceptance['proposal_id']==p['id'] and acceptance['model_calls']==0,'Offline acceptance');require(h.runtime_metadata()==p['runtime'],'Runtime drift')
 with (out/'service-intent.json').open('x') as stream:json.dump({'proposal_id':p['id'],'calls_max':CAP,'human_source':p['authorization'],'real_service':real},stream);stream.flush();os.fsync(stream.fileno())
 service=out/'service';service.mkdir();raw={};completed=[];stop=None
 def guard():require(preflight(out)[0]['id']==p['id'] and len(h.records_checked(service))<CAP,'Binding/globalcap')
 config={'calls_max':CAP,'stage_caps':{g:sum(a==g for a,pid in plan()) for g in GROUPS},'models':{'reader':MODEL,'generator':MODEL},'forbidden_request_ids':[]};by_group={}
 for group in GROUPS:
  folder=service/group;folder.mkdir();by_group[group]=h.StrictCalls(folder,config,backend or h.generation.codex_generate,guard)
 for group,pid in plan():
  calls=by_group[group]
  try:
   request=static[group+':'+pid]
   with patch.object(h.fr,'SYSTEM',request['system']),patch.object(h.generation,'run_bounded',calls.observed_runner):value=calls.call(group,request)
   raw.setdefault(group,{})[pid]=value;atomic(service/'answers.synthetic.json',raw);completed.append([group,pid]);atomic(service/'completed-plan.json',completed);h.validate_wire(value,request['schema']);previous.decode(f,value)
   print(json.dumps({'group':group,'person':pid,'actual_calls':len(h.records_checked(service))}),flush=True)
  except Exception as exc:
   if not calls.stopped:calls.stop('wire_or_local_validation_failure',error_type=type(exc).__name__,error=str(exc))
   stop={'group':group,'person':pid,'reason':calls.reason};break
 try:ledger=h.summarize(h.records_checked(service))
 except Exception as exc:ledger={'integrity_uncertain':True,'known_usage':None,'error_type':type(exc).__name__};stop=stop or {'reason':'ledger_integrity_uncertain'}
 result={'status':'stopped' if stop else 'complete','proposal_id':p['id'],'backend_kind':'actual_codex_service' if real else 'injected_fake_not_model_evidence','ledger':ledger,'stop_reason':stop,'completed_plan':completed,**analyze(f,raw)};write_once(service/'report.json',result);return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','run']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();value=prepare(args.out) if args.action=='prepare' else preflight(args.out)[0] if args.action=='preflight' else execute(args.out);print(json.dumps({k:value[k] for k in ['id','status','ledger'] if k in value}))
