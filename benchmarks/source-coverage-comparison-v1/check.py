"""Offline replay of consumed source-inventory/audit/compression evidence. No backend."""
from collections import Counter
import hashlib, importlib.util, json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'benchmarks/source-coverage-pipeline-v1'))
from runaway import grouped_support as grouped,choice_reader
from runaway.card import canonical
from runaway.constraint_extract import parse_answer,check as schema_check
import producers,auditing
spec=importlib.util.spec_from_file_location('source_coverage_count_helpers',ROOT/'benchmarks/natural-controls-v1/check.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
counts=helpers.counts
MODULES=('card','choice_reader','choice_contract','constraint_extract','portable','profile','prompt_codec','scope_rows','grouped_support','support_extract','text_integrity')
PIPELINE=('coverage_contract','producers','auditing')
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def read(path):return json.loads(path.read_text())
def optional_usage(provenance):
 try:return helpers.usage(provenance)
 except ValueError:return None

MODEL='gpt-6.1-sol';AS_OF='2026-10-23';BUDGET=512;CAP=45
VARIANTS=('grouped-v1','coverage-v1')
COMMON='仅当唯一已记录做法出现在本题选项中时返回该做法；唯一已知做法未列入选项时返回U，不改选另一做法。\n'
TAIL_NOTE='原始多角色记录尾部，开头可能被截断；只把完整标明user的决定作为证据。\n'
CONFIG={'requested_model':MODEL,'calls_max':CAP,'timeout_seconds':180,'variants':list(VARIANTS),
 'whole_public_budget':BUDGET,'as_of':AS_OF,'reader_mode':'standard','answer_format':'text',
 'source_only_inventory':True,'distinct_source_only_audit_call':True,'audit_flag_blocks_compression':True,
 'under_budget_partial_cards_read_but_cannot_pass_strict_gate':True,'retry':False,'repair':False,'resume':False,
 'aggregate_token_cap':None,'money_cap':None,'invocation_unit':'one tool-free local codex exec child; upstream RPC/retries unobservable'}

def plan(people):
 if len(people)!=4 or len(set(people))!=4:raise ValueError('Four distinct profiles required')
 pairs=[('none','shared',None)]+[('full',pid,None) for pid in people]
 pairs += [('inventory',pid,'coverage-v1') for pid in people]
 pairs += [('audit',pid,'coverage-v1') for pid in people]
 for r in range(2):pairs += [('extract',pid,VARIANTS[(r+i)%2]) for i,pid in enumerate(people)]
 for vr in range(2):
  for gr in range(3):pairs += [(('own','tail','wrong')[(gr+i)%3],pid,VARIANTS[(vr+i)%2]) for i,pid in enumerate(people)]
 return [{'slot':i+1,'group':g,'person':pid,'variant':v,'budget':BUDGET if g in ('extract','own','tail','wrong') else None} for i,(g,pid,v) in enumerate(pairs)]

def key(slot):return ':'.join(str(slot[k]) for k in ('group','person','variant'))
def donors(people):return {pid:people[(i+1)%len(people)] for i,pid in enumerate(people)}
def inputs(root):
 people=read(root/'sources/index.json')['people']
 return people,{pid:read(root/'sources'/(pid+'.json')) for pid in people},read(root/'evaluation/queries.public.json')

def request(slot,sources,queries,artifacts,people):
 if slot not in plan(people):raise ValueError('Unexpected slot')
 g,pid,v=slot['group'],slot['person'],slot['variant']
 if g=='inventory':req=producers.make_inventory_request(sources[pid]['sources'])
 elif g=='audit':
  inv=artifacts.get(('inventory',pid,'coverage-v1'))
  if inv is None:return None
  req=auditing.make_audit_request(inv['ledger'])
 elif g=='extract':
  if v=='grouped-v1':req={'system':grouped.SYSTEM,**grouped.make_request(sources[pid],BUDGET)}
  else:
   inv=artifacts.get(('inventory',pid,v));audit=artifacts.get(('audit',pid,v))
   if inv is None or audit is None or not audit['audit']['clear_for_compression']:return None
   req=auditing.make_card_request(inv['ledger'],audit['audit'],BUDGET)
 else:
  if g in ('none','full'):material='' if g=='none' else canonical(sources[pid])
  else:
   owner=donors(people)[pid] if g=='wrong' else pid
   prod=artifacts.get(('extract',owner,v))
   if prod is None:return None
   material=prod['prompt']
   if g=='tail':
    size=len(material);raw='\n'.join(s['role']+': '+s['text'] for s in sources[pid]['sources'])
    if size<=len(TAIL_NOTE) or len(raw)<size-len(TAIL_NOTE):raise ValueError('Exact character tail impossible')
    material=TAIL_NOTE+raw[-(size-len(TAIL_NOTE)):]
  req=choice_reader.make_request(material,queries,as_of=AS_OF,answer_format='text',reader_mode='standard')
  req={**req,'system':grouped.SYSTEM,'prompt':COMMON+req['prompt']}
 return {'model':MODEL,**req}

def bind(slot,answer,sources,artifacts,people):
 g,pid,v=slot['group'],slot['person'],slot['variant'];source=sources[pid]
 if g=='inventory':
  ledger=producers.accept_inventory(canonical(answer),source['sources'])
  auditing.make_audit_request(ledger) # Reject a future oversize dependency before spending its slot.
  return {'kind':'inventory','ledger':ledger,'source_sha256':digest(source),'answer_sha256':digest(answer)}
 if g=='audit':
  inv=artifacts['inventory',pid,v];audit=auditing.accept_audit(canonical(answer),inv['ledger'])
  if audit['clear_for_compression']:auditing.make_card_request(inv['ledger'],audit,BUDGET)
  return {'kind':'audit','audit':audit,'source_sha256':digest(source),'answer_sha256':digest(answer)}
 if g!='extract':raise ValueError('Only producer stages yield artifacts')
 if v=='grouped-v1':
  detail=grouped.bind(answer,source,BUDGET);text=detail['prompt.md'];partial=False;complete=None;audit_id=None
 else:
  inv=artifacts['inventory',pid,v];audit=artifacts['audit',pid,v]['audit']
  detail=auditing.accept_card(canonical(answer),inv['ledger'],audit,BUDGET);text=detail['prompt']
  if detail['status']=='budget_unmet':raise ValueError('Whole public coverage card exceeds512characters; no truncation')
  partial=bool(detail['accounting']['omissions']);complete=not partial;audit_id=audit['id']
 if len(text)>BUDGET:raise ValueError('Whole public budget differs')
 return {'kind':'extract','variant':v,'budget':BUDGET,'prompt':text,'characters':len(text),
  'source_sha256':digest(source),'answer_sha256':digest(answer),'partial':partial,'complete_accounting':complete,
  'audit_id':audit_id,'details':detail}

def control_summary(rows,people,answered):
 full=counts(rows,{pid:answered.get(('full',pid),{}) for pid in people})
 none=counts(rows,{pid:answered.get(('none','shared'),{}) for pid in people})
 return {'full':full,'none':none,'qualified':full['joint']['correct']==len(rows) and full['joint']['missing']==0 and full['personal_known']['correct']>none['personal_known']['correct'],'contemporary':True}


def summarize(rows,people,answers,artifacts):
 controls=control_summary(rows,people,{(g,pid):a for (g,v,pid),a in answers.items() if g in ('full','none')})
 report={'controls':controls,'variants':{},'passing_variants':[],'default_switch_authorized':False,
  'fresh_holdout':False,'human_fidelity_verified':False,'sampling_variability_measured':False,
  'cross_model_or_harness_validation':False,'developer_visible_corpus':True,'next_stage_authorized':False,
  'inventory_semantic_completeness_verified':False,'audit_clear_is_model_judgement':True}
 donor=donors(people)
 inventory_valid=sum(('inventory',pid,'coverage-v1') in artifacts for pid in people)
 audited=[artifacts['audit',pid,'coverage-v1']['audit'] for pid in people if ('audit',pid,'coverage-v1') in artifacts]
 stage={'inventory_valid':inventory_valid,'audit_imported':len(audited),'audit_clear':sum(a['clear_for_compression'] for a in audited),
        'audit_flagged':sum(not a['clear_for_compression'] for a in audited),'planned_profiles':len(people)}
 report['pipeline_stages']=stage
 for variant in VARIANTS:
  groups={g:counts(rows,{pid:a for (gg,v,pid),a in answers.items() if gg==g and v==variant}) for g in ('own','tail','wrong')}
  groups['wrong_against_donor']=counts(rows,{donor[pid]:a for (g,v,pid),a in answers.items() if g=='wrong' and v==variant})
  products=[artifacts['extract',pid,variant] for pid in people if ('extract',pid,variant) in artifacts]
  full=sum(prod['complete_accounting'] is True for prod in products)
  perfect=lambda g:groups[g]['joint']['correct']==len(rows) and groups[g]['joint']['missing']==0
  strict=controls['qualified'] and len(products)==len(people) and perfect('own') and perfect('wrong_against_donor')
  if variant=='coverage-v1':strict=strict and inventory_valid==len(people) and stage['audit_clear']==len(people) and full==len(people)
  if strict:report['passing_variants'].append(variant)
  den=controls['full']['joint']['correct']-controls['none']['joint']['correct'];num=groups['own']['joint']['correct']-controls['none']['joint']['correct']
  report['variants'][variant]={'groups':groups,'valid_products':len(products),'partial_products':sum(prod['partial'] for prod in products),
   'full_unit_accounting_products':full if variant=='coverage-v1' else None,'planned_products':len(people),
   'strict_retention':strict,'whole_budget_characters':BUDGET,
   'identity_specificity':strict and groups['wrong']['personal_known']['correct']<groups['own']['personal_known']['correct'],
   'observed_fidelity':{g:{'correct':z['joint']['correct'],'observed':z['joint']['planned']-z['joint']['missing'],'planned':z['joint']['planned']} for g,z in groups.items()},
   'own_losses':[{**e,'type':'unknown_not_preserved' if e['gold']=='U' else 'known_choice_lost'} for e in groups['own']['errors']],
   'normalized_accuracy_gain':{'value':num/den if den>0 else None,'numerator':num,'denominator':den,'is_likelihood_RIG':False}}
 b=report['variants']['grouped-v1'];c=report['variants']['coverage-v1']
 report['paired_descriptive_difference']={'valid_products':c['valid_products']-b['valid_products'],
  'own_planned_cells_correct':c['groups']['own']['joint']['correct']-b['groups']['own']['joint']['correct'],
  'pure_inventory_or_audit_causal_effect':False,'statistical_significance_claimed':False,
  'per_person':{pid:{v:report['variants'][v]['groups']['own']['by_person'][pid] for v in VARIANTS} for pid in people},
  'per_cohort':{co:{v:report['variants'][v]['groups']['own']['by_cohort'][co] for v in VARIANTS} for co in b['groups']['own']['by_cohort']}}
 return report


def replay(data):
 if (data['kind']!='consumed_actual_source_coverage_comparison' or data['fresh_holdout'] is not False
     or data['human_fidelity_verified'] is not False or data['developer_visible_corpus'] is not True):raise ValueError('Study claim changed')
 if data['requested_model']!=MODEL or data['as_of']!=AS_OF or data['budget_characters']!=BUDGET or data['variants']!=list(VARIANTS):raise ValueError('Frozen protocol changed')
 expected_paths={'runaway/'+m+'.py' for m in MODULES}|{'benchmarks/source-coverage-pipeline-v1/'+m+'.py' for m in PIPELINE}
 if set(data['runtime_sha256'])!=expected_paths:raise ValueError('Measured module inventory differs')
 for path,expected in data['runtime_sha256'].items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise ValueError('Measured module changed: '+path)
 sources,queries,rows=data['sources'],data['queries'],data['reference']['rows'];people=list(sources)
 if len(queries)!=40 or len(rows)!=80 or len({(r['person'],r['case']) for r in rows})!=80:raise ValueError('Planned denominator changed')
 byquery={q['id']:q for q in queries}
 if len(byquery)!=40:raise ValueError('Duplicate query')
 for pid,source in sources.items():
  helpers.validate_sources(source)
  if len(source['sources'])!=48:raise ValueError('Expected48messages per source')
 for row in rows:
  a,b=[byquery[q] for q in row['query_ids']];va,vb=list(a['options'].values()),list(b['options'].values())
  if a['scenario']!=b['scenario'] or vb!=va[1:]+va[:1]:raise ValueError('Option rotation differs')
  if row['gold']!='U' and row['gold'] not in va:raise ValueError('Known action not offered')
  index={s['id']:s for s in sources[row['person']]['sources']}
  for anchor in row['support']:
   s=index[anchor['source_id']]
   if s['role']!='user' or anchor['quote'] not in s['text']:raise ValueError('Reference anchor changed')
 slots=plan(people);records=data['records'];status=data['execution_status'];skipped=status['skipped']
 if len(records)>CAP or len({r['execution_id'] for r in records})!=len(records):raise ValueError('Call cap/independent IDs differ')
 if [r['slot'] for r in records]!=sorted(set(r['slot'] for r in records)):raise ValueError('Repeated/unordered slot')
 skipped_ids=[s['slot'] for s in skipped];record_ids=[r['slot'] for r in records]
 if set(skipped_ids)&set(record_ids) or len(set(skipped_ids))!=len(skipped_ids):raise ValueError('Skipped slot mapping differs')
 if status['status'] in ('complete','completed_with_pipeline_failures') and sorted(record_ids+skipped_ids)!=list(range(1,CAP+1)):raise ValueError('Complete scope has unaccounted slots')
 artifacts,answered,total,bad={},{},Counter(),[]
 stage_costs={}
 for rec in records:
  slot={k:rec[k] for k in ('slot','group','person','variant','budget')}
  if slot not in slots or rec['simulated'] is not False:raise ValueError('Slot/mock record differs')
  if slot['slot']>=6:
   c=control_summary(rows,people,{(g,pid):a for (g,v,pid),a in answered.items() if g in ('full','none')})
   if not c['qualified']:raise ValueError('Producer/read admitted without qualified controls')
  expected=request(slot,sources,queries,artifacts,people)
  if expected is None or expected!=rec['request'] or digest(expected)!=rec['request_sha256']:raise ValueError('Request source/artifact/budget/query binding differs')
  response=rec.get('response')
  if response is not None:
   original=(json.dumps(response,ensure_ascii=False,indent=2)+'\n').encode()
   if hashlib.sha256(original).hexdigest()!=rec['raw_response_sha256']:raise ValueError('Original response hash differs')
   prov=response['provenance']
   if prov['backend']!='codex' or prov['model_requested']!=MODEL:raise ValueError('Backend/model differs')
   value=optional_usage(prov)
   if value!=rec['usage']:raise ValueError('Usage binding differs')
  else:
   if rec['state']=='completed':raise ValueError('Missing completed raw response')
   failure=rec.get('failure_provenance');value=None if not failure else optional_usage(failure)
   if value!=rec['usage']:raise ValueError('Failed-call usage binding differs')
  if value is not None:total.update(value)
  stage=stage_costs.setdefault(rec['group']+':'+str(rec['variant']),{'local_calls':0,'known_usage':Counter(),'missing_usage':0})
  stage['local_calls']+=1
  if value is None:stage['missing_usage']+=1
  else:stage['known_usage'].update(value)
  if rec['state']!='completed':continue
  answer=parse_answer(response['raw']);schema_check(answer,expected['schema'])
  if rec['group'] in ('inventory','audit','extract'):
   try:artifact=bind(slot,answer,sources,artifacts,people)
   except (ValueError,TypeError,KeyError) as exc:
    if rec.get('product_invalid') is not True or 'artifact' in rec:raise ValueError('Invalid producer status differs')
    bad.append({**slot,'error_type':type(exc).__name__,'message':str(exc),'repair':False});continue
   if rec.get('product_invalid') or artifact!=rec.get('artifact'):raise ValueError('Actual artifact changed')
   original=(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n').encode()
   if hashlib.sha256(original).hexdigest()!=rec['artifact_sha256']:raise ValueError('Artifact hash differs')
   if bool(rec.get('audit_flagged'))!=(slot['group']=='audit' and not artifact['audit']['clear_for_compression']):raise ValueError('Audit gate flag changed')
   if bool(rec.get('partial_product'))!=(slot['group']=='extract' and artifact['partial']):raise ValueError('Partial-card flag changed')
   artifacts[slot['group'],slot['person'],slot['variant']]=artifact
  else:
   choice_reader.decode_response(queries,answer,answer_format='text',reader_mode='standard')
   answered[rec['group'],rec['variant'],rec['person']]=answer
 for s in skipped:
  slot={k:s[k] for k in ('slot','group','person','variant','budget')}
  if slot not in slots or request(slot,sources,queries,artifacts,people) is not None:raise ValueError('Unjustified skipped dependency')
 exported=[dict(group=g,person=pid,variant=v,artifact=a) for (g,pid,v),a in artifacts.items()]
 if exported!=data['artifacts']:raise ValueError('Exported artifact inventory differs')
 if sum(r['usage'] is None for r in records)!=status['missing_usage']:raise ValueError('Missing usage differs')
 if dict(total)!=data['known_usage'] or bad!=status['invalid_products']:raise ValueError('Usage/invalid producer evidence differs')
 for stage in stage_costs.values():stage['known_usage']=dict(stage['known_usage'])
 if stage_costs!=data['stage_costs']:raise ValueError('Stage cost attribution differs')
 result=summarize(rows,people,answered,artifacts)
 if status['control_gate'] is not None and status['control_gate']!=result['controls']:raise ValueError('Control gate changed')
 result.update(attempts=len(records),status=status['status'],missing_usage=status['missing_usage'])
 if result!=data['expected_results']:raise ValueError('Frozen results changed')
 return result


def check():
 here=Path(__file__).resolve().parent;raw=(here/'observed.synthetic.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=(here/'observed.sha256').read_text().strip():raise ValueError('Recorded fixture changed')
 data=json.loads(raw);r=replay(data)
 return {'status':'consumed_source_coverage_comparison_replay_pass','new_model_calls':0,'attempts':r['attempts'],
         'full_correct':r['controls']['full']['joint']['correct'],'none_correct':r['controls']['none']['joint']['correct'],
         'pipeline_stages':r['pipeline_stages'],
         'variants':{v:{'valid_products':z['valid_products'],'partial_products':z['partial_products'],
                        'own':z['groups']['own']['joint'],'strict_retention':z['strict_retention']} for v,z in r['variants'].items()},
         'passing_variants':r['passing_variants'],'known_tokens':data['known_usage'].get('total_tokens'),
         'human_fidelity_verified':False,'fresh_holdout':False}

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False))
