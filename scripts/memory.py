"""Explicit experimental taste-memory bridge: prepare/import/demo, no model backend."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runaway.cli import save_private_bundle
from runaway.constraint_extract import parse_answer
from runaway.profile import validate_sources

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
baseline=load('memory_bridge_baseline',ROOT/'benchmarks/source-order-v3/candidate.py')
coverage=load('memory_bridge_coverage',ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')
provenance=load('memory_bridge_core',ROOT/'benchmarks/epistemic-transfer-v1/plan.py')
METHODS={'baseline':baseline,'coverage':coverage}

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read_json(path,limit=256000):
 data=Path(path).read_bytes()
 if len(data)>limit:raise ValueError('Input exceeds byte limit')
 return parse_answer(data.decode('utf8'))
def implementation():
 return {**provenance.implementation(),'benchmarks/object-coverage-guidance-v1/candidate.py':provenance.sha(ROOT/'benchmarks/object-coverage-guidance-v1/candidate.py')}
def request(sources,method,budget):
 if method not in METHODS:raise ValueError('Explicit supported method required')
 return {'system':baseline.b.grouped.SYSTEM,**METHODS[method].make_request(sources,budget)}
def source_file(path):
 path=Path(path)
 if path.suffix.lower()=='.json':return validate_sources(read_json(path,64000))
 text=path.read_bytes()
 if len(text)>64000:raise ValueError('Source exceeds64KB')
 return validate_sources({'schema_version':1,'sources':[{'id':'narrative','episode_id':'provided_narrative','role':'user','text':text.decode('utf8')}]})

def manual_request(req):
 return req['system']+'\n\n'+req['prompt']+'\n\nOUTPUT_SCHEMA_JSON:\n'+json.dumps(req['schema'],ensure_ascii=False,indent=2)+'\n'

def prepare(sources,method,budget,destination):
 req=request(sources,method,budget)
 markdown=manual_request(req)
 manifest={'schema_version':1,'method':method,'budget_characters':budget,'source_sha256':digest(sources),
  'request_sha256':digest(req),'manual_request_sha256':hashlib.sha256(markdown.encode()).hexdigest(),'implementation_sha256':implementation(),'experimental':True,'model_calls':0}
 # JSON is the exact measured structured-output request (without provider/model).
 # Markdown carries the same data/schema for manual interfaces; that repackaging
 # has not itself been validated across harnesses or providers.
 directory=save_private_bundle(destination,{'sources.private.json':sources,'request.private.json':req,
  'request.private.md':markdown,'manifest.private.json':manifest})
 return {'status':'request_prepared','directory':directory,'method':method,'model_calls':0,
  'request_file':'request.private.json','manual_request_file':'request.private.md','contains_private_source':True}

def prepared(directory):
 directory=Path(directory)
 if directory.is_symlink():raise ValueError('Prepared directory is a symlink')
 for name in('sources.private.json','request.private.json','request.private.md','manifest.private.json'):
  if(directory/name).is_symlink():raise ValueError('Prepared input is a symlink')
 sources=read_json(directory/'sources.private.json');req=read_json(directory/'request.private.json');m=read_json(directory/'manifest.private.json')
 if set(m)!={'schema_version','method','budget_characters','source_sha256','request_sha256','manual_request_sha256','implementation_sha256','experimental','model_calls'}:
  raise ValueError('Prepared manifest differs')
 if type(m['schema_version'])is not int or m['schema_version']!=1 or m['experimental']is not True or type(m['model_calls'])is not int or m['model_calls']!=0:
  raise ValueError('Unsupported prepared request')
 if m['implementation_sha256']!=implementation()or digest(sources)!=m['source_sha256']or digest(req)!=m['request_sha256']:
  raise ValueError('Prepared input or implementation changed')
 if req!=request(sources,m['method'],m['budget_characters']):raise ValueError('Request reconstruction differs')
 text=(directory/'request.private.md').read_bytes()
 if len(text)>256000 or text.decode('utf8')!=manual_request(req)or hashlib.sha256(text).hexdigest()!=m['manual_request_sha256']:raise ValueError('Manual request differs')
 return sources,m

def import_answer(directory,answer,destination):
 sources,m=prepared(directory)
 files=METHODS[m['method']].bind(answer,sources,m['budget_characters'])
 # Keep original syntax/projection checks. They do not prove that the model
 # captured every source-supported decision or removed every sensitive fact.
 summary={'status':'candidate_unvalidated','method':m['method'],'model_calls':0,'characters':len(files['prompt.md']),
  'budget_characters':m['budget_characters'],'source_sha256':m['source_sha256'],'request_sha256':m['request_sha256'],
  'experimental':True,'behavioral_fidelity_verified':False,'semantic_support_verified':False,
  'shareable_files':['prompt.md','portable.json'],'private_files':[name for name in files if name not in('prompt.md','portable.json')]+['import.private.json']}
 files['import.private.json']=summary
 out=save_private_bundle(destination,files)
 return {**summary,'directory':out}

def demo(destination):
 path=ROOT/'benchmarks/ambiguous-source-repeat-v1/measured.synthetic.json'
 if provenance.sha(path)!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Published demo archive changed')
 data=read_json(path,2000000)
 record=next(r for r in data['records']if r['slot']==7)
 if record['profile']!='c2v'or record['method']!='object-coverage-guidance-v1'or 'card'not in record:raise ValueError('Demo origin differs')
 sources=data['sources']['c2v'];answer=parse_answer(record['raw'])
 files=coverage.bind(answer,sources,1536)
 if files['prompt.md']!=record['card']['prompt']:raise ValueError('Demo projection differs')
 destination=Path(destination);destination.mkdir(parents=True,mode=0o700,exist_ok=False)
 prepare(sources,'coverage',1536,destination/'request')
 with(destination/'answer.private.json').open('x')as f:json.dump(answer,f,ensure_ascii=False,indent=2)
 (destination/'answer.private.json').chmod(0o600)
 result=import_answer(destination/'request',answer,destination/'candidate')
 return {**result,'synthetic_archive_replay':True,'new_inference':False,'origin_slot':7}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);actions=parser.add_subparsers(dest='command',required=True)
 p=actions.add_parser('prepare');p.add_argument('--input',type=Path,required=True);p.add_argument('--method',choices=tuple(METHODS),required=True);p.add_argument('--budget-chars',type=int,default=1536);p.add_argument('--out',type=Path,required=True)
 p=actions.add_parser('import');p.add_argument('--prepared',type=Path,required=True);p.add_argument('--answer',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p=actions.add_parser('demo');p.add_argument('--out',type=Path,required=True)
 args=parser.parse_args(argv)
 try:
  if args.command=='prepare':result=prepare(source_file(args.input),args.method,args.budget_chars,args.out)
  elif args.command=='import':result=import_answer(args.prepared,read_json(args.answer),args.out)
  else:result=demo(args.out)
 except(ValueError,TypeError,KeyError,OSError,StopIteration)as exc:
  print(json.dumps({'error':type(exc).__name__,'message':'Invalid local input or binding; inspect local files. No model call was made.','model_calls':0}),file=sys.stderr)
  return 2
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
