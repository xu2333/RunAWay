"""Offline reproducible synthetic input preparation and raw-choice scoring."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
from runaway import choice_reader,support_extract
spec=importlib.util.spec_from_file_location('synthetic_world',HERE/'world.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
SYSTEM=json.loads((HERE/'observed.synthetic.json').read_text(encoding='utf-8'))['system']


def read(path):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'),object_pairs_hook=pairs)


def prepare(case_set,arm,answer_format="label"):
    world=w.world(case_set=='fresh');queries,_=w.queries(world);sources=w.source_data();answers=read(HERE/'extractor-answers.synthetic.json')
    materials={'shared':''} if arm=='none' else {pid:w.canonical(value) for pid,value in sources.items()} if arm=='full' else {pid:support_extract.bind(answers[pid],value,768)['prompt.md'] for pid,value in sources.items()}
    return {pid:{'system':SYSTEM,**choice_reader.make_request(text,queries,as_of='2026-04-01',answer_format=answer_format)} for pid,text in materials.items()}


def score(case_set,answers,shared=False,answer_format="label"):
    world=w.world(case_set=='fresh');queries,mapping=w.queries(world)
    if type(answers) is not dict:raise ValueError('Provide person->query->rawletter mappings')
    if shared:
        if set(answers)!={'shared'}:raise ValueError('Expected shared key')
        answers={pid:answers['shared'] for pid in w.PEOPLE}
    if set(answers)-set(w.PEOPLE):raise ValueError('Unexpected person ID')
    decoded={}
    for pid,rows in answers.items():
        labels=choice_reader.decode_response(queries,rows,answer_format=answer_format,allow_missing=True)
        decoded[pid]={mapping[key]:value for key,value in labels.items()}
    return w.evaluate(world,decoded)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','score','check-observed']);parser.add_argument('--case-set',choices=['development','fresh'],default='development');parser.add_argument('--arm',choices=['full','none','card']);parser.add_argument('--answers',type=Path);parser.add_argument('--shared',action='store_true');parser.add_argument('--answer-format',choices=['label','text'],default='label');args=parser.parse_args()
    try:
        if args.action=='prepare':
            if args.arm is None:raise ValueError('Choose --arm')
            result=prepare(args.case_set,args.arm,args.answer_format)
        elif args.action=='score':
            if args.answers is None:raise ValueError('Provide --answers')
            result=score(args.case_set,read(args.answers),args.shared,args.answer_format)
        else:
            observed=read(HERE/'observed.synthetic.json');count=0
            for name,row in observed['groups'].items():
                actual=score(row['case_set'],row['answers'],shared=name.endswith('_none'))
                if any(actual[key]!=value for key,value in row['summary'].items()):raise ValueError('Observed score mismatch:'+name)
                count+=1
            # A universalU must fail known controls, including all positions.
            qs,_=w.queries(w.world());dummy=score('development',{'shared':{q['id']:'U' for q in qs}},True)
            if dummy['known']['correct']!=0 or dummy['strict_pass']:raise ValueError('Abstention control failed')
            old=read(HERE/'old-regression.synthetic.json');known=unknown=consistent=0
            for pid,sources in old['sources'].items():
                if support_extract.bind(old['extractor_answers'][pid],sources,768)['prompt.md']!=old['cards'][pid]:raise ValueError('Old automatic render differs')
                for case in old['world']['cases']:
                    values=[order['semantics'].get(old['raw_answers'][pid][order['public']['id']],old['raw_answers'][pid][order['public']['id']]) for order in case['orders']]
                    correct=all(value==case['gold'][pid] for value in values)
                    if not correct:raise ValueError('Old observed case differs')
                    consistent+=len(set(values))==1
                    if case['gold'][pid]=='U':unknown+=correct
                    else:known+=correct
            if (known,unknown,consistent)!=(56,32,88):raise ValueError('Old denominator mismatch')
            focused=read(HERE/'focused.synthetic.json');focus_runs=0
            for row in focused['focuses'].values():
                case=row['case']
                for arm in ['full','card','donor']:
                    raw=row['answers'][arm];meanings=[order['semantics'].get(raw['q%02d'%(i+1)],raw['q%02d'%(i+1)]) for i,order in enumerate(case['orders'])]
                    source=row['donor'] if arm=='donor' else row['target']
                    expected={'gold_for_target':case['gold'][row['target']],'gold_for_source':case['gold'][source],'observed':meanings,'correct_for_target':all(v==case['gold'][row['target']] for v in meanings),'correct_for_source':all(v==case['gold'][source] for v in meanings),'order_consistent':len(set(meanings))==1}
                    if expected!=row['expected'][arm]:raise ValueError('Focused result mismatch')
                    focus_runs+=1
            readout_count=0
            readout_path=HERE/'readout-formats.synthetic.json'
            if not readout_path.exists():raise ValueError('Missing frozen readout results')
            if readout_path.exists():
                readouts=read(readout_path)
                expected_groups={prefix+'_'+arm for prefix in ['luna_label','luna_text','sol_text'] for arm in ['full','none','card']}|{'luna_text_full_repeat','luna_text_card_repeat'}
                if set(readouts['groups'])!=expected_groups:raise ValueError('Missing or extra readout group')
                executions=readouts['executions']
                if len(executions)!=51 or len({row['execution_id'] for row in executions})!=51 or len({row['request_id'] for row in executions})!=39:raise ValueError('Readout execution counts differ')
                public_queries,_=w.queries(w.world(True))
                if readouts['queries']!=public_queries:raise ValueError('Readout questions differ')
                for name,row in readouts['groups'].items():
                    expected_people={'shared'} if row['arm']=='none' else set(w.PEOPLE)
                    if set(row['answers'])!=expected_people or set(row['requests_sha256'])!=expected_people:raise ValueError('Readout people differ:'+name)
                    records=[record for record in executions if record['group']==name]
                    if len(records)!=len(expected_people) or {record['person'] for record in records}!=expected_people or any(record['outcome']!='completed' or record['request_id']!=row['requests_sha256'][record['person']] for record in records):raise ValueError('Readout execution binding differs:'+name)
                    for pid,expected in row['requests_sha256'].items():
                        request={'system':readouts['system'],'model':row['model_requested'],**choice_reader.make_request(readouts['materials'][row['arm']][pid],public_queries,as_of=readouts['as_of'],answer_format=row['answer_format'])}
                        if hashlib.sha256(w.canonical(request).encode()).hexdigest()!=expected:raise ValueError('Readout request binding mismatch:'+name+':'+pid)
                    actual=score('fresh',row['answers'],shared=row['arm']=='none',answer_format=row['answer_format'])
                    if any(actual[key]!=value for key,value in row['summary'].items()):raise ValueError('Readout score mismatch:'+name)
                    readout_count+=1
            result={'passed':True,'groups_reproduced':count,'old_automatic_card_cases_reproduced':88,'focused_runs_reproduced':focus_runs,'readout_groups_reproduced':readout_count,'model_calls':0,'always_unknown_rejected':True}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError) as exc:parser.exit(2,str(exc)+'\n')

if __name__=='__main__':main()
