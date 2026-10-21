"""Frozen fresh-policy end-to-end study; prepare/preflight are offline."""
import argparse
import copy
import importlib.util
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('fresh_boundary_world',HERE/'world.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
from runaway import choice_reader as reader, support_extract as extractor, generation, fidelity_runner as fr
from runaway.card import canonical,digest
from runaway.end_to_end_runner import StrictCalls
from runaway.shared_schema import parse_wire
from runaway.shared_schema_executor import records_checked,runtime_metadata
from runaway.execution_ledger import summarize
from runaway.pipeline import write_once
from runaway.taste_executor import atomic
CAP=56;BUDGET=768;AS_OF='2026-07-01'
MODELS={'luna':'gpt-6-luna','sol':'gpt-6-sol'}
COMMON='仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'


def require(ok,message):
 if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):return parse_wire(Path(path).read_bytes())


def validate_wire(value,node):
 allowed={'type','enum','properties','required','additionalProperties','items'}
 require(not set(node)-allowed,'Unsupported local schema keywords')
 kind=node['type'];match={'object':type(value) is dict,'array':type(value) is list,'string':type(value) is str,'integer':type(value) is int}
 require(kind in match and match[kind],'Schema type mismatch')
 if 'enum' in node:require(value in node['enum'],'Schema enum mismatch')
 if kind=='object':
  require(set(node.get('required',[]))<=set(value),'Schema missing keys');properties=node.get('properties',{})
  if node.get('additionalProperties') is False:require(not set(value)-set(properties),'Schema extra keys')
  for key,item in value.items():
   if key in properties:validate_wire(item,properties[key])
 if kind=='array':
  for item in value:validate_wire(item,node['items'])


def source_names():
 return sorted([str(p.relative_to(ROOT)) for p in (ROOT/'runaway').glob('*.py')]+['benchmarks/fresh-boundary-v1/world.py','benchmarks/fresh-boundary-v1/study.py','tests/test_fresh_boundary.py','tests/test_scoped_reader.py'])


def plan():
 slots=[]
 def add(prefix,mode,arm,pid,repeat=False):slots.append([prefix+'_'+mode+'_'+arm+('_repeat' if repeat else ''),pid])
 for prefix in MODELS:
  for index,pid in enumerate(w.PEOPLE):
   for mode in (['standard','scoped'] if index%2==0 else ['scoped','standard']):add(prefix,mode,'full',pid)
  for mode in ['standard','scoped']:add(prefix,mode,'none','shared')
 slots += [['extraction',pid] for pid in w.PEOPLE]
 for prefix in MODELS:
  for index,pid in enumerate(w.PEOPLE):
   for mode in (['standard','scoped'] if index%2==0 else ['scoped','standard']):add(prefix,mode,'own',pid)
  for pid in w.PEOPLE:add(prefix,'standard','wrong',pid)
 for index,pid in enumerate(w.PEOPLE):
  for mode in (['scoped','standard'] if index%2==0 else ['standard','scoped']):add('luna',mode,'own',pid,True)
 require(len(slots)==CAP,'Fixed cap');return slots


def descriptor(group):
 if group=='extraction':return ('sol','standard','extraction')
 return tuple(group.split('_')[:3])


def request_for(f,group,pid,cards):
 prefix,mode,arm=descriptor(group)
 if arm=='extraction':return {'system':extractor.SYSTEM,'model':MODELS['sol'],**extractor.make_request(f['histories'][pid],BUDGET)}
 material='' if arm=='none' else canonical(f['histories'][pid]) if arm=='full' else cards[pid if arm=='own' else f['donors'][pid]]['prompt.md']
 req=reader.make_request(material,f['queries'],as_of=AS_OF,answer_format='text',reader_mode=mode)
 return {'system':extractor.SYSTEM,'model':MODELS[prefix],**req,'prompt':COMMON+req['prompt']}


def prepare(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);f=w.fixtures();static={}
 for group,pid in plan():
  if descriptor(group)[2] in ('full','none','extraction'):static[group+':'+pid]=request_for(f,group,pid,{})
 write_once(out/'world.synthetic.json',f);write_once(out/'static-requests.synthetic.json',static);write_once(out/'plan.json',plan())
 p={'kind':'fresh_synthetic_boundary_e2e_v1','directory':str(out),'calls_max':CAP,'budget_characters':BUDGET,'models':MODELS,'extractor_model':MODELS['sol'],'source_hashes':{n:sha(ROOT/n) for n in source_names()},'input_hashes':{n:sha(out/n) for n in ['world.synthetic.json','static-requests.synthetic.json','plan.json']},'runtime':runtime_metadata(),
 'authorization':'Current direct human: 那就持续推进, after the fresh-user end-to-end plan. Synthetic data only, existing Codex backend; independently declared56-call ceiling. No prior allowance or real-person data reused.',
 'design':'Four new authored synthetic users, four domains,32new scenarios,92rotated queries/person,128person/scenario cases:40known88unknown. Models each standard/scoped full4 none1 own4 plus standard wrong4=22; extraction4Sol; Luna own standard4/scoped4 independent reverse-order repeats8; total56. Full/none contemporary per reader contract. Paragraph default, same automatic card for both readers. Balanced reader-contract order byperson; repeat reversed. Not a layout study.',
 'quality':'All128correct across allpositions plus missing0 and known(full-none)/40>=.25 qualifies full per model/contract. Report every arm and scope accuracy/joint, unknown reasons, lost/recovered and donor sensitivity separately. Scoped full qualification and stable transfer additionally require all128scope-and-choice cases correct. Full failure does not stop fixed remaining diagnostics. Stable transfer requires full qualification and own strict pass, and both Luna own draws pass for its contract. No best-of, threshold relaxation, subjective model judge, populationCI or likelihoodRIG.',
 'visibility':'Encoder gets only one role-labelled history, extractor contract and budget; reader gets one history/card/empty material, public questions and answer contract. Policies, hand tables, gold, private anchors, group/person labels, other responses and code never enter service requests. Dynamic cards must be exact production bind result from that person extraction; wrong cards only predefined paired donor.',
 'stop':'Any transport, JSON/schema, usage or binding failure stops all later calls, no retries/resume/fallback/replenishment. A syntactically valid extraction failing production anchors/budget is retained as invalid product; skip only its dependent own/wrong requests, retain planned denominators, finish other independent slots. Never truncate or repair. Quality failures do not stop unconditional repeats.',
 'limits':'New authored policies/scenarios relative to prior six-policy studies, not independently collected/external validation. Generated histories and finite tables authored in same project; manual hand oracle checks only program agreement. Four synthetic people/two contrasting pairs; no human fidelity, cross-vendor, resolved server identity, runtime harness or causal compression claim when full fails. Report unobserved domains64 separately from informative unknowns24. Character budget, not token/money cap.'}
 p['id']=digest(canonical(p));write_once(out/'proposal.json',p);return p


def preflight(out):
 out=Path(out).resolve();p=read(out/'proposal.json');require(p['id']==digest(canonical({k:v for k,v in p.items() if k!='id'})),'Proposal binding')
 require(p['directory']==str(out) and p['calls_max']==CAP and p['models']==MODELS and p['budget_characters']==BUDGET,'Scope drift')
 require(set(p['source_hashes'])==set(source_names()),'Source inventory drift')
 for n,h in p['source_hashes'].items():require(sha(ROOT/n)==h,'Frozen code drift:'+n)
 for n,h in p['input_hashes'].items():require(sha(out/n)==h,'Input drift:'+n)
 f=read(out/'world.synthetic.json');require(f==w.fixtures() and read(out/'plan.json')==plan(),'Fixture/plan reconstruction')
 static=read(out/'static-requests.synthetic.json');expected={g+':'+pid:request_for(f,g,pid,{}) for g,pid in plan() if descriptor(g)[2] in ('full','none','extraction')};require(static==expected,'Request visibility/binding')
 return p,f,static


def decode(f,group,raw):
 mode=descriptor(group)[1];labels=reader.decode_response(f['queries'],raw,answer_format='text',reader_mode=mode)
 return labels,({qid:v['scope'] for qid,v in raw.items()} if mode=='scoped' else None)


def analyze(f,raw):
 scores={};rejected={}
 for group in sorted({g for g,pid in plan()}-{'extraction'}):
  arm=descriptor(group)[2];answers={};scopes={} if descriptor(group)[1]=='scoped' else None
  for pid,value in raw.get(group,{}).items():
   try:labels,scope=decode(f,group,value)
   except ValueError as exc:rejected[group+':'+pid]={'error':str(exc),'raw_sha256':digest(canonical(value))};continue
   for target in (w.PEOPLE if arm=='none' else [pid]):
    answers[target]=labels
    if scopes is not None:scopes[target]=scope
  scores[group]=w.evaluate(f,answers,scopes)
 quality={}
 for prefix in MODELS:
  for mode in ['standard','scoped']:
   full=scores[prefix+'_'+mode+'_full'];none=scores[prefix+'_'+mode+'_none'];own=scores[prefix+'_'+mode+'_own'];qualified=full['strict_choice_pass'] and (mode!='scoped' or full['scope_choice_joint']['correct']==128) and (full['known']['correct']-none['known']['correct'])/40>=.25
   quality[prefix+'_'+mode]={'full_qualified':qualified,'retention_interpretable':qualified,'own_strict_pass':own['strict_choice_pass'],'own_scope_joint_pass':mode=='scoped' and own['scope_choice_joint']['correct']==128,'stable_transfer_pass':qualified and own['strict_choice_pass'] and (mode!='scoped' or own['scope_choice_joint']['correct']==128) and (prefix!='luna' or (scores[prefix+'_'+mode+'_own_repeat']['strict_choice_pass'] and (mode!='scoped' or scores[prefix+'_'+mode+'_own_repeat']['scope_choice_joint']['correct']==128)))}
 pairs={}
 for prefix in MODELS:
  for before,after in [(prefix+'_standard_full',prefix+'_standard_own'),(prefix+'_scoped_full',prefix+'_scoped_own'),(prefix+'_standard_own',prefix+'_scoped_own')]+([(prefix+'_standard_own_repeat',prefix+'_scoped_own_repeat')] if prefix=='luna' else []):
   left={(e['person'],e['case']) for e in scores[before]['errors'] if not e['choice_correct']};right={(e['person'],e['case']) for e in scores[after]['errors'] if not e['choice_correct']};delta={}
   for kind in ['known','unknown']:
    ids={(pid,c['id']) for c in f['cases'] for pid in w.PEOPLE if (c['gold'][pid]!='U')==(kind=='known')}
    delta[kind]={'lost':sorted([list(k) for k in (right-left)&ids]),'recovered':sorted([list(k) for k in (left-right)&ids])}
   pairs[before+'->'+after]=delta
 donor_scores={}
 for prefix in MODELS:
  group=prefix+'_standard_wrong';answers={}
  for pid,value in raw.get(group,{}).items():
   try:answers[pid]=decode(f,group,value)[0]
   except ValueError:continue
  donor_world=copy.deepcopy(f)
  for case in donor_world['cases']:
   gold=case['gold'].copy();scope=case['scope_gold'].copy();case['gold']={pid:gold[f['donors'][pid]] for pid in w.PEOPLE};case['scope_gold']={pid:scope[f['donors'][pid]] for pid in w.PEOPLE}
  donor_scores[group]=w.evaluate(donor_world,answers)
 return {'groups':scores,'rejected_answers':rejected,'wrong_against_donor':donor_scores,'quality':quality,'paired_losses':pairs,'human_fidelity_tested':False}


def execute(out,backend=None):
 out=Path(out).resolve();p,f,static=preflight(out);real=backend is None
 if real:
  a=read(out/'offline-acceptance.json');require(a['passed'] and a['proposal_id']==p['id'] and a['model_calls']==0,'Offline acceptance required');require(runtime_metadata()==p['runtime'],'Runtime drift')
 with (out/'service-intent.json').open('x') as stream:json.dump({'proposal_id':p['id'],'calls_max':CAP,'human_source':p['authorization'],'real_service':real},stream);stream.flush();os.fsync(stream.fileno())
 service=out/'service';service.mkdir();raw={};cards={};invalid={};completed=[];skipped=[];calls_by_group={};stop=None
 def guard():
  require(preflight(out)[0]['id']==p['id'],'Preflight drift');require(len(records_checked(service))<CAP,'Global cap')
 backend=backend or generation.codex_generate
 for group in sorted({g for g,pid in plan()}):
  folder=service/group;folder.mkdir();model=MODELS[descriptor(group)[0]];cap=sum(g==group for g,pid in plan())
  calls_by_group[group]=StrictCalls(folder,{'calls_max':cap,'stage_caps':{group:cap},'models':{'reader':model,'generator':model},'forbidden_request_ids':[]},backend,guard)
 for group,pid in plan():
  arm=descriptor(group)[2];calls=calls_by_group[group]
  donor=pid if arm=='own' else f['donors'].get(pid)
  if arm in ('own','wrong') and donor not in cards:
   skipped.append([group,pid,'invalid_or_missing_extraction:'+str(donor)]);atomic(service/'skipped.json',skipped);continue
  try:
   request=static.get(group+':'+pid) or request_for(f,group,pid,cards)
   with patch.object(fr,'SYSTEM',request['system']),patch.object(generation,'run_bounded',calls.observed_runner):value=calls.call(group,request)
   raw.setdefault(group,{})[pid]=value;atomic(service/'answers.synthetic.json',raw);completed.append([group,pid]);atomic(service/'completed-plan.json',completed)
   validate_wire(value,request['schema'])
   if arm=='extraction':
    try:cards[pid]=extractor.bind(value,f['histories'][pid],BUDGET)
    except ValueError as exc:invalid[pid]={'error':str(exc),'no_repair':True};atomic(service/'invalid-products.json',invalid)
    atomic(service/'products.synthetic.json',cards)
   else:decode(f,group,value)
   print(json.dumps({'group':group,'person':pid,'actual_calls':len(records_checked(service)),'invalid_products':len(invalid)}),flush=True)
  except Exception as exc:
   if not calls.stopped:calls.stop('validation_or_local_failure',error_type=type(exc).__name__,error=str(exc))
   stop={'group':group,'person':pid,'reason':calls.reason};break
 result={'status':'stopped' if stop else 'completed_with_invalid_products' if invalid else 'complete','proposal_id':p['id'],'backend_kind':'actual_codex_service' if real else 'injected_fake_not_model_evidence','ledger':summarize(records_checked(service)),'stop_reason':stop,'invalid_products':invalid,'completed_plan':completed,'skipped':skipped,**analyze(f,raw)}
 write_once(service/'report.json',result);return result


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','preflight','run','analyze']);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
 if args.action=='prepare':value=prepare(args.out)
 elif args.action=='preflight':value=preflight(args.out)[0]
 elif args.action=='analyze':value=analyze(read(args.out/'world.synthetic.json'),read(args.out/'service/answers.synthetic.json'));atomic(args.out/'analysis.json',value)
 else:value=execute(args.out)
 print(json.dumps({k:value[k] for k in ['id','status','ledger'] if k in value},ensure_ascii=False))
