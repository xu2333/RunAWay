"""Frozen posthoc nine-read diagnostic inputs; no service backend or authority."""
import importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
base=load('fixed_coverage_source',ROOT/'benchmarks/object-coverage-comparison-v1/plan.py')
read,sha,digest=base.read,base.sha,base.digest
CAP,MODEL,AS_OF=9,base.MODEL,base.AS_OF
PROFILES=base.PROFILES
ARCHIVE=ROOT/'benchmarks/object-coverage-comparison-v1/measured.synthetic.json'
ARCHIVE_SHA=sha(ARCHIVE)
VIEWS=('a8r:baseline','a8r:guidance','c2v:guidance')
def inputs():
 if sha(ARCHIVE)!=ARCHIVE.with_suffix('.sha256').read_text().strip():raise ValueError('Origin archive drift')
 data=read(ARCHIVE);cards=[r for r in data['records']if 'card'in r]
 if [(r['slot'],r['profile'],r['method'])for r in cards]!=[(4,'a8r',base.METHODS[0]),(5,'a8r',base.METHODS[1]),(6,'c2v',base.METHODS[1])]:raise ValueError('Foreign card origins')
 return {**base.inputs(),'materials':{view:r['card']['prompt']for view,r in zip(VIEWS,cards)},
  'origin_sha256':sha(ARCHIVE),'origin_records':[{'slot':r['slot'],'request_sha256':r['request_sha256'],'artifact_sha256':r['artifact_sha256']}for r in cards]}
def slots():
 jobs=[('none','shared_all',None,None),('full','a8r',None,None),('full','c2v',None,None)]
 jobs += [('read',v.split(':')[0],v,r)for r,order in((0,VIEWS),(1,tuple(reversed(VIEWS))))for v in order]
 return [{'slot':i+1,'kind':k,'profile':pid,'view':v,'read_repeat':r}for i,(k,pid,v,r)in enumerate(jobs)]
def request(slot):
 if slot not in slots():raise ValueError('Outside nine frozen slots')
 if slot['kind']!='read':return base.request(next(s for s in base.slots()if s['kind']==slot['kind']and s['profile']==slot['profile']))
 old=base.base
 req=old.choice_reader.make_request(inputs()['materials'][slot['view']],inputs()['queries']['all'],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'model':MODEL,'system':old.base.old.old.grouped_support.SYSTEM,**req,'prompt':old.base.old.old.COMMON+req['prompt']}
def implementation():
 files={**base.implementation(),'scripts/capture_codex_failure.py':sha(ROOT/'scripts/capture_codex_failure.py'),
  'benchmarks/object-coverage-comparison-v1/measured.synthetic.json':sha(ARCHIVE)}
 files.update({'benchmarks/coverage-fixed-views-v1/'+p.name:sha(p)for p in HERE.glob('*.py')})
 return dict(sorted(files.items()))
def values():
 data=inputs()
 return {'proposal.json':{'kind':'unapproved_coverage_fixed_views_readonly9','model':MODEL,'as_of':AS_OF,
  'max_new_local_cli_attempts':9,'source_messages':44,'unique_public_forms':30,'fixed_public_card_characters':[353,324,506],
  'stages':{'shared_none':1,'own_full':2,'fixed_card_reads':6},'primary_cases_per_fixed_view':15,'answers_per_case':4,
  'paired_method_comparison':'a8r only;one existing card/method;not generation stability or causal evidence',
  'guided_coverage_endpoint':'a8r+c2v,30fixed cases:18known12unknown;do not compare with15baseline cases',
  'fatal':'Any control,transport,wire,schema,decode,unknownusage,model,runtime,guard or input failure stops all remainder.No retry/repair/resume/replenishment.',
  'capture':'Separate serial-only safe completion observer around unchanged pinned once helper;preserve existing timeout provenance;no raw streams or thread IDs in new completion metadata.',
  'new_extractions':0,'tail_reads':0,'whole_card_cap':1536,'independent_holdout':False,'production_default_changed':False,
  'old43_scope_reopened':False,'old43_scores_replaced':False,'approved':False,'new_service_authority':False,
  'aggregate_token_cap':None,'money_cap':None,'local_child_timeout_seconds':180,
  'execution_condition':'Fresh direct human grant and all three PR52 CI checks at3b05ddc397ebae8f85709da8611ca990647c6160 succeed.'},
  'sources.json':data['sources'],'queries.public.json':data['queries'],'reference.private.json':data['rows'],
  'materials.public.json':data['materials'],'origin.public.json':{'sha256':data['origin_sha256'],'records':data['origin_records']},
  'slots.json':slots(),'static-requests.json':{str(s['slot']):request(s)for s in slots()},'implementation-sha256.json':implementation()}
def prepare(destination):
 destination.mkdir(exist_ok=False);files={}
 for name,value in values().items():
  (destination/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');files[name]=sha(destination/name)
 (destination/'manifest.json').write_text(json.dumps({'files':dict(sorted(files.items())),'new_model_calls':0},indent=2)+'\n')
def verify(root):
 for name,expected in read(root/'manifest.json')['files'].items():
  rel=Path(name)
  if rel.is_absolute()or'..'in rel.parts or(root/rel).is_symlink()or sha(root/rel)!=expected:raise ValueError('Input drift')
 if any(read(root/name)!=value for name,value in values().items()):raise ValueError('Reconstruction drift')
 return True
