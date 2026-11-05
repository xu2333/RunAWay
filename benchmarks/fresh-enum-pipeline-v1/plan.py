"""Unapproved45-attempt fresh-source pipeline; no service backend."""
import copy,importlib.util,json,sys
from functools import lru_cache
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
seed=load('fresh_pipeline_seed',ROOT/'benchmarks/source-id-enum-repeat-v1/plan.py')
corpus=load('fresh_pipeline_corpus',HERE/'corpus.py')
producer=load('fresh_pipeline_producer',ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')
reviewer=seed.enumerated
choice_reader=seed.base.choice_reader
read,sha,digest=seed.read,seed.sha,seed.digest
PROFILES=corpus.PROFILES
MODEL,AS_OF,BUDGET,CAP='gpt-6.1-sol','2026-11-04',1536,45
VIEWS=('draft','reviewed','draft_tail','reviewed_tail')
def inputs():return corpus.build()
transcript=seed.base.transcript

def slots():
 jobs=[]
 def add(kind,pid=None,view=None,repeat=None):jobs.append({'slot':len(jobs)+1,'kind':kind,'profile':pid,'view':view,'read_repeat':repeat})
 add('none')
 for pid in PROFILES:add('full',pid)
 for i,pid in enumerate(PROFILES):
  add('extract',pid);add('review',pid)
  order=VIEWS if i%2==0 else tuple(reversed(VIEWS))
  for repeat in(0,1):
   for view in(order if repeat==0 else tuple(reversed(order))):add('read',pid,view,repeat)
 return jobs

def bind(pid,stage,answer):
 if pid not in PROFILES or stage not in('draft','reviewed'):raise ValueError('Foreign parent')
 factory=producer if stage=='draft'else reviewer
 return factory.bind(answer,inputs()['sources'][pid],BUDGET)

def material(pid,view,graphs):
 if view not in VIEWS:raise ValueError('Foreign view')
 stage='reviewed'if view.startswith('reviewed')else'draft'
 if(pid,stage)not in graphs:return None
 prompt=bind(pid,stage,graphs[pid,stage])['prompt.md']
 if not 0<len(prompt)<=BUDGET:raise ValueError('Public budget differs')
 if not view.endswith('_tail'):return prompt
 raw=transcript(inputs()['sources'][pid])
 if len(raw)<=BUDGET:raise ValueError('Tail control must come from longer source')
 return raw[-len(prompt):]

def request(slot,graphs=None):
 if slot not in slots():raise ValueError('Outside frozen45schedule')
 graphs={}if graphs is None else graphs;data=inputs();pid=slot['profile'];system=seed.base.base.old.old.grouped_support.SYSTEM
 if slot['kind']=='extract':req=producer.make_request(data['sources'][pid],BUDGET)
 elif slot['kind']=='review':
  if(pid,'draft')not in graphs:return None
  req=reviewer.make_request(data['sources'][pid],graphs[pid,'draft'],BUDGET)
 else:
  text=''if slot['kind']=='none'else transcript(data['sources'][pid])if slot['kind']=='full'else material(pid,slot['view'],graphs)
  if text is None:return None
  req=choice_reader.make_request(text,data['queries']['all'],as_of=AS_OF,answer_format='text',reader_mode='standard')
  req['prompt']=seed.base.base.old.old.COMMON+req['prompt']
 return {'model':MODEL,'system':system,**req}

def implementation():
 files=seed.implementation()
 files.update({'benchmarks/fresh-enum-pipeline-v1/'+p.name:sha(p)for p in HERE.glob('*.py')})
 return dict(sorted(files.items()))
@lru_cache(maxsize=1)
def _values(fingerprint):
 if digest(implementation())!=fingerprint:raise ValueError('Implementation drift')
 data=inputs();chars={p:sum(len(s['text'])for s in src['sources'])for p,src in data['sources'].items()}
 if min(chars.values())<=BUDGET:raise ValueError('Text-only source must exceed card ceiling')
 proposal={'kind':'unapproved_fresh_enum_pipeline45','model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':CAP,
  'stages':{'controls':5,'fresh_initial_extractions':4,'enum_reviews':4,'card_readers':16,'equal_character_tail_readers':16},
  **data['design'],'source_text_characters':chars,'whole_public_character_cap':BUDGET,'views':list(VIEWS),
  'answers_per_case_per_view':4,'initial_generation_stability_verified':False,'review_repetition_stability_verified':False,
  'control':'All four full16/16bothorders,no missing,personal-known gain over shared none,before any extraction.',
  'pipeline':'Each person one fresh source-only coverage extraction,one source+own-draft enum review,then two reads of each card and its own exact-character role-labelled transcript suffix.No chosen historical bad card.',
  'source_only':'Producer sees own sources only plus fixed schema/guide/budget.Reviewer additionally sees its own fresh draft.No questions,reference,author evidence,old cards/response/score or manual corrections.',
  'reader':'Only complete own public card or exact-character own-source suffix,plus32common question forms.No appended decoder/source index.',
  'reference':'Current explicit XOR/XNOR source rule,or all16binary tables consistent with final decisions after rule withdrawal.Unknown missing features/out-of-scope/status remain U.Hand64cell reference checked separately.',
  'invalid':'Invalid initial product skips its review and8readers;invalid review skips only4reviewed-card/tail readers.Denominators remain64/view.Binding-invalid includes out-of-source enum ID.No repair/replacement.',
  'fatal':'Control,transport,shared structural wire/schema/decode,unknownusage,model,input/runtime/ownedguard failure closes remainder.Unusedexpire.No retry,resume,repair or replenishment.',
  'pipeline_comparison_not_enum_only_ablation':True,'extra_review_cost_reported':True,'token_matched':False,'external_reader_decoder':False,
  'posthoc_historical_parent_selection':False,'old_scopes_reopened':False,'old_scores_replaced':False,'production_default_changed':False,
  'aggregate_token_cap':None,'money_cap':None,'local_child_timeout_seconds':180,'approved':False,'new_service_authority':False,
  'execution_condition':'Fresh direct human45scope grant and all three CI checks successful at exact published implementation head.'}
 return {'proposal.json':proposal,'sources.json':data['sources'],'queries.public.json':data['queries'],'reference.private.json':data['rows'],
  'author-evidence.private.json':data['author_evidence'],'design.json':data['design'],'slots.json':slots(),
  'static-requests.json':{str(s['slot']):request(s)for s in slots()if s['kind']in('none','full','extract')},
  'dynamic-rules.json':{'slots':[s for s in slots()if s['kind']in('review','read')],'builder':'benchmarks/fresh-enum-pipeline-v1/plan.py:request','own_valid_fresh_parent_only':True},
  'implementation-sha256.json':implementation()}
def values():return copy.deepcopy(_values(digest(implementation())))
def prepare(root):
 root=Path(root);root.mkdir(exist_ok=False);data=values()
 for n,v in data.items():(root/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 (root/'manifest.json').write_text(json.dumps({'files':{n:sha(root/n)for n in sorted(data)},'new_model_calls':0},indent=2)+'\n')
def verify(root):
 for n,h in read(root/'manifest.json')['files'].items():
  p=Path(n)
  if p.is_absolute()or'..'in p.parts or(root/p).is_symlink()or sha(root/p)!=h:raise ValueError('Frozen input drift')
 if any(read(root/n)!=v for n,v in values().items()):raise ValueError('Reconstruction differs')
 return True
