"""Unapproved source-only coverage comparison; no service backend."""
import argparse,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
sys.path.insert(0,str(ROOT))
PREFIX='benchmarks/ambiguous-source-repeat-v1'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
base=load('coverage_comparison_original',ROOT/'benchmarks/epistemic-transfer-v1/plan.py')
coverage=load('coverage_comparison_guidance',ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')
read,sha,digest,choice_reader=base.read,base.sha,base.digest,base.choice_reader
PROFILES=('c2v','d9n');METHODS=('source-order-v3','object-coverage-guidance-v1')
MODEL,AS_OF,CAP,BUDGET='gpt-6.1-sol','2026-11-02',27,1536

def inputs():
 data=base.inputs();rows=[r for r in data['rows']if r['person']in PROFILES]
 assert len(rows)==30 and sum(r['gold']!='U'for r in rows)==10
 return {'sources':{pid:data['sources'][pid]for pid in PROFILES},'queries':data['queries'],'rows':rows,
  'design':{'kind':'consumed_ambiguous_withdrawn_source_repeat','profiles':2,'source_messages':44,
   'primary_cases_per_method_view':30,'known':10,'unknown':20,
   'personal_known':sum(r['personal_known']for r in rows),'derived_known':sum(r['derived_known']for r in rows),
   'independent_holdout':False,'independent_semantic_acceptance':False,'real_person_fidelity_verified':False}}
def bank(pid):
 if pid in PROFILES or pid=='shared_all':return 'all'
 raise ValueError('Foreign bank')
def factory(method):
 if method==METHODS[0]:return base.candidate
 if method==METHODS[1]:return coverage
 raise ValueError('Foreign method')
def parent(slot):return slot['profile'],slot['method'],slot['generation']
def cells():
 return [(pid,m,g)for g in(0,1)for i,pid in enumerate(PROFILES)
  for m in(METHODS if(i+g)%2==0 else tuple(reversed(METHODS)))]
def slots():
 jobs=[('none','shared_all',None,None,None,None)]+[('full',pid,None,None,None,None)for pid in PROFILES]
 for pid,m,g in cells():
  jobs.append(('extract',pid,m,g,None,None))
  jobs += [('read',pid,m,g,r,'card')for r in(0,1)]
 return [{'slot':i+1,'kind':k,'profile':pid,'method':m,'generation':g,'budget':BUDGET if m else None,
  'read_repeat':r,'view':v,'key':':'.join(map(str,(k,pid,m,g,r,v)))}for i,(k,pid,m,g,r,v)in enumerate(jobs)]

def bind(slot,answer):
 if slot not in slots()or slot['kind']!='extract':raise ValueError('Only own planned extraction may bind')
 return factory(slot['method']).bind(answer,inputs()['sources'][slot['profile']],BUDGET)
transcript=base.transcript
material=base.material

def request(slot,parents=None):
 if slot not in slots():raise ValueError('Outside frozen43schedule')
 data=inputs();pid=slot['profile'];system=base.base.old.old.grouped_support.SYSTEM
 if slot['kind']=='extract':return {'model':MODEL,'system':system,**factory(slot['method']).make_request(data['sources'][pid],BUDGET)}
 if slot['kind']=='none':text=''
 elif slot['kind']=='full':text=transcript(data['sources'][pid])
 else:
  if parent(slot)not in(parents or{}):return None
  own=next(s for s in slots()if s['kind']=='extract'and parent(s)==parent(slot))
  text=material(pid,bind(own,parents[parent(slot)])['prompt.md'],slot['view'])
 req=choice_reader.make_request(text,data['queries']['all'],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'model':MODEL,'system':system,**req,'prompt':base.base.old.old.COMMON+req['prompt']}
def implementation():
 files={'scripts/capture_codex_failure.py':sha(ROOT/'scripts/capture_codex_failure.py'),**base.implementation(),'benchmarks/object-coverage-guidance-v1/candidate.py':sha(ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')}
 files.update({PREFIX+'/'+path.name:sha(path)for path in HERE.glob('*.py')})
 return dict(sorted(files.items()))
def values():
 data=inputs()
 proposal={'kind':'unapproved_ambiguous_source_repeat27','model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':27,
  'stages':{'shared_no_memory':1,'own_full_controls':2,'source_only_extractions':8,'card_reads':16},
  'source_messages':44,'profiles':list(PROFILES),'unique_public_forms':30,'methods':list(METHODS),
  'whole_public_character_cap':1536,'generations_per_profile_method':2,'reads_per_parent_view':2,
  'answers_per_primary_case_method_view':8,'primary_cases_per_method_view':30,'known':10,'unknown':20,
  'control':'Shared none then both full controls;each full15/15bothorders,no missing,and personal-known gain.Before all extraction.',
  'schedule':'For each generation,profiles c2v then d9n;alternate baseline/guidance order by profile+generation parity.Each extraction immediately followed by own two reads.No shared conversation or previous outputs.',
  'source_only':'Own22fictional messages,budget,fixed header/guide/guidance/schema only.No questions,reference,old cards/graphs,responses/scores,manual bindings or author parameters.',
  'intervention':'Previously fixed generic prefix only.No encoder/schema/wire/binder/compiler/reader/budget change.',
  'endpoint':'Each method fixed30cases across two independent extraction calls,two reads,two orders.All8correct;no best-of or pooling as independent people;not a population stability estimate.',
  'invalid_parent':'Skip only own2reads;own15cases remain missing in30case method endpoint in strict method endpoint.No repair or replacement.',
  'fatal':'Any control,transport,wire/schema/decode,unknownusage,model,runtime,input or ownedguard failure stops all remainder.Unusedexpire.',
  'capture':'Existing serial safe-completion observer around unchanged one-child helper;no retry or partial-answer acceptance.',
  'aggregate_token_cap':None,'money_cap':None,'local_child_timeout_seconds':180,'max_nominal_timeout_sum_seconds':4860,
  'not_aggregate_duration_spend_or_upstream_cancellation_cap':True,'retry':False,'repair':False,'resume':False,'replenishment':False,
  'tail_reads':0,'independent_holdout':False,'independent_semantic_acceptance':False,'real_person_fidelity_verified':False,
  'production_default_changed':False,'old_scopes_reopened':False,'old43_scores_replaced':False,'approved':False,'new_service_authority':False,
  'execution_condition':'Fresh direct human grant and all three PR54 CI checks at4e0f65fed0804e5d3fea0dd9f94ba7a5c0a9049c succeed.'}
 return {'proposal.json':proposal,'sources.json':data['sources'],'queries.public.json':data['queries'],
  'reference.private.json':data['rows'],'design.json':data['design'],'slots.json':slots(),
  'static-requests.json':{s['key']:request(s)for s in slots()if s['kind']!='read'},
  'dynamic-rules.json':{'slots':[s for s in slots()if s['kind']=='read'],'builder':PREFIX+'/plan.py:request','own_valid_parent_only':True},
  'implementation-sha256.json':implementation()}
def prepare(destination):
 contents=values();destination.mkdir(exist_ok=False)
 for name,value in contents.items():(destination/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (destination/'manifest.json').write_text(json.dumps({'files':{n:sha(destination/n)for n in sorted(contents)},'new_model_calls':0},indent=2)+'\n',encoding='utf8')
 return contents['proposal.json']
def verify(root,*,reconstruct=True):
 for name,expected in read(root/'manifest.json')['files'].items():
  path=Path(name)
  if path.is_absolute()or'..'in path.parts or(root/path).is_symlink()or sha(root/path)!=expected:raise ValueError('Frozen input drift')
 if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Implementation drift')
 if reconstruct and any(read(root/n)!=v for n,v in values().items()):raise ValueError('Reconstruction drift')
 return True
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args();print(json.dumps(prepare(args.out),ensure_ascii=False,indent=2))
