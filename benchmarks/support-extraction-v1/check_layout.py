"""Offline audit of the fixed source-fact-preserving layout comparison."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parents[1]))
from runaway import support_extract
from runaway.choice_reader import make_request,decode_response
spec=importlib.util.spec_from_file_location('layout_coverage_world',HERE/'coverage_world.py');cw=importlib.util.module_from_spec(spec);spec.loader.exec_module(cw);w=cw.w


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):return hashlib.sha256(w.canonical(value).encode()).hexdigest()


def read(path):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs)


def plan_for():
    plan=[]
    for model in ['luna','sol']:
        plan += [[model+'_full',pid] for pid in w.PEOPLE]+[[model+'_none','shared']]
        for i,pid in enumerate(w.PEOPLE):plan += [[model+'_'+arm,pid] for arm in (['paragraph','rows'] if i%2==0 else ['rows','paragraph'])]
        if model=='luna':
            for i,pid in enumerate(w.PEOPLE):plan += [['luna_'+arm+'_repeat',pid] for arm in (['rows','paragraph'] if i%2==0 else ['paragraph','rows'])]
    return plan


def validate(value):
    worlds=cw.worlds();queries,mapping=w.queries(worlds['combined']);sources=w.source_data();extractions=read(HERE/'extractor-answers.synthetic.json')
    require(value['synthetic'] is True and value['queries']==queries,'Questions differ')
    expected={model+'_'+arm for model in ['luna','sol'] for arm in ['full','none','paragraph','rows']}|{'luna_paragraph_repeat','luna_rows_repeat'}
    require(set(value['groups'])==expected and value['status']=='complete','Group matrix incomplete')
    plan=plan_for();require(value['completed_plan']==plan,'Counterbalanced order differs')
    records=value['executions'];require(len(records)==50 and len({row['execution_id'] for row in records})==50 and len({row['request_id'] for row in records})==38,'Actual execution counts differ')
    require({(row['group'],row['person']) for row in records}=={tuple(slot) for slot in plan},'Execution slots differ')
    require(set(value['materials'])=={'full','none','paragraph','rows'} and value['materials']['none']=={'shared':''},'Material arms differ')
    for pid in w.PEOPLE:
        require(value['materials']['full'][pid]==w.canonical(sources[pid]),'Full history differs')
        for layout in ['paragraph','rows']:
            text=support_extract.bind(extractions[pid],sources[pid],768,layout=layout)['prompt.md']
            require(text==value['materials'][layout][pid] and len(text)<=768,'Source-bound render differs:'+layout+':'+pid)
    scores={};quality={}
    summary_keys={'known','unknown','order_consistent','missing_variants','by_kind','by_axis','by_person','strict_pass'}
    for name,row in value['groups'].items():
        model='gpt-6-luna' if name.startswith('luna_') else 'gpt-6-sol';arm=name.split('_')[1]
        require((row['arm'],row['model_requested'])==(arm,model),'Group metadata differs')
        people={'shared'} if arm=='none' else set(w.PEOPLE)
        require(set(row['answers'])==set(row['requests_sha256'])==set(row['answers_sha256'])==people,'People differ')
        for pid in people:
            request={'system':value['system'],'model':model,**make_request(value['materials'][arm][pid],queries,as_of=value['as_of'],answer_format='text',reader_mode='standard')}
            require(digest(request)==row['requests_sha256'][pid],'Request binding differs:'+name+':'+pid)
            require(digest(row['answers'][pid])==row['answers_sha256'][pid],'Answer binding differs:'+name+':'+pid)
        group_records=[record for record in records if record['group']==name]
        require(len(group_records)==len(people) and all(record['outcome']=='completed' and record['request_id']==row['requests_sha256'][record['person']] and record['answer_sha256']==row['answers_sha256'][record['person']] for record in group_records),'Actual group execution differs')
        decoded={pid:decode_response(queries,answer,answer_format='text') for pid,answer in row['answers'].items()};decoded={pid:decoded['shared'] for pid in w.PEOPLE} if arm=='none' else decoded
        answers={pid:{mapping[key]:label for key,label in rows.items()} for pid,rows in decoded.items()};scores[name]={suite:w.evaluate(world,answers) for suite,world in worlds.items()}
        require(set(row['summary'])==set(worlds),'Case suites differ')
        for suite,score in scores[name].items():require(set(row['summary'][suite])==summary_keys and all(score[key]==expected for key,expected in row['summary'][suite].items()),'Observed score differs:'+name+':'+suite)
    for model in ['luna','sol']:
        quality[model]={}
        for suite in worlds:
            full,none,paragraph,rows=[scores[model+'_'+arm][suite] for arm in ['full','none','paragraph','rows']];gain=(full['known']['correct']-none['known']['correct'])/full['known']['planned'];qualified=full['strict_pass'] and gain>=.25
            quality[model][suite]={'full_qualified':qualified,'known_full_minus_none':gain,'paragraph_strict_pass':paragraph['strict_pass'],'rows_strict_pass':rows['strict_pass'],'retention_interpretable':qualified}
    require(quality==value['quality'],'Qualification differs')
    stable=all(scores[name][suite]['strict_pass'] for name in ['luna_rows','luna_rows_repeat','sol_rows'] for suite in worlds)
    require(stable==value['stable_rows_strict_pass'],'Stable layout gate differs')
    for arm in ['paragraph','rows']:require(value['groups']['luna_'+arm]['requests_sha256']==value['groups']['luna_'+arm+'_repeat']['requests_sha256'],'Repeat inputs differ')
    return {'passed':True,'groups_reproduced':10,'actual_calls':50,'unique_request_fingerprints':38,'stable_rows_strict_pass':stable,'default_layout_changed':False,'model_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'layout-observed.synthetic.json');args=parser.parse_args()
    try:print(json.dumps(validate(read(args.data)),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc:parser.exit(2,str(exc)+'\n')
