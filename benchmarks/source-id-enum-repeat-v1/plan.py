"""Frozen preparation for59source-ID reviews/reads; no backend or live authority."""
import copy,importlib.util,json,sys
from functools import lru_cache
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
seed=load('repeat35_seed',ROOT/'benchmarks/source-id-review-v1/plan.py')
base,reviewer=seed.base,seed.reviewer
enumerated=load('enum59_candidate',ROOT/'benchmarks/source-id-enum-v1/candidate.py')
METHODS=('existing','enumerated')
read,sha,digest=seed.read,seed.sha,seed.digest
MODEL,AS_OF,CAP,BUDGET=seed.MODEL,seed.AS_OF,59,1536
PROFILES=('c2v','f7s')
PARENTS=(('p0','c2v','ambiguous-source-repeat-v1',4,585,'previously_complete'),
 ('p1','c2v','ambiguous-source-repeat-v1',19,312,'previously_incomplete'),
 ('p2','f7s','remaining-source-repeat-v1',22,434,'previously_complete'),
 ('p3','f7s','remaining-source-repeat-v1',49,240,'previously_incomplete'))
@lru_cache(maxsize=1)
def _load_inputs():
 parents={};sources={};raw=base.inputs()
 for key,person,archive,slot,chars,band in PARENTS:
  file=ROOT/'benchmarks'/archive/'measured.synthetic.json'
  if sha(file)!=file.with_suffix('.sha256').read_text().strip():raise ValueError('Parent archive drift')
  data=read(file)
  if data['queries']!=raw['queries']:raise ValueError('Original public forms differ')
  if [r for r in data['reference_rows']if r['person']==person]!=[r for r in raw['rows']if r['person']==person]:raise ValueError('Original reference differs')
  record=next(r for r in data['records']if r['slot']==slot)
  if record['profile']!=person or record['card']['characters']!=chars:raise ValueError('Fixed parent differs')
  own=data['sources'][person]
  if own!=raw['sources'][person]:raise ValueError('Original source differs')
  graph=seed.parse_answer(record['raw'])
  public=reviewer.legacy.bind(graph,own,BUDGET)['prompt.md']
  if public!=record['card']['prompt']:raise ValueError('Parent binding differs')
  if person in sources and sources[person]!=own:raise ValueError('Person source differs')
  sources[person]=own
  parents[key]={'profile':person,'draft':graph,'prompt':public,'characters':chars,
   'origin':{'archive':archive,'archive_sha256':sha(file),'slot':slot,'request_sha256':record['request_sha256'],
    'raw_value_sha256':record['raw_value_sha256'],'artifact_sha256':record['artifact_sha256'],'prior_band':band}}
 for first,second in(('p0','p1'),('p2','p3')):
  if parents[first]['origin']['request_sha256']!=parents[second]['origin']['request_sha256']:raise ValueError('Pair not same original producer request')
 raw=base.inputs()
 return {'sources':sources,'parents':parents,'queries':raw['queries'],'rows':[r for r in raw['rows']if r['person']in PROFILES]}
def inputs():
 data=_load_inputs()
 for parent in data['parents'].values():
  origin=parent['origin'];file=ROOT/'benchmarks'/origin['archive']/'measured.synthetic.json'
  if sha(file)!=origin['archive_sha256']or sha(file)!=file.with_suffix('.sha256').read_text().strip():raise ValueError('Cached origin drift')
 return copy.deepcopy(data)
def slots():
 values=[]
 def add(kind,profile=None,parent=None,review_repeat=None,read_repeat=None,view=None,method=None):
  values.append({'slot':len(values)+1,'kind':kind,'profile':profile,'parent':parent,
   'review_repeat':review_repeat,'read_repeat':read_repeat,'view':view,'method':method})
 add('none')
 for profile in PROFILES:add('full',profile)
 for repeat,order in enumerate((('p0','p3','p2','p1'),('p1','p2','p3','p0'))):
  for parent in order:
   person=dict((p[0],p[1])for p in PARENTS)[parent]
   if repeat==0:add('read',person,parent,read_repeat=0,view='original')
   methods=METHODS if(int(parent[1:])+repeat)%2==0 else tuple(reversed(METHODS))
   for method in methods:
    add('review',person,parent,review_repeat=repeat,method=method)
    for read_repeat in(0,1):add('read',person,parent,repeat,read_repeat,'reviewed',method)
   if repeat==1:add('read',person,parent,read_repeat=1,view='original')
 return values

def request(slot,reviewed=None):
 if slot not in slots():raise ValueError('Outside frozen59slots')
 data=inputs();person=slot['profile'];parent=slot['parent'];system=base.base.old.old.grouped_support.SYSTEM
 if slot['kind']=='review':
  factory=reviewer if slot['method']=='existing'else enumerated
  req=factory.make_request(data['sources'][person],data['parents'][parent]['draft'],BUDGET)
  return {'model':MODEL,'system':system,**req}
 if slot['kind']=='none':text=''
 elif slot['kind']=='full':text=base.transcript(data['sources'][person])
 elif slot['view']=='original':text=data['parents'][parent]['prompt']
 elif reviewed is None:return None
 else:text=reviewer.bind(reviewed,data['sources'][person],BUDGET)['prompt.md']
 req=base.choice_reader.make_request(text,data['queries']['all'],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'model':MODEL,'system':system,**req,'prompt':base.base.old.old.COMMON+req['prompt']}
def implementation():
 files=seed.implementation()
 file=ROOT/'benchmarks/ambiguous-source-repeat-v1/measured.synthetic.json';files[str(file.relative_to(ROOT))]=sha(file)
 files['benchmarks/source-id-enum-v1/candidate.py']=sha(ROOT/'benchmarks/source-id-enum-v1/candidate.py')
 files.update({'benchmarks/source-id-enum-repeat-v1/'+p.name:sha(p)for p in HERE.glob('*.py')})
 return dict(sorted(files.items()))
@lru_cache(maxsize=1)
def _values_cached(fingerprint):
 if digest(implementation())!=fingerprint:raise ValueError('Implementation drift during preparation')
 data=inputs();proposal={'kind':'unapproved_source_id_enum_repeat59','model':MODEL,'as_of':AS_OF,
  'max_new_local_cli_attempts':59,'stages':{'none':1,'full':2,'review':16,'original_reads':8,'reviewed_reads':32},
  'source_messages':44,'unique_public_forms':30,'fixed_parents':4,'reviews_per_parent_per_method':2,'methods':list(METHODS),'reads_per_card':2,
  'whole_public_character_cap':BUDGET,'unique_person_cases':30,'parent_case_cells':60,
  'known_unique_person_cases':13,'unknown_unique_person_cases':17,'primary_cases_per_parent':15,
  'acceptance_target':'Each method keeps60parent/case cells;both reviews require8/8answers.Report per-review4answer endpoints,availability,known/unknown,recovery,observed regression and missing separately.No default promotion follows.',
  'original_answers_per_parent_case':4,'each_review_answers_per_case':4,'both_reviews_answers_per_case':8,
  'selection':'Posthoc paired complete/incomplete drafts from two consumed fictional worlds;same original producer request within each person.Not independent people or holdout.',
  'review_input':'Only own22source messages and unchanged original quoted draft graph.No question,reference,old reader response/score,previous reviewed graph,manual correction or author parameter.',
  'control':'All own full15/15bothorders,no missing,and personal-known gain over shared none,before any parent read/review.',
  'invalid_product':'Out-of-source IDs are binding-invalid under both methods,including request-enum-only violation;record conformance separately.Binding/budget-invalid review skips only its own2reads;keeps missing in its parent denominator.Other repeats/original readers continue.',
  'fatal':'Control,transport,shared structural wire/schema/decode,unknownusage,model,input/runtime or ownedguard failure stops remainder.Unusedexpire.No retry,manual repair,resume or replenishment.',
  'reviewer_schema_compiler_reader_unchanged':False,'prompt_binder_compiler_reader_unchanged':True,'only_request_anchor_schema_changes':True,'request_enum_only_id_violation_is_product_invalid':True,'same_reference_rejection_class_for_both_methods':True,'new_initial_extractions':0,
  'fresh_initial_generation_stability_verified':False,'independent_holdout':False,'real_person_fidelity_verified':False,
  'source_reference_semantics_verified':False,'production_default_changed':False,'old_scores_replaced':False,
  'aggregate_token_cap':None,'money_cap':None,'local_child_timeout_seconds':180,'approved':False,'new_service_authority':False,
  'execution_condition':'Fresh direct human grant and all three CI jobs successful at the recorded exact published implementation head.'}
 return {'proposal.json':proposal,'sources.json':data['sources'],'parents.public.json':data['parents'],
  'queries.public.json':data['queries'],'reference.private.json':data['rows'],'slots.json':slots(),
  'static-requests.json':{str(s['slot']):request(s)for s in slots()if s['view']!='reviewed'},
  'dynamic-rules.json':{'slots':[s for s in slots()if s['view']=='reviewed'],
   'builder':'benchmarks/source-id-enum-repeat-v1/plan.py:request','only_own_parent_method_and_review_repeat':True},
  'implementation-sha256.json':implementation()}
def values():
 inputs() # Recheck sealed archive bytes even when requests are cached.
 return copy.deepcopy(_values_cached(digest(implementation())))
def prepare(destination):
 destination=Path(destination);destination.mkdir(exist_ok=False)
 for name,value in values().items():(destination/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 (destination/'manifest.json').write_text(json.dumps({'files':{n:sha(destination/n)for n in sorted(values())},'new_model_calls':0},indent=2)+'\n')
def verify(root):
 for name,expected in read(root/'manifest.json')['files'].items():
  rel=Path(name)
  if rel.is_absolute()or'..'in rel.parts or(root/rel).is_symlink()or sha(root/rel)!=expected:raise ValueError('Frozen input drift')
 if any(read(root/name)!=value for name,value in values().items()):raise ValueError('Input reconstruction differs')
 return True
