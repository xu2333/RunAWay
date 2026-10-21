"""Fixed46-call long-source and whole-card budget pressure test."""
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
w=load('long_budget_world',HERE/'world.py');h=load('long_budget_shared_tools',HERE.parent/'fresh-boundary-v1/study.py')
CAP=46;BUDGETS=[768,512,384];AS_OF='2026-09-30';MODELS={'sol':'gpt-6-sol','luna':'gpt-6-luna'}
read=h.read;require=h.require;sha=h.sha;canonical=h.canonical;digest=h.digest;atomic=h.atomic;write_once=h.write_once


def budget_order(index):return [BUDGETS[(index+j)%3] for j in range(3)] if index<3 else [384,512,768]


def plan():
 slots=[]
 for prefix in MODELS:
  for pid in w.PEOPLE:slots.append([prefix+'_full',pid])
  if prefix=='sol':
   for pid in w.PEOPLE:slots.append(['sol_short',pid])
  slots.append([prefix+'_none','shared'])
 for index,pid in enumerate(w.PEOPLE):
  for budget in budget_order(index):slots.append(['extract_'+str(budget),pid])
 for index,pid in enumerate(w.PEOPLE):
  for budget in reversed(budget_order(index)):slots.append(['sol_'+str(budget),pid])
 for pid in w.PEOPLE:slots.append(['luna_768',pid])
 for pid in reversed(w.PEOPLE):slots.append(['sol_384_repeat',pid])
 require(len(slots)==CAP,'Fixed46cap');return slots


def descriptor(group):
 parts=group.split('_')
 if parts[0]=='extract':return 'sol','extraction',int(parts[1])
 if parts[1] in ('full','short','none'):return parts[0],parts[1],None
 return parts[0],'own',int(parts[1])


def source_names():
 return sorted([str(p.relative_to(ROOT)) for p in (ROOT/'runaway').glob('*.py')]+['benchmarks/fresh-boundary-v1/world.py','benchmarks/fresh-boundary-v1/study.py','benchmarks/long-trajectory-v1/world.py','benchmarks/long-trajectory-v1/study.py','tests/test_long_trajectory.py'])


def request_for(f,group,pid,products):
 prefix,arm,budget=descriptor(group)
 if arm=='extraction':return {'system':h.extractor.SYSTEM,'model':MODELS['sol'],**h.extractor.make_request(f['histories'][pid],budget)}
 if arm=='none':material=''
 elif arm=='short':material=canonical(w.base.fixtures()['histories'][pid])
 elif arm=='full':material=canonical(f['histories'][pid])
 else:material=products[str(budget)][pid]['prompt.md']
 req=h.reader.make_request(material,f['queries'],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'system':h.extractor.SYSTEM,'model':MODELS[prefix],**req,'prompt':h.COMMON+req['prompt']}


def prepare(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);f=w.fixtures();static={g+':'+pid:request_for(f,g,pid,{}) for g,pid in plan() if descriptor(g)[1]!='own'}
 for name,value in [('world.synthetic.json',f),('static-requests.synthetic.json',static),('plan.json',plan())]:write_once(out/name,value)
 p={'kind':'long_trajectory_whole_budget_v1','directory':str(out),'calls_max':CAP,'budgets':BUDGETS,'models':MODELS,'source_hashes':{n:sha(ROOT/n) for n in source_names()},'input_hashes':{n:sha(out/n) for n in ['world.synthetic.json','static-requests.synthetic.json','plan.json']},'runtime':h.runtime_metadata(),
 'authorization':'Current direct human: 继续验证. Synthetic-only new46-call ceiling through existing Codex backend; no prior call balance or real-person data reused.',
 'design':'Same4consumed final policies, alternative dated long histories with18user decisions across3epochs/person and assistant/tool observations; not new independent users or real harness trajectories.40scenes=32consumed+8new derived stress scenes;116cyclicqueries/person;160person/scenario cases=43known117unknown. Newcohort32cases=3known29unknown. Source-visibility and finite-world hand oracle fixed. Standard production reader plus same absent-option instruction/system throughout.',
 'matrix':'Sol longfull4 shortfull4 none1; Luna longfull4 none1=14controls. One Sol extraction/person/budget768512384=12. Sol own12; Luna768own4; Sol384ownrepeat4 in reversedperson order.46maximum physical invocations. No wrong-person rerun; prior donor test already complete. Repetition not reuse of an old response. Same public questions for all arms; extraction sees no questions/policies/gold.',
 'quality':'Full qualifies per requestedmodel only all160current-choice cases correct across allpositions,missing0, known(full-none)/43>=.25. Solshort measured separately to diagnose length; no substitution for longfull. Primary allplanned-denominator curves perbudget and cohorts, known/unknown/missing and invalid productcounts. Retention interpreted only with qualified contemporaneous longfull.384stable gate also requires both Sol384card draws perfect, no invalid products. Report every lost/recovered case, including budget-induced abstentions. No picking bestencoder/reader draw or retuning consumed scenes.',
 'stop':'Singleuse, no resume/retry/repair/fallback/replenishment. Transport/wire/schema/unknownusage/bindingfailure stops every later call. Valid-schema extraction failing production evidence/budget is an invalid product; skip its dependent reads/repeat only, retain all planned denominators and other independent slots. Quality failures do not stop fixed remaining work. Never truncate.',
 'limits':'This is current-state selection from deliberately redundant edited histories, not compression of all biography, newperson generalization, latent-rule induction, realperson fidelity, or external holdout. Report plain source text, roleJSON and current short-history reference separately; long-source ratio must not be mislabeled latent semantic compression. Budgets may alter extractor wording plus glossary packing; one encoder draw each, not a causal isolating experiment. Requested models only, no vendor/runtimeharness/populationCI/likelihoodRIG/invoice claims. No aggregate token or money cap implied.'}
 p['id']=digest(canonical(p));write_once(out/'proposal.json',p);return p


def preflight(out):
 out=Path(out).resolve();p=read(out/'proposal.json');require(p['id']==digest(canonical({k:v for k,v in p.items() if k!='id'})),'Proposal checksum')
 require(p['directory']==str(out) and p['calls_max']==CAP and p['budgets']==BUDGETS and p['models']==MODELS,'Scope drift');require(set(p['source_hashes'])==set(source_names()),'Source inventory')
 for n,hsh in p['source_hashes'].items():require(sha(ROOT/n)==hsh,'Frozen source drift:'+n)
 for n,hsh in p['input_hashes'].items():require(sha(out/n)==hsh,'Input drift:'+n)
 f=read(out/'world.synthetic.json');require(f==w.fixtures() and read(out/'plan.json')==plan(),'World/plan reconstruction')
 static=read(out/'static-requests.synthetic.json');require(static=={g+':'+pid:request_for(f,g,pid,{}) for g,pid in plan() if descriptor(g)[1]!='own'},'Static visibility/binding')
 return p,f,static


def decode(f,raw):return h.reader.decode_response(f['queries'],raw,answer_format='text')


def analyze(f,raw):
 scores={};rejected={}
 for group in sorted({g for g,pid in plan() if descriptor(g)[1]!='extraction'}):
  answers={}
  for pid,value in raw.get(group,{}).items():
   try:labels=decode(f,value)
   except ValueError as exc:rejected[group+':'+pid]={'error':str(exc),'raw_sha256':digest(canonical(value))};continue
   for target in (w.PEOPLE if descriptor(group)[1]=='none' else [pid]):answers[target]=labels
  scores[group]=w.evaluate(f,answers)
 quality={}
 for prefix in MODELS:
  full,none=scores[prefix+'_full'],scores[prefix+'_none'];qualified=full['strict_choice_pass'] and (full['known']['correct']-none['known']['correct'])/43>=.25
  quality[prefix]={'long_full_qualified':qualified,'retention_interpretable':qualified}
  if prefix=='sol':quality[prefix]['short_full_strict_pass']=scores['sol_short']['strict_choice_pass']
 quality['sol']['stable_384_transfer_pass']=quality['sol']['long_full_qualified'] and scores['sol_384']['strict_choice_pass'] and scores['sol_384_repeat']['strict_choice_pass']
 pairs={}
 for before,after in [('sol_full','sol_768'),('sol_full','sol_512'),('sol_full','sol_384'),('sol_768','sol_512'),('sol_512','sol_384'),('sol_384','sol_384_repeat'),('luna_full','luna_768')]:
  left={(e['person'],e['case']) for e in scores[before]['errors'] if not e['choice_correct']};right={(e['person'],e['case']) for e in scores[after]['errors'] if not e['choice_correct']};delta={}
  for kind in ['known','unknown']:
   ids={(p,c['id']) for c in f['cases'] for p in w.PEOPLE if (c['gold'][p]!='U')==(kind=='known')};delta[kind]={'lost':sorted([list(x) for x in (right-left)&ids]),'recovered':sorted([list(x) for x in (left-right)&ids])}
  pairs[before+'->'+after]=delta
 return {'groups':scores,'quality':quality,'paired_losses':pairs,'rejected_answers':rejected,'real_person_fidelity_verified':False,'historical_recall_tested':False}


def execute(out,backend=None):
 out=Path(out).resolve();p,f,static=preflight(out);real=backend is None
 if real:
  a=read(out/'offline-acceptance.json');require(a['passed'] and a['proposal_id']==p['id'] and a['model_calls']==0,'Offline acceptance');require(h.runtime_metadata()==p['runtime'],'Runtime drift')
 with (out/'service-intent.json').open('x') as stream:json.dump({'proposal_id':p['id'],'calls_max':CAP,'human_source':p['authorization'],'real_service':real},stream);stream.flush();os.fsync(stream.fileno())
 service=out/'service';service.mkdir();raw={};products={};invalid={};completed=[];skipped=[];calls_by_group={};stop=None
 def guard():require(preflight(out)[0]['id']==p['id'] and len(h.records_checked(service))<CAP,'Binding/globalcap')
 backend=backend or h.generation.codex_generate
 for group in sorted({g for g,p in plan()}):
  folder=service/group;folder.mkdir();model=MODELS[descriptor(group)[0]];cap=sum(g==group for g,p in plan());calls_by_group[group]=h.StrictCalls(folder,{'calls_max':cap,'stage_caps':{group:cap},'models':{'reader':model,'generator':model},'forbidden_request_ids':[]},backend,guard)
 for group,pid in plan():
  prefix,arm,budget=descriptor(group);calls=calls_by_group[group]
  if arm=='own' and pid not in products.get(str(budget),{}):skipped.append([group,pid,'invalid_or_missing_extraction:'+str(budget)+':'+pid]);atomic(service/'skipped.json',skipped);continue
  try:
   request=static.get(group+':'+pid) or request_for(f,group,pid,products)
   with patch.object(h.fr,'SYSTEM',request['system']),patch.object(h.generation,'run_bounded',calls.observed_runner):value=calls.call(group,request)
   raw.setdefault(group,{})[pid]=value;atomic(service/'answers.synthetic.json',raw);completed.append([group,pid]);atomic(service/'completed-plan.json',completed);h.validate_wire(value,request['schema'])
   if arm=='extraction':
    try:products.setdefault(str(budget),{})[pid]=h.extractor.bind(value,f['histories'][pid],budget)
    except ValueError as exc:invalid[str(budget)+':'+pid]={'error':str(exc),'no_repair':True};atomic(service/'invalid-products.json',invalid)
    atomic(service/'products.synthetic.json',products)
   else:decode(f,value)
   print(json.dumps({'group':group,'person':pid,'actual_calls':len(h.records_checked(service)),'invalid_products':len(invalid)}),flush=True)
  except Exception as exc:
   if not calls.stopped:calls.stop('wire_or_local_validation_failure',error_type=type(exc).__name__,error=str(exc))
   stop={'group':group,'person':pid,'reason':calls.reason};break
 try:ledger=h.summarize(h.records_checked(service))
 except Exception as exc:ledger={'integrity_uncertain':True,'known_usage':None,'error_type':type(exc).__name__};stop=stop or {'reason':'ledger_integrity_uncertain'}
 result={'status':'stopped' if stop else 'completed_with_invalid_products' if invalid else 'complete','proposal_id':p['id'],'backend_kind':'actual_codex_service' if real else 'injected_fake_not_model_evidence','ledger':ledger,'stop_reason':stop,'invalid_products':invalid,'completed_plan':completed,'skipped':skipped,**analyze(f,raw)};write_once(service/'report.json',result);return result

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','run']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();value=prepare(args.out) if args.action=='prepare' else preflight(args.out)[0] if args.action=='preflight' else execute(args.out);print(json.dumps({k:value[k] for k in ['id','status','ledger'] if k in value}))
