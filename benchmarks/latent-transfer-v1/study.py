"""Fixed31-call finite-family transfer through source-only production extraction."""
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
w=load('latent_transfer_world',HERE/'world.py');shared=load('latent_transfer_helpers',HERE.parent/'guarded384-v1/study.py');h=shared.h
read=shared.read;require=shared.require;sha=shared.sha;canonical=shared.canonical;digest=shared.digest;atomic=shared.atomic;write_once=shared.write_once
CAP=31;BUDGET=512;MODEL='gpt-6-sol';AS_OF='2026-10-21';GROUPS=['none','full','extraction','own','tail','wrong']
TAIL_NOTE='原始多角色记录尾部，开头可能被截断；只把完整标明user的决定作为证据。\n'


def plan():return [['none','shared']]+[['full',p] for p in w.PEOPLE]+[['extraction',p] for p in w.PEOPLE]+[['own',p] for p in reversed(w.PEOPLE)]+[['tail',p] for p in w.PEOPLE]+[['wrong',p] for p in list(w.PEOPLE[2:])+list(w.PEOPLE[:2])]


def raw_tail(f,pid,characters):
 require(characters>len(TAIL_NOTE),'Raw suffix budget too small');raw='\n'.join(row['role']+': '+row['text'] for row in f['histories'][pid]['sources']);return TAIL_NOTE+raw[-(characters-len(TAIL_NOTE)):]


def request_for(f,group,pid,products):
 if group=='extraction':return {'system':h.extractor.SYSTEM,'model':MODEL,**h.extractor.make_request(f['histories'][pid],BUDGET)}
 if group=='none':material=''
 elif group=='full':material=canonical(f['histories'][pid])
 elif group=='tail':material=raw_tail(f,pid,len(products[pid]['prompt.md']))
 else:material=products[f['donors'][pid] if group=='wrong' else pid]['prompt.md']
 request=h.reader.make_request(material,f['queries'],as_of=AS_OF,answer_format='text',reader_mode='standard');return {'system':h.extractor.SYSTEM,'model':MODEL,**request,'prompt':f['decoder_contract']+h.COMMON+request['prompt']}


def source_names():return sorted(set(shared.source_names()+['benchmarks/latent-transfer-v1/world.py','benchmarks/latent-transfer-v1/study.py','tests/test_latent_transfer.py']))


def prepare(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);f=w.fixtures();static={g+':'+p:request_for(f,g,p,{}) for g,p in plan() if g in ['none','full','extraction']}
 for n,v in [('world.synthetic.json',f),('static-requests.synthetic.json',static),('plan.json',plan())]:write_once(out/n,v)
 p={'kind':'new_people_identifiable_rule_transfer_v1','directory':str(out),'calls_max':CAP,'model':MODEL,'budget':BUDGET,'source_hashes':{n:sha(ROOT/n) for n in source_names()},'input_hashes':{n:sha(out/n) for n in ['world.synthetic.json','static-requests.synthetic.json','plan.json']},'runtime':h.runtime_metadata(),'execution_guard':{'required':'owned macOS idle-sleep assertion before intent and every call','wrapper_sha256':sha(ROOT/'scripts/with_awake.py'),'active_deadline_seconds':180,'permanent_settings_changed':False},
 'authorization':'Current direct human: 继续推进. New synthetic-only31-call ceiling through existing Codex service; no old unused balance, human/PRISM data, retries or additional encoder draws.',
 'design':'6new authored synthetic profiles,3effective observed decisions each,8public candidate rules over3binary features.4unique version spaces and2ambiguous pairs; gold marginalizes all compatible rules, never the unrecoverable hidden author rule. Independent hand truth64entries/version-space6/scenario102checks.17scenes/34rotatedqueries/person=102cases,55known47unknown,43personal-known12structural-known. Heldout-combination30cases=26known4unknown; only14ofitsknowns require personal memory. Closed family/feature vocabulary and domain assumptions are public, not inferred universal human traits.',
 'matrix':'none1/full6/source-onlyproductionextraction6/own6/character-matched-role-labelled-raw-tail6/wrong-person6=31physical calls. Wrong-person inputs equal donor own inputs and create independent execution identities; donor-gold repeat is also reported. One extraction/person at512wholeUnicodecharacters. Same619-character shared decoder contract for every reader, standard request builder plus fixed public finite-family inference/absent-option instructions. Encoder sees only own source history with common rule definitions and observations, never evaluation queries/gold/author policy. Raw tail length matches that person actual card, including fixed fragment warning; character-matched, NOT token-matched. Report decoder overhead separately.',
 'quality':'New contemporary full qualifies only all102cases/allpositions correct,missing0,and personal-known(full-none)/43>=.25. Retention interpretable only with qualified full. Strict transport gate additionally requires own and wrong-against-donor repeat both102/102,missing0. Identity-specificity also requires lower wrong-target personal-known than own. Report all31slots, invalid products, missing denominators, every paired loss and repeated-answer change. None expected ceiling from uninformed version space recorded; alwaysU gets0known47unknown. No population CIs.',
 'stop':'Exclusive intent; no resume/retry/repair/truncation/fallback/deadline extension/replacement/replenishment. Transport, wire/schema/decode, unknownusage, guard or binding failure stops all later calls. Valid-schema extraction rejected by source/role/budget is an invalid product; skip only dependent own/tail/wrong reader slots, keep all102planned denominators and independent slots. Quality errors do not stop fixed remaining calls.',
 'limits':'Controlled shared-codebook reasoning protocol, not stock-reader behavior without it, unconstrained latent-taste inference, human fidelity, demographic profiling, new-person population estimate, cross-vendor/runtime-harness portability or likelihoodRIG. Histories are authored and short; observed decisions are explicit.619shareddecodercharacters must not be hidden as free compression. Read token usage is not end-to-end savings or invoice. Requested model only; resolved identity unavailable.31is a call cap, not token/money cap. After first outcomes this corpus is consumed.'}
 p['id']=digest(canonical(p));write_once(out/'proposal.json',p);return p


def preflight(out):
 out=Path(out).resolve();p=read(out/'proposal.json');require(p['id']==digest(canonical({k:v for k,v in p.items() if k!='id'})),'Proposal checksum');require(p['directory']==str(out) and p['calls_max']==CAP and p['model']==MODEL and p['budget']==BUDGET,'Scope drift');require(set(p['source_hashes'])==set(source_names()),'Source inventory')
 for n,hsh in p['source_hashes'].items():require(sha(ROOT/n)==hsh,'Frozen source drift:'+n)
 for n,hsh in p['input_hashes'].items():require(sha(out/n)==hsh,'Input drift:'+n)
 f=read(out/'world.synthetic.json');static=read(out/'static-requests.synthetic.json');require(f==w.fixtures() and read(out/'plan.json')==plan(),'World/plan reconstruction');require(static=={g+':'+pid:request_for(f,g,pid,{}) for g,pid in plan() if g in ['none','full','extraction']},'Static request binding');return p,f,static


def decode(f,answer):return h.reader.decode_response(f['queries'],answer,answer_format='text')


def analyze(f,raw):
 scores={};decoded={};rejected={}
 for group in [g for g in GROUPS if g!='extraction']:
  answers={}
  for pid,value in raw.get(group,{}).items():
   try:labels=decode(f,value)
   except ValueError as exc:rejected[group+':'+pid]={'error':str(exc),'raw_sha256':digest(canonical(value))};continue
   for target in (w.PEOPLE if group=='none' else [pid]):answers[target]=labels
  decoded[group]=answers;scores[group]=w.evaluate(f,answers)
 donor=w.evaluate(f,decoded['wrong'],donor_gold=True);qualified=scores['full']['strict_pass'] and (scores['full']['personal_known']['correct']-scores['none']['personal_known']['correct'])/43>=.25;quality={'contemporary_full_qualified':qualified,'retention_interpretable':qualified,'strict_transport_pass':qualified and scores['own']['strict_pass'] and donor['strict_pass'],'identity_specificity_verified':scores['own']['strict_pass'] and donor['strict_pass'] and scores['wrong']['personal_known']['correct']<scores['own']['personal_known']['correct']}
 pairs={}
 for left,right in [('full','own'),('full','tail'),('tail','own'),('own','wrong')]:
  le={(e['person'],e['case']) for e in scores[left]['errors']};re={(e['person'],e['case']) for e in scores[right]['errors']};delta={}
  for kind in ['known','unknown']:
   ids={(p,c['id']) for c in f['cases'] for p in w.PEOPLE if (c['gold'][p]!=w.U)==(kind=='known')};delta[kind]={'lost':sorted([list(x) for x in (re-le)&ids]),'recovered':sorted([list(x) for x in (le-re)&ids])}
  pairs[left+'->'+right]=delta
 disagreements=[]
 for target in w.PEOPLE:
  person=f['donors'][target]
  for case in f['cases']:
   qids=[o['public']['id'] for o in case['orders']]
   if all(q in decoded['own'].get(person,{}) and q in decoded['wrong'].get(target,{}) for q in qids) and any(decoded['own'][person][q]!=decoded['wrong'][target][q] for q in qids):disagreements.append({'person':person,'wrong_target':target,'case':case['id'],'own':[decoded['own'][person][q] for q in qids],'donor_repeat':[decoded['wrong'][target][q] for q in qids]})
 return {'groups':scores,'wrong_against_donor':donor,'quality':quality,'paired_losses':pairs,'donor_repeat_disagreements':disagreements,'rejected_answers':rejected,'real_person_fidelity_verified':False}


def execute(out,backend=None):
 out=Path(out).resolve();p,f,static=preflight(out);real=backend is None
 if real:
  require(shared.guard_status()['owned_active'],'Owned idle-sleep guard required before service intent');acceptance=read(out/'offline-acceptance.json');require(acceptance['passed'] and acceptance['proposal_id']==p['id'] and acceptance['model_calls']==0,'Offline acceptance');require(h.runtime_metadata()==p['runtime'],'Runtime drift')
 with (out/'service-intent.json').open('x') as stream:json.dump({'proposal_id':p['id'],'calls_max':CAP,'human_source':p['authorization'],'real_service':real},stream);stream.flush();os.fsync(stream.fileno())
 service=out/'service';service.mkdir();raw={};products={};invalid={};completed=[];skipped=[];stop=None
 def guard():
  require(preflight(out)[0]['id']==p['id'] and len(h.records_checked(service))<CAP,'Binding/globalcap')
  if real:
   observation=shared.guard_status();require(observation['owned_active'],'Owned guard disappeared');observation['before_call']=len(h.records_checked(service))+1;path=out/'guard-observations.json';rows=read(path) if path.exists() else [];rows.append(observation);atomic(path,rows)
 by_group={}
 for group in GROUPS:
  folder=service/group;folder.mkdir();cap=sum(g==group for g,p in plan());by_group[group]=h.StrictCalls(folder,{'calls_max':cap,'stage_caps':{group:cap},'models':{'reader':MODEL,'generator':MODEL},'forbidden_request_ids':[]},backend or h.generation.codex_generate,guard)
 for group,pid in plan():
  donor=f['donors'][pid] if group=='wrong' else pid;calls=by_group[group]
  if group in ['own','tail','wrong'] and donor not in products:skipped.append([group,pid,'invalid_or_missing_extraction:'+donor]);atomic(service/'skipped.json',skipped);continue
  try:
   request=static.get(group+':'+pid) or request_for(f,group,pid,products)
   with patch.object(h.fr,'SYSTEM',request['system']),patch.object(h.generation,'run_bounded',calls.observed_runner):value=calls.call(group,request)
   raw.setdefault(group,{})[pid]=value;atomic(service/'answers.synthetic.json',raw);completed.append([group,pid]);atomic(service/'completed-plan.json',completed);h.validate_wire(value,request['schema'])
   if group=='extraction':
    try:products[pid]=h.extractor.bind(value,f['histories'][pid],BUDGET)
    except ValueError as exc:invalid[pid]={'error':str(exc),'no_repair':True};atomic(service/'invalid-products.json',invalid)
    atomic(service/'products.synthetic.json',products)
   else:decode(f,value)
   print(json.dumps({'group':group,'person':pid,'actual_calls':len(h.records_checked(service)),'invalid_products':len(invalid)}),flush=True)
  except Exception as exc:
   if not calls.stopped:calls.stop('wire_or_local_validation_failure',error_type=type(exc).__name__,error=str(exc))
   stop={'group':group,'person':pid,'reason':calls.reason};break
 try:ledger=h.summarize(h.records_checked(service))
 except Exception as exc:ledger={'integrity_uncertain':True,'known_usage':None,'error_type':type(exc).__name__};stop=stop or {'reason':'ledger_integrity_uncertain'}
 result={'status':'stopped' if stop else 'completed_with_invalid_products' if invalid else 'complete','proposal_id':p['id'],'backend_kind':'actual_codex_service' if real else 'injected_fake_not_model_evidence','ledger':ledger,'stop_reason':stop,'completed_plan':completed,'skipped':skipped,'invalid_products':invalid,**analyze(f,raw)};write_once(service/'report.json',result);return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','run']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();value=prepare(args.out) if args.action=='prepare' else preflight(args.out)[0] if args.action=='preflight' else execute(args.out);print(json.dumps({k:value[k] for k in ['id','status','ledger'] if k in value}))
