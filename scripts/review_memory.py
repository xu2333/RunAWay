"""Explicit source-ID review preparation/import; no model backend or automatic retry."""
import argparse,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
m=load('review_memory_original_bridge',ROOT/'scripts/memory.py')
p=load('review_memory_frozen_reference_plan',ROOT/'benchmarks/source-id-review-v1/plan.py')
r=p.reviewer

def implementation():
 return {**p.implementation(),'scripts/memory.py':p.sha(ROOT/'scripts/memory.py'),
  'scripts/review_memory.py':p.sha(Path(__file__))}

def request(sources,draft,budget):
 if any(len(s['text'])>2000 for s in sources['sources']):
  raise ValueError('Whole-message review requires every selected message to fit2000characters')
 return {'system':m.baseline.b.grouped.SYSTEM,**r.make_request(sources,draft,budget)}

def manifest(sources,draft,req,budget):
 return {'kind':'source_id_review_prepared_v1','budget_characters':budget,
  'source_sha256':m.digest(sources),'draft_sha256':m.digest(draft),'request_sha256':m.digest(req),
  'manual_request_sha256':hashlib.sha256(m.manual_request(req).encode()).hexdigest(),
  'implementation_sha256':implementation(),'model_calls':0,'semantic_support_verified':False}

def prepare(original_prepared,draft,destination):
 sources,original=m.prepared(original_prepared);budget=original['budget_characters']
 req=request(sources,draft,budget)
 files={'sources.private.json':sources,'draft.private.json':draft,'request.private.json':req,
  'request.private.md':m.manual_request(req),'manifest.private.json':manifest(sources,draft,req,budget)}
 for value in files.values():
  encoded=value.encode()if type(value)is str else(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
  if len(encoded)>256000:raise ValueError('Review packet exceeds the local import byte limit')
 directory=m.save_private_bundle(destination,files)
 return {'status':'review_request_prepared','directory':directory,'model_calls':0,
  'contains_private_source_and_old_graph':True,'request_file':'request.private.json','manual_request_file':'request.private.md'}

def prepared(directory):
 directory=Path(directory)
 if directory.is_symlink():raise ValueError('Symlink review refused')
 for name in('sources.private.json','draft.private.json','request.private.json','request.private.md','manifest.private.json'):
  if(directory/name).is_symlink():raise ValueError('Symlink review file refused')
 sources=m.read_json(directory/'sources.private.json');draft=m.read_json(directory/'draft.private.json')
 req=m.read_json(directory/'request.private.json');value=m.read_json(directory/'manifest.private.json')
 expected=request(sources,draft,value['budget_characters'])
 if m.digest(req)!=m.digest(expected) or m.digest(value)!=m.digest(manifest(sources,draft,expected,value['budget_characters'])):
  raise ValueError('Review source,draft,request or implementation differs')
 if(directory/'request.private.md').read_bytes()!=m.manual_request(expected).encode():raise ValueError('Manual review request differs')
 return sources,value

def import_answer(directory,answer,destination):
 sources,metadata=prepared(directory)
 files=r.bind(answer,sources,metadata['budget_characters'])
 summary={'status':'candidate_unvalidated','method':'source-id-review-v1','model_calls':0,
  'characters':len(files['prompt.md']),'budget_characters':metadata['budget_characters'],
  'source_sha256':metadata['source_sha256'],'parent_graph_sha256':metadata['draft_sha256'],
  'request_sha256':metadata['request_sha256'],'semantic_support_verified':False,
  'source_coverage_verified':False,'behavioral_fidelity_verified':False,
  'shareable_files':['prompt.md','portable.json'],
  'private_files':[n for n in files if n not in('prompt.md','portable.json')]+['review-import.private.json']}
 files['review-import.private.json']=summary
 directory=m.save_private_bundle(destination,files)
 return {**summary,'directory':directory}

def demo(destination):
 replay=load('review_memory_actual_replay',ROOT/'scripts/replay_source_id_review.py')
 replay.check();data=p.read(replay.DEFAULT);record=next(v for v in data['records']if v['kind']=='review')
 with tempfile.TemporaryDirectory()as tmp:
  base=Path(tmp);m.prepare(data['sources']['f7s'],'coverage',1536,base/'original')
  prepare(base/'original',data['draft'],base/'review')
  expected=dict(record['request']);expected.pop('model')
  if m.read_json(base/'review/request.private.json')!=expected:raise ValueError('Archived exact request differs')
  result=import_answer(base/'review',m.parse_answer(record['raw']),destination)
 return {**result,'archived_fictional_fixture_replay':True,'fresh_generation':False}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);actions=parser.add_subparsers(dest='command',required=True)
 command=actions.add_parser('prepare');command.add_argument('--original-prepared',type=Path,required=True);command.add_argument('--draft-answer',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
 command=actions.add_parser('import');command.add_argument('--prepared',type=Path,required=True);command.add_argument('--answer',type=Path,required=True);command.add_argument('--out',type=Path,required=True)
 command=actions.add_parser('demo');command.add_argument('--out',type=Path,required=True)
 args=parser.parse_args(argv)
 try:
  if args.command=='prepare':result=prepare(args.original_prepared,m.read_json(args.draft_answer),args.out)
  elif args.command=='import':result=import_answer(args.prepared,m.read_json(args.answer),args.out)
  else:result=demo(args.out)
 except(ValueError,TypeError,KeyError,OSError,StopIteration)as exc:
  print(json.dumps({'error':type(exc).__name__,'message':'Invalid local review input or binding; inspect the selected files. No model call was made.','model_calls':0}),file=sys.stderr);return 2
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
