"""Unapproved seven-call fixed-draft review; all static data fictional."""
import importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
sys.path.insert(0,str(ROOT))
from runaway.constraint_extract import parse_answer
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
base=load('fixed_review_source',ROOT/'benchmarks/epistemic-transfer-v1/plan.py')
reviewer=load('fixed_review_encoder',HERE/'reviewer.py')
read,sha,digest=base.read,base.sha,base.digest
MODEL,AS_OF,CAP,BUDGET=base.MODEL,base.AS_OF,7,1536
PROFILES=('f7s',)
ARCHIVE=ROOT/'benchmarks/remaining-source-repeat-v1/measured.synthetic.json'
def inputs():
 if sha(ARCHIVE)!=ARCHIVE.with_suffix('.sha256').read_text().strip():raise ValueError('Origin archive drift')
 data=read(ARCHIVE);record=next(r for r in data['records']if r['slot']==49)
 if record['profile']!='f7s'or record['method']!='object-coverage-guidance-v1'or record['generation']!=1 or record['card']['characters']!=240:raise ValueError('Fixed draft differs')
 draft=parse_answer(record['raw'])
 sources=data['sources']['f7s'];public=reviewer.bind(draft,sources,BUDGET)['prompt.md']
 if public!=record['card']['prompt']:raise ValueError('Original public view differs')
 return {'sources':{'f7s':sources},'queries':base.inputs()['queries'],'rows':[r for r in base.inputs()['rows']if r['person']=='f7s'],
  'draft':draft,'original':public,'origin':{'archive_sha256':sha(ARCHIVE),'slot':49,'raw_value_sha256':record['raw_value_sha256'],'artifact_sha256':record['artifact_sha256']}}
def slots():
 return [{'slot':i+1,'kind':k,'profile':'f7s','view':v,'read_repeat':r}for i,(k,v,r)in enumerate((
 ('none',None,None),('full',None,None),('review',None,None),('read','original',0),('read','reviewed',0),('read','reviewed',1),('read','original',1)))]
def request(slot,reviewed=None):
 if slot not in slots():raise ValueError('Outside frozen7slots')
 data=inputs();system=base.base.old.old.grouped_support.SYSTEM
 if slot['kind']=='review':return {'model':MODEL,'system':system,**reviewer.make_request(data['sources']['f7s'],data['draft'],BUDGET)}
 if slot['kind']=='none':text=''
 elif slot['kind']=='full':text=base.transcript(data['sources']['f7s'])
 elif slot['view']=='original':text=data['original']
 elif reviewed is None:return None
 else:text=reviewer.bind(reviewed,data['sources']['f7s'],BUDGET)['prompt.md']
 req=base.choice_reader.make_request(text,data['queries']['all'],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'model':MODEL,'system':system,**req,'prompt':base.base.old.old.COMMON+req['prompt']}
def implementation():
 files={**base.implementation(),'scripts/capture_codex_failure.py':sha(ROOT/'scripts/capture_codex_failure.py'),
  'benchmarks/object-coverage-guidance-v1/candidate.py':sha(ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py'),
  'benchmarks/remaining-source-repeat-v1/measured.synthetic.json':sha(ARCHIVE)}
 files.update({'benchmarks/source-review-diagnostic-v1/'+p.name:sha(p)for p in HERE.glob('*.py')})
 return dict(sorted(files.items()))
def values():
 data=inputs();proposal={'kind':'unapproved_source_review_fixed_draft7','model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':7,
  'stages':{'no_memory':1,'full_control':1,'source_only_review':1,'fixed_original_reads':2,'new_reviewed_reads':2},
  'source_messages':22,'unique_public_forms':30,'fixed_original_characters':240,'whole_public_character_cap':1536,
  'primary_cases_per_view':15,'known':7,'unknown':8,'answers_per_case':4,
  'review_input':'Own source22messages and fixed old draft graph including its literal source anchors.No questions,references,reader outputs/scores,author parameters or manual bindings.',
  'posthoc':'One fixed losing card chosen after observing its failure;new general review guidance targets encoder incompletion.Not fresh generation,stability or independent holdout.',
  'preservation':'Original raw graph/card/reference/old responses unchanged;review creates a separate new candidate,not a patch to sealed records.',
  'control':'None then full15/15bothorders,no missing,and personal-known gain;before review.',
  'invalid_product':'Budget/binding-invalid reviewed product skips only its own2reads,keeps15missing in reviewed endpoint;original2reads still run.',
  'fatal':'Any control,transport,wire/schema/decode,unknownusage,model,input/runtime or ownedguard failure stops remainder.Unusedexpire.No retry,manual repair,resume or replenishment.',
  'schema_wire_binder_reader_unchanged':True,'new_initial_extractions':0,'review_outputs':1,'generation_stability_verified':False,
  'independent_holdout':False,'production_default_changed':False,'old66_scores_replaced':False,'approved':False,'new_service_authority':False,
  'aggregate_token_cap':None,'money_cap':None,'local_child_timeout_seconds':180,
  'execution_condition':'Fresh direct human grant and all three PR56 CI checks at9bf5e51399a48f3b00834e43499d820ba7aacf83 succeed.'}
 return {'proposal.json':proposal,'sources.json':data['sources'],'queries.public.json':data['queries'],'reference.private.json':data['rows'],
  'draft.private.json':data['draft'],'materials.public.json':{'original':data['original']},'origin.public.json':data['origin'],'slots.json':slots(),
  'static-requests.json':{str(s['slot']):request(s)for s in slots()if s['view']!='reviewed'},
  'dynamic-rules.json':{'slots':[s for s in slots()if s['view']=='reviewed'],'builder':'benchmarks/source-review-diagnostic-v1/plan.py:request','own_valid_review_only':True},
  'implementation-sha256.json':implementation()}
def prepare(destination):
 destination.mkdir(exist_ok=False)
 for name,value in values().items():(destination/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 (destination/'manifest.json').write_text(json.dumps({'files':{n:sha(destination/n)for n in sorted(values())},'new_model_calls':0},indent=2)+'\n')
def verify(root):
 for name,expected in read(root/'manifest.json')['files'].items():
  rel=Path(name)
  if rel.is_absolute()or'..'in rel.parts or(root/rel).is_symlink()or sha(root/rel)!=expected:raise ValueError('Input drift')
 if any(read(root/name)!=v for name,v in values().items()):raise ValueError('Reconstruction drift')
 return True
