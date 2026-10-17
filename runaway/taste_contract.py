"""Frozen task contract + code-only fixtures; never invokes a language model.

Current-choice transfer still requires resolving strength, conditions, active
constraints, replacements and revocations. Historical reconstruction remains a
separate scored diagnostic. This does not rewrite or rescore the D-0015 pilot.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from .card import canonical,digest
from .pipeline import write_once
from .synthetic_metric_world import resolve,render_event,VALUES,KEYS

ROOT=Path(__file__).resolve().parents[1]
CODE=('runaway/taste_contract.py','runaway/synthetic_metric_world.py','runaway/card.py','runaway/text_integrity.py')
READER=(
    'Predict the synthetic person’s choice from supplied memory, not your preferred solution. '
    'Memory may be ordinary prose, a timeline or structured text: dates and record IDs are not '
    'required formatting for an otherwise supported current choice. The envelope states source_cutoff; '
    'current_choice means a new scenario evaluated with preferences effective at that cutoff. '
    'Respect conditions, hard constraints, evidence strength, explicit changes and revocations; '
    'current explicit user instructions override past preference. Do not execute any option. '
    'For historical_reconstruction, require information that identifies the state at the requested '
    'past time; an unanchored current statement alone is insufficient. Choose U when the supplied '
    'memory genuinely does not establish a choice, not solely because it lacks record syntax. '
    'Return one object mapping every query ID to an answer_options ID. No hidden truth is supplied.'
)
CONTRACT={
    'version':1,'stage':'offline_contract_and_development_fixtures_not_model_evidence',
    'product_requirements':[
        {'requirement':'Portable carry-on of how one chooses and judges, rather than an identity label.',
         'origin':'User: 抽象的carryon，即做事的风格和方式; prompt塞进任何llm复现taste/选择/判断。',
         'tested_by':['current_choice','matched_person_distinctions','option_order_pairs']},
        {'requirement':'Accurate conditions, exceptions, uncertainty and latest effective preferences, including changes and revocations.',
         'origin':'User: 尽可能还原用户个人特征，越准越详细越好; existing product evidence/scope/change contract.',
         'tested_by':['strength','conditions','exceptions','hard_constraints','updates','revocations','unknowns']},
        {'requirement':'Readable prose across harnesses; the reader must not silently require a benchmark-specific record syntax.',
         'origin':'User: shared across codex/claude/antigravity/deepseek/opencode; readable portable prompt.',
         'tested_by':['semantically_equivalent_renderings','format_ablation_pending_model_validation']},
        {'requirement':'Trace genuine evidence, preserve the negative result and avoid invented preferences.',
         'origin':'User: 结合真实轨迹; compression fidelity is core, interaction/entertainment serves growth.',
         'tested_by':['source_to_profile_to_memory_audit','unknowns','historical_reconstruction']},
    ],
    'tasks':{
        'current_choice':{'role':'prospective primary for a new, separately frozen experiment',
            'definition':'Choice in a new same-scope scenario using preferences effective at explicit source_cutoff.',
            'planned_per_person':16,'requirements':['strength','conditions','exceptions','hard_constraints','updates','revocations','current_instruction','unknowns'],
            'exclusions':'Not an exemption from latest changes or conditional limits; no demographic/default-personality guessing.'},
        'historical_reconstruction':{'role':'independent diagnostic, never removed from D0015 or silently pooled away',
            'definition':'Recover a choice or fact at a specified earlier time.',
            'planned_per_person':8,'requirements':['old_fact','replacement','revocation','revocation_of_revocation'],
            'interpretation':'A current-only representation may intentionally be non-identifying for a past query; report this loss explicitly.'},
    },
    'scoring':{'primary':'Correct categorical choices / all16 planned current queries per person; failures remain.',
        'diagnostic':'Correct / all8 planned historical queries per person; always reported alongside primary.',
        'joint_reporting':'Also report unweighted correct/all24 and worst critical layer; never substitute a successful subset for D0015.',
        'pairing':'Both twins must be correct on their differing scenarios; both option orders must preserve action.',
        'abstention':'U is credited only for a code-defined unknown, never for a missing output.',
        'quality_vs_cost':'Full rendered memory length and all extraction/compression/reader costs stay separate.'},
    'gates':{'reader_full_history_current_accuracy_min':.90,'reader_hard_constraint_errors_max':0,
        'reader_wrong_person_must_reduce_matched_distinctions':True,
        'promotion':'No winner claim from current-score gain alone if any critical layer regresses or hard errors appear; historical losses remain visible.'},
    'reader_instruction':READER,
    'D0015':'All original scores, denominators, queries and answers remain sealed. These fixtures are development, not a new model result.',
    'limitations':['Finite authored event ontology and explicit source coverage; not an arbitrary person or population.',
        'Code-only answerability/format controls do not predict actual model response to a prompt repair.',
        'All future model inputs, cohort, protocol, budgets and thresholds must be frozen before new inference.'],
    'external_model_call_limit_for_this_work':0,
}


def contract():
    body={**CONTRACT,'source_hashes':{name:digest((ROOT/name).read_text()) for name in CODE}}
    return {**body,'id':digest(canonical(body))}


def events(feedback,layout,exception_bit,restored=True):
    opposite=lambda value,pair:next(v for v in pair if v!=value)
    def e(day,op,key=None,value=None,**kw):
        return {'id':f'r{day:02}','day':day,'op':op,**({'key':key} if key else {}),**({'value':value} if value else {}),**kw}
    rows=[e(1,'prefer','feedback',feedback,strength=3),
          e(2,'prefer','feedback',opposite(feedback,['direct','gentle']),strength=1),
          e(3,'replace','feedback',opposite(feedback,['direct','gentle']),strength=2),
          e(4,'revoke',target='r03'),
          e(5,'except','feedback',opposite(feedback,['direct','gentle']),when='public'),
          e(6,'prefer','auto','auto',strength=3),e(7,'hard','auto','ask',when='irreversible'),
          e(8,'revoke',target='r07')]
    if restored:rows.append(e(9,'revoke',target='r08'))
    rows.extend([e(10,'prefer','layout',layout,strength=2),
          e(11,'replace','layout',opposite(layout,['minimal','restore']),strength=3),
          e(12,'revoke',target='r11'),
          e(13,'except','layout','restore' if exception_bit else 'minimal',when='repeated'),
          e(14,'fact','mark','line'),e(15,'clear','mark')])
    return rows


def make_case(pid,index,task,question,key,at,context,values,tags,order=0,instruction=None):
    values=list(values)
    if order:values.reverse()
    options={label:VALUES[value] for label,value in zip(('A','B'),values)}|{'U':'材料不足，无法判断'}
    public={'id':'q-'+digest(pid+':'+str(index))[:14],'task':task,'question':question,'answer_options':options}
    if task=='historical_reconstruction':public['at']=at
    return {'public':public,'key':key,'at':at,'context':context,'tags':tags,
            'canonical_options':dict(zip(('A','B'),values))|{'U':'U'},
            'current_instruction':instruction,'comparison_key':str(index),'order_pair':str(index//2) if task=='current_choice' else None}


def cases(pid,split):
    rows=[]
    descriptions={
      'dev':[
        ('feedback',False,'在私下讨论一份汇报稿时，你会怎样指出其中可修正的问题？',['strength','updates','revocations','conditions']),
        ('feedback',True,'多人同时参与汇报稿评审时，你会怎样指出其中可修正的问题？',['exceptions','conditions']),
        ('auto',False,'整理任务可以完整撤销，你会选择哪种处理方式？',['conditions']),
        ('auto',True,'整理任务无法撤销，你会选择哪种处理方式？',['hard_constraints','revocations','conditions']),
        ('layout',False,'一个工具没有发生反复求助，入口采取哪种方案？',['updates','revocations','conditions']),
        ('layout',True,'组织者已经反复求助，工具入口采取哪种方案？',['exceptions','distinctions','conditions'])],
      'eval':[
        ('feedback',False,'你单独给合作者一份计算草稿提修改意见，开头采用哪种方式？',['strength','updates','revocations','conditions']),
        ('feedback',True,'草稿的修改意见将在多人评审现场提出，开头采用哪种方式？',['exceptions','conditions']),
        ('auto',False,'助手将归拢一组资料，所有变动都可恢复原样，你更倾向哪种方式？',['conditions']),
        ('auto',True,'助手将归拢一组资料，变动完成后不能恢复原样，你更倾向哪种方式？',['hard_constraints','revocations','conditions']),
        ('layout',False,'预约工具的组织者没有反复请求帮助，首页入口按哪种取舍设计？',['updates','revocations','conditions']),
        ('layout',True,'预约工具的组织者连续多次请求帮助，首页入口按哪种取舍设计？',['exceptions','distinctions','conditions'])],
      'transfer':[
        ('feedback',False,'你正一对一回应合作者可改正的设计问题，采用哪种反馈开场？',['strength','updates','revocations','conditions']),
        ('feedback',True,'这次设计问题要在整个协作小组面前反馈，采用哪种开场？',['exceptions','conditions']),
        ('auto',False,'新助手将整理一批标签，所有更改可以一步完整撤回，你倾向怎样操作？',['conditions']),
        ('auto',True,'新助手将整理一批标签，但这些更改将不能恢复，你倾向怎样操作？',['hard_constraints','revocations','conditions']),
        ('layout',False,'借阅工具的使用者未反复求助，主入口采取哪种布局？',['updates','revocations','conditions']),
        ('layout',True,'借阅工具的使用者已经反复求助，主入口采取哪种布局？',['exceptions','distinctions','conditions'])]}
    for key,flag,question,tags in descriptions[split]:
        contexts={'feedback':'public','auto':'irreversible','layout':'repeated'}
        values={'feedback':['direct','gentle'],'auto':['auto','ask'],'layout':['minimal','restore']}[key]
        for order in (0,1):rows.append(make_case(pid,len(rows),'current_choice',question,key,20,{contexts[key]:flag},values,tags,order))
    for order in (0,1):
        rows.append(make_case(pid,len(rows),'current_choice','这次整理虽然可撤销，但用户当前明确要求逐项确认，你应遵循哪种选择？','auto',20,{'irreversible':False},['auto','ask'],['current_instruction'],order,'ask'))
    for order in (0,1):
        rows.append(make_case(pid,len(rows),'current_choice','没有更多个人信息，要替此人挑一部影片，哪种偏好有材料支持？','film',20,{},['mystery','documentary'],['unknowns'],order))
    retrospective=[('feedback',3,{},['direct','gentle'],['updates']),
        ('auto',7,{'irreversible':True},['auto','ask'],['hard_constraints']),
        ('auto',8,{'irreversible':True},['auto','ask'],['revocations']),
        ('auto',9,{'irreversible':True},['auto','ask'],['revocation_of_revocation']),
        ('layout',11,{},['minimal','restore'],['updates']),('layout',12,{},['minimal','restore'],['revocations']),
        ('mark',14,{},['dot','line'],['old_fact']),('mark',16,{},['dot','line'],['unknowns'])]
    for key,at,context,values,tags in retrospective:
        condition='（整理操作无法撤销）' if context.get('irreversible') else '（不在公开场合）' if key=='feedback' else '（没有反复求助）' if key=='layout' else ''
        rows.append(make_case(pid,len(rows),'historical_reconstruction',f'仅问第{at}天当时的记录：{condition}【{KEYS[key]}】是什么选择？',key,at,context,values,tags))
    return rows


def canonical_choice(person,case):
    if case['current_instruction'] is not None:return case['current_instruction']
    return resolve(person['events'],case)[0]


def gold(person,case):
    wanted=canonical_choice(person,case)
    return next(label for label,value in case['canonical_options'].items() if value==wanted)


def build_world(seed=91627,mode='representative'):
    if mode not in ('representative','comparison'):raise ValueError('Unknown fixture mode')
    # Representative examples are development only. The future comparison uses
    # a different parameter combination and wording, selected before inference.
    people=[]
    selected=('direct','minimal') if int(digest(str(seed))[:8],16)%2 else ('gentle','restore')
    configs=[('dev','direct','restore',False),('eval','gentle','minimal',True)]
    if mode=='comparison':configs=[configs[0],('eval',selected[0],selected[1],True)]
    for split,feedback,layout,restored in configs:
        ids=['p-'+digest(f'{seed}:{split}:{bit}')[:12] for bit in (0,1)]
        for bit,pid in enumerate(ids):
            person={'id':pid,'twin':ids[1-bit],'split':split,'source_cutoff':20,
                    'parameters':{'feedback':feedback,'layout':layout,'hard_restored':restored,'exception_bit':bit},
                    'events':events(feedback,layout,bit,restored)}
            person['history']='合成记录完整覆盖下列领域至第20天；第15天后没有新增更改，未记录领域仍未知。\n'+'\n'.join(render_event(e,split) for e in person['events'])
            person['cases']=cases(pid,'transfer' if mode=='comparison' and split=='eval' else split)
            for case in person['cases']:case['gold']=gold(person,case)
            people.append(person)
    body={'origin':'fully_synthetic','purpose':'representative_development_fixtures_only' if mode=='representative' else 'future_comparison_not_run',
          'seed':seed,'mode':mode,'people':people}
    return {**body,'id':digest(canonical(body))}


def score(world,predictions,task):
    if task not in ('current_choice','historical_reconstruction','joint'):raise ValueError('Unknown task')
    people=[p for p in world['people'] if p['split']=='eval'];layers={};correct=planned=missing=hard_errors=violations=0
    for person in people:
        for case in person['cases']:
            if task!='joint' and case['public']['task']!=task:continue
            value=predictions.get(person['id'],{}).get(case['public']['id']);right=value==case['gold'];planned+=1;correct+=right;missing+=value is None
            for tag in case['tags']:
                row=layers.setdefault(tag,{'correct':0,'planned':0,'missing':0});row['correct']+=right;row['planned']+=1;row['missing']+=value is None
            if 'hard_constraints' in case['tags']:
                hard_errors+=not right;violations+=value is not None and value!='U' and not right
    twins_correct=twins_planned=0
    lookup={p['id']:p for p in people}
    for person in people:
        if person['id']>=person['twin']:continue
        for a,b in zip(person['cases'],lookup[person['twin']]['cases']):
            if task!='joint' and a['public']['task']!=task:continue
            if canonical_choice(person,a)==canonical_choice(lookup[person['twin']],b):continue
            twins_planned+=1;twins_correct+=(predictions.get(person['id'],{}).get(a['public']['id'])==a['gold'] and predictions.get(person['twin'],{}).get(b['public']['id'])==b['gold'])
    pairs={'correct':0,'consistent':0,'planned':0,'missing':0}
    if task in ('current_choice','joint'):
        for person in people:
            current=[c for c in person['cases'] if c['public']['task']=='current_choice']
            for a,b in zip(current[::2],current[1::2]):
                x=predictions.get(person['id'],{}).get(a['public']['id']);y=predictions.get(person['id'],{}).get(b['public']['id'])
                pairs['planned']+=1;pairs['missing']+=x is None or y is None
                pairs['correct']+=x==a['gold'] and y==b['gold']
                pairs['consistent']+=x in a['canonical_options'] and y in b['canonical_options'] and a['canonical_options'][x]==b['canonical_options'][y]
    return {'task':task,'correct':correct,'planned':planned,'missing':missing,'accuracy':correct/planned,
            'layers':layers,'hard_constraint_errors':hard_errors,'observed_hard_violations':violations,
            'matched_distinctions':{'correct':twins_correct,'planned':twins_planned},'option_order_pairs':pairs}


def policy_signature(person):
    return tuple(resolve(person['events'],{'key':key,'at':20,'context':context})[0]
        for key,context in [('feedback',{'public':False}),('feedback',{'public':True}),
            ('auto',{'irreversible':False}),('auto',{'irreversible':True}),
            ('layout',{'repeated':False}),('layout',{'repeated':True})])


def current_prose(person):
    f,p,a,h,l,r=policy_signature(person)
    return (f'截至材料截止时点，在与原记录同范围的新任务中：私下反馈选{VALUES[f]}，公开反馈选{VALUES[p]}；'
            f'可撤销的整理选{VALUES[a]}，不可撤销时选{VALUES[h]}；没有反复求助时入口选{VALUES[l]}，'
            f'反复求助时选{VALUES[r]}。当前明确要求优先；影片偏好无材料支持。'
            '这段只描述有效选择，不声称提供每个历史时点的信息。')


def compatibility_family(person):
    """Finite information witness, not a natural-language inference engine.

    All64 timelines have identical current policies. Transient choices, their
    times and a cleared old fact vary. This is an audit of the declared semantic
    projection; it does not annotate arbitrary model prose automatically.
    """
    family=[]
    for mark,hard,revoke,feedback,layout,clear in itertools.product((0,1),repeat=6):
        other=copy.deepcopy(person);events={e['id']:e for e in other['events']}
        events['r14']['value']='dot' if mark else 'line';events['r07']['day']=8 if hard else 7
        if revoke:
            events['r08']['day']=9
            if 'r09' in events:events['r09']['day']=10
        if feedback:events['r03']['day']=5;events['r04']['day']=6
        if layout:events['r11']['day']=12;events['r12']['day']=13
        if clear:events['r15']['day']=18
        family.append(other)
    return family


def answerability(person):
    family=compatibility_family(person);signature=policy_signature(person)
    compatible=[p for p in family if policy_signature(p)==signature]
    rows=[]
    for case in person['cases']:
        possible=sorted({canonical_choice(p,case) for p in compatible})
        rows.append({'query_id':case['public']['id'],'task':case['public']['task'],
                     'possible_canonical_answers':possible,'identified_in_this_finite_family':len(possible)==1})
    return {'semantic_projection':'six effective condition/action choices, known source cutoff and absent film domain',
            'not_a_parser_of_model_memory':True,'compatible_histories':len(compatible),'queries':rows}


def calibrate(world):
    controls={}
    for name in ('full_semantic_oracle','none','always_U','delete_exceptions','delete_hard','ignore_revocations'):
        values={}
        for person in (p for p in world['people'] if p['split']=='eval'):
            modified=copy.deepcopy(person)
            if name=='delete_exceptions':modified['events']=[e for e in person['events'] if e['op']!='except']
            if name=='delete_hard':modified['events']=[e for e in person['events'] if e['op']!='hard']
            if name=='ignore_revocations':modified['events']=[e for e in person['events'] if e['op']!='revoke']
            values[person['id']]={c['public']['id']:(
                'U' if name=='always_U' or name=='none' and c['current_instruction'] is None else gold(modified,c)
                ) for c in person['cases']}
        controls[name]={task:score(world,values,task) for task in ('current_choice','historical_reconstruction','joint')}
    proofs=[]
    for person in (p for p in world['people'] if p['split']=='eval'):
        alternative=copy.deepcopy(person)
        next(e for e in alternative['events'] if e['op']=='fact' and e['key']=='mark')['value']='dot'
        case=next(c for c in person['cases'] if c['key']=='mark' and c['at']==14)
        proofs.append({'kind':'current_state_does_not_identify_past_fact','person':person['id'],
            'same_current_projection':policy_signature(person)==policy_signature(alternative),
            'all_current_answers_equal':all(canonical_choice(person,c)==canonical_choice(alternative,c) for c in person['cases'] if c['public']['task']=='current_choice'),
            'distinct_past_answers':[canonical_choice(person,case),canonical_choice(alternative,case)],
            'conclusion':'This projection genuinely loses a past fact; a formatting wrapper cannot restore it.'})
        renamed=copy.deepcopy(person);mapping={e['id']:'event-'+str(i) for i,e in enumerate(person['events'])}
        for event in renamed['events']:
            event['id']=mapping[event['id']]
            if 'target' in event:event['target']=mapping[event['target']]
        proofs.append({'kind':'record_label_renaming_preserves_semantics','person':person['id'],
            'all_answers_equal':all(canonical_choice(person,c)==canonical_choice(renamed,c) for c in person['cases']),
            'conclusion':'Literal rNN syntax is not logically necessary; actual LLM format sensitivity remains untested.'})
    return {'kind':'deterministic_answerability_and_scorer_controls_not_model_effects','external_model_calls':0,
            'controls':controls,'proofs':proofs,
            'finite_answerability':{p['id']:answerability(p) for p in world['people'] if p['split']=='eval'},
            'current_prose':{p['id']:current_prose(p) for p in world['people'] if p['split']=='eval'}}


def freeze(out,seed=91627,mode='representative'):
    root=Path(out);root.mkdir(parents=True,exist_ok=False)
    spec=contract();write_once(root/'contract.json',spec)  # Written before fixtures.
    world=build_world(seed,mode);write_once(root/'fixtures.synthetic.json',world)
    write_once(root/'calibration.synthetic.json',calibrate(world))
    for name in CODE:
        target=root/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    jobs=[{'persona_id':p['id'],'source_cutoff':p['source_cutoff'],'instruction':READER,
           'memory':None,'queries':[c['public'] for c in p['cases']]} for p in world['people'] if p['split']=='eval']
    write_once(root/'reader-job-templates.jsonl',''.join(json.dumps(j,ensure_ascii=False)+'\n' for j in jobs))
    return {'contract_id':spec['id'],'fixture_id':world['id'],'external_model_calls':0,'development_only':mode=='representative'}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--out',required=True);f.add_argument('--seed',type=int,default=91627);f.add_argument('--mode',choices=('representative','comparison'),default='representative')
    s=sub.add_parser('score');s.add_argument('--run',required=True);s.add_argument('--answers',required=True);s.add_argument('--out',required=True)
    a=p.parse_args()
    if a.command=='freeze':result=freeze(a.out,a.seed,a.mode)
    else:
        root=Path(a.run);spec=json.loads((root/'contract.json').read_text());world=json.loads((root/'fixtures.synthetic.json').read_text())
        if spec!=contract() or world!=build_world(world['seed'],world['mode']):raise ValueError('Contract, source or fixture changed')
        predictions=json.loads(Path(a.answers).read_text())
        if not isinstance(predictions,dict):raise ValueError('Answers must map persona IDs to query/option IDs')
        people={p['id']:p for p in world['people'] if p['split']=='eval'}
        for pid,answers in predictions.items():
            if pid not in people or not isinstance(answers,dict):raise ValueError('Unknown person or malformed answer map')
            queries={c['public']['id']:c for c in people[pid]['cases']}
            for qid,value in answers.items():
                if qid not in queries or not isinstance(value,str) or value not in queries[qid]['canonical_options']:raise ValueError('Unknown query or option')
        result={'contract_id':spec['id'],'fixture_id':world['id'],'external_model_calls_by_scorer':0,
            'rows':[score(world,predictions,task) for task in ('current_choice','historical_reconstruction','joint')],
            'model_effects_verified':False}
        write_once(Path(a.out),result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
