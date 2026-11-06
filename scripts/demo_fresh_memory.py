"""Replay one measured fictional fresh45card through the offline user bridge."""
import argparse,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
r=load('fresh_demo_replay',ROOT/'scripts/replay_fresh_enum_pipeline.py')
v=load('fresh_demo_review_bridge',ROOT/'scripts/review_memory.py');m=v.m

def demo(person,stage,destination):
 if person not in r.p.PROFILES or stage not in('draft','reviewed'):raise ValueError('Unknown fictional example')
 r.check();data=r.p.read(r.DEFAULT)
 draft_record=next(x for x in data['records']if x['kind']=='extract'and x['profile']==person)
 draft=m.parse_answer(draft_record['raw']);files={'draft-answer.private.json':draft}
 selected=draft_record
 if stage=='reviewed':
  selected=next(x for x in data['records']if x['kind']=='review'and x['profile']==person)
  files['review-answer.private.json']=m.parse_answer(selected['raw'])
 destination=Path(m.save_private_bundle(destination,files))
 m.prepare(data['sources'][person],'coverage',1536,destination/'request')
 expected=dict(draft_record['request']);expected.pop('model')
 if m.read_json(destination/'request/request.private.json')!=expected:raise ValueError('Initial exact request differs')
 if stage=='draft':result=m.import_answer(destination/'request',draft,destination/'candidate')
 else:
  v.prepare(destination/'request',draft,destination/'review-request','enumerated')
  expected=dict(selected['request']);expected.pop('model')
  if m.read_json(destination/'review-request/request.private.json')!=expected:raise ValueError('Review exact request differs')
  result=v.import_answer(destination/'review-request',m.parse_answer(selected['raw']),destination/'candidate')
 if(destination/'candidate/prompt.md').read_text()!=selected['card']['prompt']:raise ValueError('Public example bytes differ')
 return {**result,'fictional_example':person,'stage':stage,'synthetic_archive_replay':True,'fresh_generation':False,'scores_inherited_by_new_imports':False}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--person',choices=r.p.PROFILES,default='pavo')
 parser.add_argument('--stage',choices=('draft','reviewed'),default='draft');parser.add_argument('--out',type=Path,required=True)
 args=parser.parse_args(argv)
 try:result=demo(args.person,args.stage,args.out)
 except(ValueError,TypeError,KeyError,OSError,StopIteration)as exc:
  print(json.dumps({'error':type(exc).__name__,'message':'Invalid or existing local demo output;no model call was made.','model_calls':0}),file=sys.stderr);return 2
 print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
