"""Reproduce the scope-first protocol comparison offline, without a model call."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from runaway.choice_reader import make_request,decode_response
spec=importlib.util.spec_from_file_location('coverage_public_world',HERE/'coverage_world.py');cw=importlib.util.module_from_spec(spec);spec.loader.exec_module(cw)
w=cw.w


def require(condition,message):
    if not condition:raise ValueError(message)


def digest(value):return hashlib.sha256(w.canonical(value).encode()).hexdigest()


def validate(value):
    worlds=cw.worlds();queries,mapping=w.queries(worlds['combined'])
    require(value['synthetic'] is True and value['queries']==queries,'Question set differs')
    expected={prefix+'_'+arm for prefix in ['luna_standard','luna_coverage','sol_coverage'] for arm in ['full','none','card']}|{'luna_coverage_full_repeat','luna_coverage_card_repeat'}
    require(set(value['groups'])==expected,'Missing or extra main group')
    records=value['executions'];prior=value['closed_diagnostic']
    require(value['main_status']=='complete' and len(records)==51,'Main comparison incomplete')
    require(prior['status']=='stopped' and prior['attempts']==11 and prior['completed']==10 and prior['failed']==1 and prior['missing_usage']==1,'Closed diagnostic accounting differs')
    require(len(prior['executions'])==11,'Diagnostic record count differs')
    require(sum(x['outcome']=='completed' for x in prior['executions'])==10 and sum(x['outcome']=='failed' for x in prior['executions'])==1,'Diagnostic outcomes differ')
    diagnostic_scores={(row['group'],row['key']):row for row in prior['scored_responses']}
    require(len(diagnostic_scores)==10 and sum(len(rows) for rows in prior['raw_answers'].values())==10,'Diagnostic raw response count differs')
    for record in prior['executions']:
        group=record['group'];key=record['diagnostic'];meta=prior['index'][key]
        require(group in ('single_full','single_card'),'Unexpected diagnostic group')
        arm=group.removeprefix('single_');pid=meta['person'];query=meta['query']
        request={'system':value['system'],'model':'gpt-6-luna',**make_request(value['materials'][arm][pid],[query],as_of=value['as_of'],answer_format='text',reader_mode='standard')}
        require(digest(request)==record['request_id'],'Diagnostic request fingerprint differs')
        if record['outcome']=='completed':
            answer=prior['raw_answers'][group][key];label=decode_response([query],answer,answer_format='text')[query['id']]
            case=next(case for case in worlds['development']['cases'] if case['scene']==meta['scene'])
            observed=case['orders'][0]['semantics'].get(label,label);gold=case['gold'][pid];scored=diagnostic_scores[(group,key)]
            require((scored['gold'],scored['observed'],scored['correct'])==(gold,observed,observed==gold),'Diagnostic score differs')
        else:require(key not in prior['raw_answers'].get(group,{}),'Failed diagnostic has an invented answer')
    all_records=records+prior['executions']
    require(len({x['execution_id'] for x in all_records})==62,'Duplicate actual execution ID')
    forbidden={x['request_id'] for x in prior['executions']}
    require(not forbidden&{x['request_id'] for x in records},'Previously attempted diagnostic request reused')
    require(len({x['request_id'] for x in records})==39,'Main unique request count differs')
    scores={};quality={}
    for name,row in value['groups'].items():
        arm=row['arm'];mode=row['reader_mode'];model=row['model_requested']
        expected_mode='standard' if name.startswith('luna_standard') else 'coverage'
        expected_model='gpt-6-sol' if name.startswith('sol_') else 'gpt-6-luna'
        expected_arm=next((candidate for candidate in ['full','none','card'] if name.endswith('_'+candidate) or name.endswith('_'+candidate+'_repeat')),None)
        require((arm,mode,model)==(expected_arm,expected_mode,expected_model),'Reader group metadata differs:'+name)
        people={'shared'} if arm=='none' else set(w.PEOPLE)
        require(set(row['answers'])==set(row['requests_sha256'])==set(row['answers_sha256'])==people,'Main people differ:'+name)
        group_records=[record for record in records if record['group']==name]
        require(len(group_records)==len(people) and {record['person'] for record in group_records}==people,'Execution group differs:'+name)
        for person in people:
            request={'system':value['system'],'model':model,**make_request(value['materials'][arm][person],queries,as_of=value['as_of'],answer_format='text',reader_mode=mode)}
            require(digest(request)==row['requests_sha256'][person],'Wire request fingerprint differs:'+name+':'+person)
            require(digest(row['answers'][person])==row['answers_sha256'][person],'Raw answer fingerprint differs:'+name+':'+person)
        require(all(record['outcome']=='completed' and record['request_id']==row['requests_sha256'][record['person']] for record in group_records),'Execution binding differs:'+name)
        decoded={pid:decode_response(queries,raw,answer_format='text') for pid,raw in row['answers'].items()}
        decoded={pid:decoded['shared'] for pid in w.PEOPLE} if arm=='none' else decoded
        answers={pid:{mapping[key]:label for key,label in labels.items()} for pid,labels in decoded.items()}
        scores[name]={suite:w.evaluate(world,answers) for suite,world in worlds.items()}
        for suite,score in scores[name].items():require(all(score[key]==expected for key,expected in row['summary'][suite].items()),'Observed result differs:'+name+':'+suite)
    for prefix in ['luna_standard','luna_coverage','sol_coverage']:
        quality[prefix]={}
        for suite in worlds:
            full,none,card=[scores[prefix+'_'+arm][suite] for arm in ['full','none','card']]
            gain=(full['known']['correct']-none['known']['correct'])/full['known']['planned']
            qualified=full['strict_pass'] and gain>=.25
            quality[prefix][suite]={'full_qualified':qualified,'card_strict_pass':card['strict_pass'],'known_full_minus_none':gain,'retention_interpretable':qualified}
    require(quality==value['quality'],'Reader qualification differs')
    stable=all(row['full_qualified'] and row['card_strict_pass'] for row in quality['luna_coverage'].values()) and all(scores['luna_coverage_'+arm+'_repeat'][suite]['strict_pass'] for arm in ['full','card'] for suite in worlds)
    require(stable==value['stable_coverage_strict_pass'],'Stable quality gate differs')
    for arm in ['full','card']:require(value['groups']['luna_coverage_'+arm]['requests_sha256']==value['groups']['luna_coverage_'+arm+'_repeat']['requests_sha256'],'Repeat input differs')
    return {'passed':True,'groups_reproduced':len(scores),'main_calls':51,'closed_diagnostic_attempts':11,'whole_turn_attempts':62,'missing_usage_records':1,'stable_coverage_strict_pass':stable,'model_calls':0}


def read(path):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data',type=Path,default=HERE/'coverage-observed.synthetic.json');args=parser.parse_args()
    try:print(json.dumps(validate(read(args.data)),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc:parser.exit(2,str(exc)+'\n')
