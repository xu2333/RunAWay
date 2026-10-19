"""Opt-in offline partial-context calibration using the existing fidelity scorer.

An authored transition table supplies gold, independently of both production
resolvers. This is program sensitivity evidence, never LLM or person fidelity.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from . import fidelity_stress as fs, temporal as t, temporal_concise as codec
from .card import canonical, digest
from .pipeline import write_once
from .synthetic_metric import file_hash

DOMAIN = '产品验证'
P, Q = '方向尚未验证', '改动不可撤销'
ACTIONS = ('先做小实验', '先完成整体设计')
VALUES = (None, False, True)
# Rows: P missing/false/true; columns: Q missing/false/true.
# X=context unknown; R=regular; E=exception; H=hard; C=conflict; N=no evidence.
TABLES = {'regular': 'RRRRRRRRR', 'exception': 'XXXRRREEE',
          'hard': 'XXXRRRXEH', 'conflict': 'XXXCCCXEH', 'cleared': 'NNNNNNNNN'}
PHASE = {1: 'regular', 2: 'regular', 3: 'regular', 4: 'regular',
         5: 'exception', 6: 'hard', 7: 'exception', 8: 'hard',
         9: 'cleared', 10: 'hard', 11: 'conflict', 12: 'hard'}
CONDITIONS = ('timestamped_snapshots', 'current_only', 'wrong_person', 'delete_hard',
              'assume_missing_false', 'weaken_conjunction', 'forget_restore',
              'erase_conflict', 'wrong_cutoff', 'missing_snapshot')
BUNDLE_NOTE = ('完全合成的程序校准输入；非模型预测。snapshots键是精确日期，每份是该日当前策略；'
               '历史只用该日快照，不能拿最终状态倒推。current仅支持第12天，缺少历史须未知。'
               '条件未提供不等于否。全部语法和边界都在所列记忆中。')


def gold(day, x, y, member):
    """Read a fixed nine-cell authored table, not production event code."""
    code = TABLES[PHASE[day]][VALUES.index(x) * 3 + VALUES.index(y)]
    status = {'X': 'context_unknown', 'C': 'conflict', 'N': 'unobserved'}.get(code, 'chosen')
    action = {'R': '1' if day == 3 else '0', 'E': str(1-member), 'H': str(member)}.get(code, 'U')
    return action, status, code == 'H'


def fixture(member):
    exception, hard = ACTIONS[1-member], ACTIONS[member]
    lines = [f'{DOMAIN}：原先选{ACTIONS[0]}，强度3。', f'{DOMAIN}：又观察到{ACTIONS[1]}，强度1。',
             f'{DOMAIN}：明确改为{ACTIONS[1]}，强度2，替代常规。', '撤销e3。',
             f'{DOMAIN}：若{P}，选{exception}。', f'{DOMAIN}：若{P}且{Q}，必须{hard}。',
             '撤销e6。', '撤销e7，恢复原规则。', f'清除{DOMAIN}此前偏好。', '撤销e9。',
             f'{DOMAIN}：又观察到{ACTIONS[1]}，强度3，未解决与原先的冲突。', '撤销e11。']
    sources = {'schema_version': 1, 'sources': [{'id': 'story', 'episode_id': 'authored-partial-context', 'role': 'user', 'text': '\n'.join(lines)+'\n'}]}
    spans = t.spans(sources)
    def event(day, kind, action='', strength=0, when=(), target=''):
        return dict(id='e'+str(day), kind=kind, domain='' if kind=='retract' else DOMAIN,
                    action=action, strength=strength, when_all=[dict(predicate=k,equals=v) for k,v in when],
                    target=target, span_ids=[spans[day-1]['id']])
    events = [event(1,'regular',ACTIONS[0],3), event(2,'regular',ACTIONS[1],1),
              event(3,'replace',ACTIONS[1],2), event(4,'retract',target='e3'),
              event(5,'exception',exception,when=[(P,True)]),
              event(6,'constraint',hard,when=[(P,True),(Q,True)]),
              event(7,'retract',target='e6'), event(8,'retract',target='e7'),
              event(9,'clear'), event(10,'retract',target='e9'),
              event(11,'regular',ACTIONS[1],3), event(12,'retract',target='e11')]
    answer = dict(scope='合成记录中的产品验证局部选择。', events=events, unmodeled=[])
    return t.bind(answer,sources)


def build_world():
    people = []
    for member in (0,1):
        pid='partial-'+str(member); cases=[]
        for day in range(1,13):
            task='current_choice' if day==12 else 'historical_reconstruction'
            for x,y in itertools.product(VALUES,repeat=2):
                context={k:v for k,v in [('c0',x),('c1',y)] if v is not None}
                action,status,active_hard=gold(day,x,y,member)
                for order in (0,1):
                    scenario=f'planning:day{day}:{VALUES.index(x)}{VALUES.index(y)}'
                    tags=['partial_context' if len(context)<2 else 'complete_context','updates','revocations']
                    if PHASE[day] in ('exception','hard','conflict'):tags+=['exceptions','conjunctions']
                    if PHASE[day] in ('hard','conflict'):tags+=['hard_constraints']
                    if status=='conflict':tags+=['conflicts']
                    if status in ('unobserved','context_unknown'):tags+=['unknowns']
                    c=fs.make_case(pid,len(cases),task,scenario,'planning',day,context,tags,'dev',order)
                    words='；'.join(k+'：'+('未提供' if v is None else '是' if v else '否') for k,v in [(P,x),(Q,y)])
                    c['public']['question']=f'只按第{day}天有效记录比较产品验证选择。{words}。未提供的条件不能当作否。'
                    c.update(gold=next(k for k,v in c['options'].items() if v==action),action=action,
                             expected_status=status,active_hard=active_hard)
                    cases.append(c)
        people.append(dict(id=pid,pair_id='authored-pair',twin='partial-'+str(1-member),target_axes=['planning'],
                           member=member,source_cutoff=12,artifact=fixture(member),cases=cases))
    body=dict(origin='fully_synthetic',purpose='authored_temporal_partial_context_calibration',people=people,
              not_real_person_or_model_evidence=True,independent_template_count=1)
    return {**body,'id':digest(canonical(body))}


def snapshots(artifact):
    result={}
    for day in range(1,13):
        source=copy.deepcopy(artifact['sources']);source['sources'][0]['text']=''.join(source['sources'][0]['text'].splitlines(keepends=True)[:day])
        answer=copy.deepcopy(artifact['extraction']);answer['events']=answer['events'][:day]
        result[str(day)]=codec.encode(t.bind(answer,source),budget_chars=10000)['text']
    return result


def memory(snap, condition):
    """Damage only program-controlled memory; never the gold or evaluation cases."""
    data={'note':BUNDLE_NOTE,'snapshots':copy.deepcopy(snap)}
    if condition=='current_only':return codec.J({'note':BUNDLE_NOTE,'current':snap['12']})
    for day,text in list(data['snapshots'].items()):
        policy=codec.decode(text);d=policy['domains'][0]
        if condition=='delete_hard' or (condition=='forget_restore' and int(day) in (8,10,11,12)):d['constraint']=[]
        if condition=='weaken_conjunction':
            for rule in d['constraint']:rule['when']=rule['when'][1:]
        if condition=='erase_conflict' and len(d['regular'])>1:d['regular']=[]
        data['snapshots'][day]=codec.serialize(policy)
    if condition=='wrong_cutoff':data['snapshots']['3']=data['snapshots']['4']
    if condition=='missing_snapshot':del data['snapshots']['6']
    return codec.J(data)


def predict(world, memories, condition):
    answers={};states={}
    for p in world['people']:
        pid=p['id'];data=json.loads(memories[pid]);decoded={day:codec.decode(s) for day,s in data.get('snapshots',{}).items()}
        current=codec.decode(data['current']) if 'current' in data else None
        answers[pid]={};states[pid]={}
        for case in p['cases']:
            key=case['public']['id'];policy=decoded.get(str(case['at']))
            if current is not None and case['at']!=12:
                answers[pid][key]='U';states[pid][key]='unsupported_history';continue
            if current is not None:policy=current
            if policy is None:continue  # Fixed denominator; missing is not U.
            context={P:case['context']['c0']} if 'c0' in case['context'] else {}
            if 'c1' in case['context']:context[Q]=case['context']['c1']
            if condition=='assume_missing_false':context={P:context.get(P,False),Q:context.get(Q,False)}
            result=codec.resolve(policy,DOMAIN,context)
            action=str(ACTIONS.index(result['action'])) if result['status']=='chosen' else 'U'
            answers[pid][key]=next(k for k,v in case['options'].items() if v==action)
            states[pid][key]=result['status']
    return answers,states


def state_score(world, states, task):
    cases=[(p,c) for p in world['people'] for c in p['cases'] if task=='joint' or c['public']['task']==task]
    correct=missing=0;confusion={}
    for p,c in cases:
        value=states.get(p['id'],{}).get(c['public']['id']);expected=c['expected_status']
        correct+=value==expected;missing+=value is None
        row=confusion.setdefault(expected,{});row[value if value is not None else 'missing']=row.get(value if value is not None else 'missing',0)+1
    return dict(correct=correct,planned=len(cases),missing=missing,confusion=confusion)


def calibrate(world=None, count=None, tokenizer=None):
    world=world or build_world();snaps={p['id']:snapshots(p['artifact']) for p in world['people']}
    controls={};payloads={}
    for condition in CONDITIONS:
        delivered={p['id']:memory(snaps[p['twin'] if condition=='wrong_person' else p['id']],condition) for p in world['people']}
        predictions,states=predict(world,delivered,condition);payloads[condition]=delivered
        rows={task:fs.score(world,predictions,task) for task in ('current_choice','historical_reconstruction','joint')}
        slices={name:dict(correct=0,planned=0) for name in ('partial_context','complete_context')};examples=[]
        for p in world['people']:
            for c in p['cases']:
                value=predictions[p['id']].get(c['public']['id']);state=states[p['id']].get(c['public']['id']);right=value==c['gold']
                label='complete_context' if len(c['context'])==2 else 'partial_context';slices[label]['planned']+=1;slices[label]['correct']+=right
                if (not right or state!=c['expected_status']) and len(examples)<2:
                    examples.append(dict(person_id=p['id'],day=c['at'],query=c['public'],context=c['context'],
                        gold_answer=c['gold'],prediction=value,gold_status=c['expected_status'],predicted_status=state,
                        action_correct=right,memory_sha256=digest(delivered[p['id']])))
        lengths={pid:dict(characters=len(text),utf8_bytes=len(text.encode()),actual_tokens=count(text) if count else None) for pid,text in delivered.items()}
        if count and any(type(v['actual_tokens']) is not int or v['actual_tokens']<1 for v in lengths.values()):raise ValueError('Invalid actual token count')
        controls[condition]=dict(scores=rows,state_scores={task:state_score(world,states,task) for task in rows},context_slices=slices,whole_memory_lengths=lengths,counterexamples=examples)
    # Compare the independently authored table with production graph evaluation at every cutoff.
    graph_checks=0
    for p in world['people']:
        for c in p['cases']:
            context={name:c['context'][key] for key,name in [('c0',P),('c1',Q)] if key in c['context']}
            actual=t.resolve(p['artifact'],DOMAIN,context,'e'+str(c['at']))
            action=str(ACTIONS.index(actual['action'])) if actual['status']=='chosen' else 'U'
            if (actual['status'],action)!=(c['expected_status'],c['action']):raise ValueError('Production graph disagrees with authored truth table')
            graph_checks+=1
    full=controls['timestamped_snapshots'];wrong=controls['assume_missing_false'];erased=controls['erase_conflict']
    checks={'correct_timeline_all_actions_and_states':full['scores']['joint']['correct']==432 and full['state_scores']['joint']['correct']==432,
        'missing_as_false_invisible_to_complete_context_only':wrong['context_slices']['complete_context']['correct']==wrong['context_slices']['complete_context']['planned'] and wrong['context_slices']['partial_context']['correct']<wrong['context_slices']['partial_context']['planned'],
        'conflict_erasure_invisible_to_action_only':erased['scores']['joint']['correct']==432 and erased['state_scores']['joint']['correct']<432,
        'swapped_person_loses_target_contrast':controls['wrong_person']['scores']['current_choice']['matched_domain_contrasts']['correct']==0,
        'deleted_hard_produces_actual_violations':controls['delete_hard']['scores']['current_choice']['hard_constraints']['observed_violations']>0,
        'forgotten_restore_and_weakened_AND_detected':all(controls[k]['scores']['joint']['correct']<432 for k in ('forget_restore','weaken_conjunction')),
        'wrong_cutoff_only_hurts_history':controls['wrong_cutoff']['scores']['current_choice']['correct']==36 and controls['wrong_cutoff']['scores']['historical_reconstruction']['correct']<396,
        'missing_snapshot_keeps_denominator':controls['missing_snapshot']['scores']['joint']['planned']==432 and controls['missing_snapshot']['scores']['joint']['missing']==36}
    report=dict(kind='offline_program_partial_context_calibration_not_model_quality',origin='fully_synthetic',world_id=world['id'],
        independent_template_count=1,paired_statistical_units=1,people=2,current_planned=36,historical_planned=396,joint_planned=432,
        graph_truth_table_checks=graph_checks,controls=controls,checks=checks,passed=all(checks.values()),tokenizer=tokenizer or {'kind':'not_measured','actual_tokens_measured':False},
        external_model_calls=0,experimental_service_tokens=0,model_quality_measured=False,real_person_fidelity_verified=False,
        limitations=['One authored single-domain mirrored pair, twelve fixed cutoffs and nine ternary contexts; correlated cases, not new human or population evidence.',
            'Gold is an independently authored transition table. Program reads controlled snapshots, not arbitrary LLM prose; no source extraction quality is measured.',
            'Timestamped baseline intentionally keeps all twelve complete snapshots; all wrapper/grammar text counted. It is not a compact-history solution.',
            'Current-only historical U may coincide with a gold U; status unsupported_history remains distinct from preserved historical state.',
            'These are new opt-in diagnostics, not rescoring or altering sealed D15–D28 results. Native development chat usage is separate, never assumed zero.'])
    report['source_lengths']={}
    for p in world['people']:
        source=p['artifact']['sources']['sources'][0]['text'];archive=codec.J(p['artifact'])
        report['source_lengths'][p['id']]={name:dict(characters=len(text),utf8_bytes=len(text.encode()),actual_tokens=count(text) if count else None)
            for name,text in [('source_text',source),('private_event_archive',archive)]}
    return report,world,payloads


def save(out, count=None, tokenizer=None):
    root=Path(out);root.mkdir(parents=True,exist_ok=False);report,world,payloads=calibrate(count=count,tokenizer=tokenizer)
    for name,value in [('report.synthetic.json',report),('world.synthetic.json',world),('memories.synthetic.json',payloads)]:write_once(root/name,value)
    source=Path(__file__).resolve().parents[1]
    manifest={str(p.relative_to(source)):file_hash(p) for p in sorted((source/'runaway').glob('*.py'))}
    write_once(root/'source-hashes.json',manifest)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True);parser.add_argument('--tokenizer');args=parser.parse_args();model=None
    try:
        count=None;metadata=None
        if args.tokenizer:
            import llama_cpp
            model=llama_cpp.Llama(model_path=args.tokenizer,vocab_only=True,n_gpu_layers=0,verbose=False)
            count=lambda text:len(model.tokenize(text.encode(),add_bos=False,special=False))
            metadata={'kind':'existing_local_gguf_tokenizer','model_sha256':file_hash(args.tokenizer),'actual_tokens_measured':True,'tokenization_only_no_model_inference':True}
        report=save(args.out,count,metadata)
        print(json.dumps({'passed':report['passed'],'checks':report['checks'],'external_model_calls':0}))
    finally:
        if model is not None:model.close()
