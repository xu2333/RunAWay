"""Consumed actual budget frontier replay, never calls a service or repairs output."""
from collections import Counter
import hashlib,importlib.util,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from runaway import support_extract,choice_reader
from runaway.card import canonical,digest
from runaway.constraint_extract import parse_answer,check as schema_check
from runaway.prompt_codec import unpack
spec=importlib.util.spec_from_file_location('frontier_count_helpers',ROOT/'benchmarks/natural-controls-v1/check.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
counts=helpers.counts
BUDGETS=(384,512,768)
MODULES=('card','choice_reader','choice_contract','constraint_extract','portable','profile','prompt_codec','scope_rows','support_extract','text_integrity')
TAIL_NOTE='原始多角色记录尾部，开头可能被截断；只把完整标明user的决定作为证据。\n'

def obj_digest(value):return digest(canonical(value))
def optional_usage(provenance):
 try:return helpers.usage(provenance)
 except ValueError:return None
def donors(people):return {p:people[(i+1)%len(people)] for i,p in enumerate(people)}
def plan(people):
 if len(people)!=4 or len(set(people))!=4:raise ValueError('Four distinct profiles required')
 pairs=[('none','shared',None)]+[('full',p,None) for p in people]
 for r in range(3):pairs += [('extract',p,BUDGETS[(r+i)%3]) for i,p in enumerate(people)]
 for br in range(3):
  for gr in range(3):pairs += [(('own','tail','wrong')[(gr+i)%3],p,BUDGETS[(br+i)%3]) for i,p in enumerate(people)]
 return [{'slot':i+1,'group':g,'person':p,'budget':b} for i,(g,p,b) in enumerate(pairs)]

def request(slot,sources,queries,products,people):
 g,pid,b=slot['group'],slot['person'],slot['budget']
 if g=='extract':return dict(support_extract.make_request(sources[pid],b),model='gpt-6.1-sol',system=support_extract.SYSTEM)
 if g in ('none','full'):material='' if g=='none' else canonical(sources[pid])
 else:
  owner=donors(people)[pid] if g=='wrong' else pid
  if (b,owner) not in products:return None
  material=products[b,owner]['prompt']
  if g=='tail':
   size=len(material);raw='\n'.join(s['role']+': '+s['text'] for s in sources[pid]['sources'])
   if size<=len(TAIL_NOTE) or len(raw)<size-len(TAIL_NOTE):raise ValueError('Exact tail impossible')
   material=TAIL_NOTE+raw[-(size-len(TAIL_NOTE)):]
 req=choice_reader.make_request(material,queries,as_of='2026-10-23',answer_format='text',reader_mode='standard')
 return dict(req,model='gpt-6.1-sol',system=support_extract.SYSTEM,prompt=helpers.COMMON+req['prompt'])

def bind(answer,source,budget):
 files=support_extract.bind(answer,source,budget,layout='paragraph')
 return {'prompt':files['prompt.md'],'characters':len(files['prompt.md']),'source_sha256':obj_digest(source),
         'answer_sha256':obj_digest(answer),'budget':budget,'files':files}

def control_summary(rows,people,answered):
 full=counts(rows,{pid:answered.get(('full',pid),{}) for pid in people})
 none=counts(rows,{pid:answered.get(('none','shared'),{}) for pid in people})
 qualified=full['joint']['correct']==len(rows) and full['joint']['missing']==0 and full['personal_known']['correct']>none['personal_known']['correct']
 return {'full':full,'none':none,'qualified':qualified,'contemporary':True}

def summarize(rows,people,answered,valid):
    controls=control_summary(rows,people,{(g,pid):a for (g,b,pid),a in answered.items() if g in ('full','none')})
    report={'controls':controls,'budgets':{},'minimum_tested_passing_budget':None,
            'fresh_holdout':False,'human_fidelity_verified':False,'sampling_variability_measured':False,
            'cross_model_or_harness_validation':False,'developer_visible_corpus':True,'next_stage_authorized':False}
    donor_lookup=donors(people)
    for budget in BUDGETS:
        groups={g:counts(rows,{pid:a for (gg,b,pid),a in answered.items() if gg==g and b==budget}) for g in ('own','tail','wrong')}
        groups['wrong_against_donor']=counts(rows,{donor_lookup[pid]:a for (g,b,pid),a in answered.items() if g=='wrong' and b==budget})
        perfect=lambda g:groups[g]['joint']['correct']==len(rows) and groups[g]['joint']['missing']==0
        strict=controls['qualified'] and sum((budget,pid) in valid for pid in people)==len(people) and perfect('own') and perfect('wrong_against_donor')
        if strict and report['minimum_tested_passing_budget'] is None:report['minimum_tested_passing_budget']=budget
        den=controls['full']['joint']['correct']-controls['none']['joint']['correct']
        num=groups['own']['joint']['correct']-controls['none']['joint']['correct']
        losses=[{**e,'type':'unknown_not_preserved' if e['gold']=='U' else 'known_choice_lost'} for e in groups['own']['errors']]
        report['budgets'][str(budget)]={'groups':groups,'valid_products':sum((budget,pid) in valid for pid in people),
            'planned_products':len(people),'strict_retention':strict,
            'identity_specificity':strict and groups['wrong']['personal_known']['correct']<groups['own']['personal_known']['correct'],
            'own_losses':losses,'normalized_accuracy_gain':{'value':num/den if den>0 else None,'numerator':num,'denominator':den,'is_likelihood_RIG':False}}
    return report


def replay(data):
 if (data['kind']!='consumed_actual_heterogeneous_synthetic_frontier' or data['fresh_holdout'] is not False
     or data['human_fidelity_verified'] is not False or data['developer_visible_corpus'] is not True):raise ValueError('Study claim changed')
 if data['requested_model']!='gpt-6.1-sol' or data['as_of']!='2026-10-23' or data['budgets']!=list(BUDGETS):raise ValueError('Frozen protocol changed')
 if set(data['runtime_sha256'])!={'runaway/'+m+'.py' for m in MODULES}:raise ValueError('Runtime inventory differs')
 for path,expected in data['runtime_sha256'].items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise ValueError('Measured production runtime changed: '+path)
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
 if len(records)>53 or len({r['execution_id'] for r in records})!=len(records):raise ValueError('Call cap/independent IDs differ')
 if [r['slot'] for r in records]!=sorted(set(r['slot'] for r in records)):raise ValueError('Repeated/unordered slot')
 skipped_ids=[s['slot'] for s in skipped];record_ids=[r['slot'] for r in records]
 if set(skipped_ids)&set(record_ids) or len(set(skipped_ids))!=len(skipped_ids):raise ValueError('Skipped slot mapping differs')
 if status['status'] in ('complete','completed_with_invalid_products') and sorted(record_ids+skipped_ids)!=list(range(1,54)):raise ValueError('Complete scope has unaccounted slots')
 products,answered,total,bad={},{},Counter(),[]
 for rec in records:
  slot={k:rec[k] for k in ('slot','group','person','budget')}
  if slot not in slots or rec['simulated'] is not False:raise ValueError('Slot/mock record differs')
  if slot['slot']>=6:
   c=control_summary(rows,people,{(g,pid):a for (g,b,pid),a in answered.items() if g in ('full','none')})
   if not c['qualified']:raise ValueError('Extraction/read admitted without qualified controls')
  expected=request(slot,sources,queries,products,people)
  if expected is None or expected!=rec['request'] or obj_digest(expected)!=rec['request_sha256']:raise ValueError('Request source/card/budget/query binding differs')
  response=rec.get('response')
  if response is not None:
   original=(json.dumps(response,ensure_ascii=False,indent=2)+'\n').encode()
   if hashlib.sha256(original).hexdigest()!=rec['raw_response_sha256']:raise ValueError('Original response hash differs')
   prov=response['provenance']
   if prov['backend']!='codex' or prov['model_requested']!=data['requested_model']:raise ValueError('Backend/model differs')
   value=optional_usage(prov)
   if value!=rec['usage']:raise ValueError('Usage binding differs')
  else:
   if rec['state']=='completed':raise ValueError('Missing completed raw response')
   failure=rec.get('failure_provenance')
   value=None if not failure else optional_usage(failure)
   if value!=rec['usage']:raise ValueError('Failed-call usage binding differs')
  if value is not None:total.update(value)
  if rec['state']!='completed':continue
  answer=parse_answer(response['raw']);schema_check(answer,expected['schema'])
  if rec['group']=='extract':
   try:product=bind(answer,sources[rec['person']],rec['budget'])
   except (ValueError,TypeError,KeyError) as exc:
    if rec.get('product_invalid') is not True:raise ValueError('Invalid product status changed')
    bad.append({**slot,'error_type':type(exc).__name__,'message':str(exc),'repair':False})
    if rec['person'] in data['products'][str(rec['budget'])]:raise ValueError('Invalid product exported')
    continue
   if rec.get('product_invalid') or product!=data['products'][str(rec['budget'])][rec['person']]:raise ValueError('Actual product changed')
   files=product['files']
   if product['characters']!=len(product['prompt']) or product['characters']>rec['budget'] or unpack(product['prompt'],files['encoding.private.json'])!=files['expanded.private.md']:raise ValueError('Whole budget/expansion differs')
   products[rec['budget'],rec['person']]=product
  else:
   choice_reader.decode_response(queries,answer,answer_format='text',reader_mode='standard')
   answered[rec['group'],rec['budget'],rec['person']]=answer
 for s in skipped:
  slot={k:s[k] for k in ('slot','group','person','budget')}
  if slot not in slots or s['group'] not in ('own','tail','wrong') or request(slot,sources,queries,products,people) is not None:raise ValueError('Unjustified skipped dependency')
 if set(data['products'])!={str(b) for b in BUDGETS} or {(int(b),pid) for b,group in data['products'].items() for pid in group}!=set(products):raise ValueError('Exported product inventory differs')
 if sum(r['usage'] is None for r in records)!=status['missing_usage']:raise ValueError('Missing usage differs')
 if dict(total)!=data['known_usage'] or bad!=status['invalid_products']:raise ValueError('Usage/invalid product evidence differs')
 result=summarize(rows,people,answered,set(products))
 if status['control_gate'] is not None and status['control_gate']!=result['controls']:raise ValueError('Control gate changed')
 result.update(attempts=len(records),status=status['status'],missing_usage=status['missing_usage'])
 if result!=data['expected_results']:raise ValueError('Frozen results changed')
 return result


def check():
 here=Path(__file__).resolve().parent;raw=(here/'observed.synthetic.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=(here/'observed.sha256').read_text().strip():raise ValueError('Recorded fixture changed')
 data=json.loads(raw);r=replay(data)
 return {'status':'consumed_frontier_replay_pass','new_model_calls':0,'attempts':r['attempts'],
         'full_correct':r['controls']['full']['joint']['correct'],'none_correct':r['controls']['none']['joint']['correct'],
         'budgets':{b:{'valid_products':v['valid_products'],'own':v['groups']['own']['joint'],'strict_retention':v['strict_retention']} for b,v in r['budgets'].items()},
         'minimum_tested_passing_budget':r['minimum_tested_passing_budget'],'known_tokens':data['known_usage'].get('total_tokens'),
         'human_fidelity_verified':False,'fresh_holdout':False}

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False))
