"""Executable synthetic event semantics. No LLM supplies the reference answers."""
import itertools
import random
import re
from .card import canonical,digest

KEYS={'mark':'标记','time':'工作时段','feedback':'反馈','auto':'整理操作','layout':'入口布局','film':'影片'}
VALUES={'dot':'圆点','line':'短线','morning':'早晨','evening':'傍晚','direct':'直说','gentle':'铺垫','auto':'自动','ask':'逐项确认','minimal':'简洁','restore':'显眼入口','mystery':'侦探片','documentary':'纪录片'}
REVERSE_KEYS={v:k for k,v in KEYS.items()};REVERSE_VALUES={v:k for k,v in VALUES.items()}
ANSWER_KEYS={'mark':['dot','line'],'time':['morning','evening'],'feedback':['direct','gentle'],'auto':['auto','ask'],'layout':['minimal','restore'],'film':['mystery','documentary']}


def answer_options(key,strength=False):
    return {k:VALUES.get(k,k) for k in (['0','1','2','3'] if strength else ANSWER_KEYS[key])}|{'U':'无足够依据'}


def active_events(events,at):
    selected=sorted([e for e in events if e['day']<=at],key=lambda e:(e['day'],e['id']))
    revoked=set()
    for event in reversed(selected):
        if event['id'] not in revoked and event['op']=='revoke':revoked.add(event['target'])
    return [e for e in selected if e['id'] not in revoked and e['op']!='revoke']


def resolve(events,query):
    events=[e for e in active_events(events,query['at']) if e.get('key')==query['key']]
    clears=[e['day'] for e in events if e['op']=='clear'];cut=max(clears,default=-1)
    events=[e for e in events if e['day']>cut and e['op']!='clear']
    context=query.get('context',{})
    def matching(event):return event.get('when') is None or context.get(event['when']) is True
    winner=None
    for kind in ['hard','except']:
        rows=[e for e in events if e['op']==kind and matching(e)]
        if rows:winner=rows[-1];break
    if winner is None:
        rows=[]
        for event in events:
            if event['op']=='replace':rows=[event]
            elif event['op'] in ('fact','prefer'):rows.append(event)
        if rows:
            if all(e['op']=='fact' for e in rows):winner=rows[-1]
            else:winner=max(rows,key=lambda e:(e.get('strength',0),e['day']))
    if winner is None:return 'U',None
    return (str(winner.get('strength',0)) if query.get('answer_kind')=='strength' else winner['value']),winner['op']


def render_event(event,split='eval',compact=False):
    key=KEYS.get(event.get('key'),'');op=event['op']
    value=VALUES.get(event.get('value'),'');strength=event.get('strength',0)
    if op=='fact':body=f'事实【{key}】是「{value}」'
    elif op=='prefer':body=f'偏好【{key}】是「{value}」，强度{strength}'
    elif op=='replace':body=f'更新替代【{key}】为「{value}」，强度{strength}，替代之前偏好'
    elif op=='clear':body=f'清除【{key}】；此后暂无这个偏好'
    elif op=='revoke':body=f'撤销记录{event["target"]}；其余记录继续适用'
    else:
        condition={'public':'公开场合','irreversible':'无法撤销','repeated':'反复求助'}[event['when']]
        body=f'{"硬约束" if op=="hard" else "条件例外"}【{key}】：若{condition}，选「{value}」'
    if compact:return f'第{event["day"]}天#{event["id"]}：{body}。'
    if split=='dev':return f'第{event["day"]}天（{event["id"]}）：我记下：{body}。这是当时这类任务的记录，不推断其他领域。'
    return f'记录{event["id"]} / 第{event["day"]}天：这一天的说明是：{body}。仅据这段经历，不把局部取舍扩成一般人格。'


def parse_history(text):
    """Transparent protocol reader for metric calibration, not an LLM decoder."""
    events=[]
    for line in text.splitlines():
        day=re.search(r'第(\d+)天',line);identity=re.search(r'(?:记录|#|（)(r\d+)',line)
        if not day or not identity:continue
        event={'day':int(day.group(1)),'id':identity.group(1)}
        if '撤销记录' in line:
            target=re.search(r'撤销记录(r\d+)',line)
            if target:events.append({**event,'op':'revoke','target':target.group(1)})
            continue
        key=re.search(r'【([^】]+)】',line)
        if not key or key.group(1) not in REVERSE_KEYS:continue
        event['key']=REVERSE_KEYS[key.group(1)]
        if '清除【' in line:event['op']='clear';events.append(event);continue
        value=re.search(r'「([^」]+)」',line)
        if not value or value.group(1) not in REVERSE_VALUES:continue
        event['value']=REVERSE_VALUES[value.group(1)]
        if '硬约束【' in line:event['op']='hard'
        elif '条件例外【' in line:event['op']='except'
        elif '更新替代【' in line:event['op']='replace'
        elif '偏好【' in line:event['op']='prefer'
        else:event['op']='fact'
        if event['op'] in ('hard','except'):
            event['when']='public' if '公开场合' in line else 'irreversible' if '无法撤销' in line else 'repeated'
        strength=re.search(r'强度(\d+)',line)
        if strength:event['strength']=int(strength.group(1))
        events.append(event)
    return events


def persona_events(parameters,exception_bit):
    mark,time,feedback,autonomy,layout=parameters
    def e(day,op,key=None,value=None,**kwargs):return {'day':day,'id':f'r{day:02}', 'op':op,**({'key':key} if key else {}),**({'value':value} if value else {}),**kwargs}
    return [e(1,'fact','mark',mark),e(2,'prefer','feedback',feedback,strength=3),e(3,'prefer','feedback','gentle' if feedback=='direct' else 'direct',strength=1),
            e(4,'except','feedback','gentle' if feedback=='direct' else 'direct',when='public'),e(5,'prefer','auto',autonomy,strength=3),e(6,'hard','auto','ask',when='irreversible'),
            e(7,'fact','time',time),e(8,'fact','time','evening' if time=='morning' else 'morning'),e(9,'revoke',target='r08'),e(10,'clear','mark'),
            e(11,'prefer','layout',layout,strength=2),e(12,'replace','layout','restore' if layout=='minimal' else 'minimal',strength=3),e(13,'revoke',target='r12'),
            e(14,'except','layout','restore' if exception_bit else 'minimal',when='repeated'),e(15,'revoke',target='r06')]


def queries(persona_id,split):
    # Query text/templates are distinct by split. Metadata for strata stays private.
    specs=[('mark',2,{},'facts'),('mark',11,{},'updates'),('time',7,{},'facts'),('time',8,{},'updates'),('time',10,{},'revocations'),
           ('feedback',3,{},'strength'),('feedback',3,{'public':True},'conditions'),('feedback',4,{'public':False},'conditions'),('feedback',4,{'public':True},'exceptions'),
           ('auto',5,{'irreversible':False},'conditions'),('auto',5,{'irreversible':True},'updates'),('auto',6,{'irreversible':True},'hard_constraints'),('auto',14,{'irreversible':True},'hard_constraints'),
           ('auto',14,{'irreversible':False},'conditions'),('layout',11,{},'facts'),('layout',12,{},'updates'),('layout',13,{},'revocations'),
           ('layout',14,{'repeated':False},'conditions'),('layout',14,{'repeated':True},'distinctions'),('layout',15,{'repeated':True},'distinctions'),('layout',16,{'repeated':True},'distinctions'),
           ('auto',16,{'irreversible':True},'revocations'),('film',16,{},'unknowns')]
    rows=[]
    for i,(key,at,context,stratum) in enumerate(specs):
        question=(f'到第{at}天为止，【{KEYS[key]}】会选什么？' if split=='dev' else f'请按第{at}天当时有效的记录，恢复【{KEYS[key]}】的选择。')+('情境：'+canonical(context) if context else '')
        public={'id':'q-'+digest(persona_id+str(i))[:14],'question':question,'key':key,'at':at,'context':context,'answer_kind':'value','answer_options':answer_options(key)}
        rows.append({'public':public,'stratum':stratum,'comparison_key':str(i)})
    public={'id':'q-'+digest(persona_id+'strength')[:14],'question':'第3天有效的反馈偏好强度是多少？','key':'feedback','at':3,'context':{},'answer_kind':'strength','answer_options':answer_options('feedback',True)}
    rows.append({'public':public,'stratum':'strength','comparison_key':'strength'})
    return rows


def build_world(seed=71317,pairs_per_split=4):
    if not 1<=pairs_per_split<=8:raise ValueError('Choose1–8pairs per split')
    rng=random.Random(seed);combinations=list(itertools.product(['dot','line'],['morning','evening'],['direct','gentle'],['auto','ask'],['minimal','restore']));rng.shuffle(combinations)
    # Coverage is chosen before any model or metric output: each split includes
    # an automatic-action policy so deleting the hard constraint is observable.
    for offset in (0,pairs_per_split):
        if combinations[offset][3]!='auto':
            index=next(i for i in range(offset+1,len(combinations)) if combinations[i][3]=='auto')
            combinations[offset],combinations[index]=combinations[index],combinations[offset]
    people=[]
    for split,offset in [('dev',0),('eval',pairs_per_split)]:
        for pair in range(pairs_per_split):
            params=combinations[offset+pair];members=['p-'+digest(f'{seed}:{split}:{pair}:{bit}')[:12] for bit in range(2)]
            for bit,pid in enumerate(members):
                events=persona_events(params,bit);cases=queries(pid,split)
                for case in cases:
                    answer,winner=resolve(events,case['public']);case['allowed_answers']=[answer];case['winning_op']=winner
                people.append({'id':pid,'twin':members[1-bit],'split':split,'parameters':list(params),'exception_bit':bit,'events':events,
                               'history':'\n'.join(render_event(e,split) for e in events),'queries':cases})
    body={'schema_version':1,'origin':'fully_synthetic','seed':seed,'people':people,'limitations':'Finite event grammar and reference protocol decoder; not a real-person or LLM performance benchmark.'}
    return {**body,'id':digest(canonical(body))}
