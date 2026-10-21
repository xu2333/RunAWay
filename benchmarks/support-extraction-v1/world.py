"""Six new synthetic policies. Gold lives here, never in extraction inputs."""
import hashlib
import json
from pathlib import Path
PEOPLE=['p17','p24','p38','p52','p69','p83']
AXES=['planning','automation','feedback','evidence','learning']
OPTIONS={
 'planning':{'probe':'先做可用小样，再按效果细化','map':'先理清完整结构与依赖，再实施','talk':'先访谈两位使用者，再动手'},
 'automation':{'auto':'默认自动处理，分错后恢复','sample':'先抽查一成结果，再决定是否整批采用','confirm':'逐项亲自确认再处理'},
 'feedback':{'warm':'先表达理解和肯定，再点问题','point':'第一句直接点问题，再给建议','ask':'先问对方想要哪种反馈，再谈问题'},
 'evidence':{'share':'标明暂定先向小组分享，边讨论边验证','check':'先做独立复核，再向小组分享','peer':'先私下与一位同行讨论，再决定是否公开','consent':'先取得相关人的明确许可，再考虑分享'},
 'learning':{'example':'先看一个完整具体例子，再读原理','formal':'先读正式定义和推导，再看例子','questions':'先通过互动提问定位问题，再看资料'}}
CURRENT={pid:{axis:list(OPTIONS[axis])[(i*(j+1)+j//2)%3] for j,axis in enumerate(AXES)} for i,pid in enumerate(PEOPLE)}
# Explicit independent, human-readable policy specification (not inferred from text).
CURRENT={
 'p17':dict(planning='probe',automation='sample',feedback='ask',evidence='share',learning='formal'),
 'p24':dict(planning='talk',automation='auto',feedback='point',evidence='peer',learning='questions'),
 'p38':dict(planning='map',automation='confirm',feedback='warm',evidence='check',learning='example'),
 'p52':dict(planning='talk',automation='sample',feedback='warm',evidence='check',learning='questions'),
 'p69':dict(planning='probe',automation='confirm',feedback='ask',evidence='peer',learning='example'),
 'p83':dict(planning='map',automation='auto',feedback='point',evidence='share',learning='formal')}
EXCEPTION=dict(planning='map',automation='confirm',feedback='point',evidence='check',learning='formal')
BASE={
 'planning':'设计一个尚未验证的入口，三个方案均能完成，没有截止压力。小样当天可免费撤回，改动没有长期代价。',
 'automation':'做熟悉的重复归类，自动约4%分错，手动更准但多一步。只改本地副本，任何分错都能立即恢复，不对外发送。',
 'feedback':'一对一私聊讨论一个重要但可修正的问题，没有紧急风险，对方未指定反馈的开场方式。',
 'evidence':'只有初步线索，尚未独立复核，且不涉及他人的保密内容。所有人知道是探索性讨论，想法可撤回，不会据此作实际决策。',
 'learning':'独自学习一个自己熟悉领域的新概念，有20分钟，无截止压力，也没人指定资料的讲解顺序。'}
EXCEPT={
 'planning':'设计尚未验证的入口，三个方案均可行，没有截止压力。一旦实施，半年不能撤回或调整。',
 'automation':'做熟悉的重复归类，自动约4%分错，手动更准但多一步。结果对外发送后无法撤回。',
 'feedback':'一对一私聊讨论一个重要但可修正的问题，无紧急风险，对方明确要求不要铺垫，第一句就点问题。',
 'evidence':'只有初步线索，尚未独立复核，不涉及保密内容。团队马上要据此作实际决定，误判代价明显。',
 'learning':'学习熟悉领域的新概念，有20分钟，无截止压力。对方明确要求先正式定义和推导，再举例。'}
PRIVATE_MISSING='只有初步线索，尚未独立复核。内容涉及别人的保密资料，尚未取得本人明确许可；团队马上要据此决策，误判代价明显。'
PRIVATE_GRANTED='只有初步线索，尚未独立复核。内容涉及别人的保密资料，但已取得本人明确许可；团队马上要据此决策，误判代价明显。'
TOPICS={
 'planning':['社团报名','科研日志','虚构约会回忆'],
 'automation':['私人录音标签','论文摘录归档','聊天贴纸分类'],
 'feedback':['小说提纲','证明草稿','演出介绍'],
 'evidence':['地图联系','模拟结果','方言线索'],
 'learning':['几何概念','编程概念','乐理概念']}


def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(value.encode()).hexdigest()


def source_data():
    result={}
    for pi,pid in enumerate(PEOPLE):
        rows=[]
        def episode(index,axis,condition,action,period,updated=False):
            eid='e%02d'%index;options=OPTIONS[axis];chosen=options[action];wrong=next(v for k,v in options.items() if k!=action)
            question=f'{period}，讨论{TOPICS[axis][pi%3]}。{condition}可选做法：'+'；'.join(options.values())+'。'
            decision=('我改为' if updated else '我的决定是')+chosen+'。'
            if updated:decision+='之前同样条件的做法不再沿用，以后同条件都按这次决定；其他情境的决定没有因此撤销。'
            else:decision+='按这里给出的条件，这是我实际采用的做法。'
            for role,suffix,text in [('user','q',question),('assistant','a','我更建议'+wrong+'。这只是我的建议，尚未得到你的确认。'),('user','u',decision)]:
                rows.append({'id':pid+'-'+eid+'-'+suffix,'episode_id':eid,'role':role,'text':text})
        for j,axis in enumerate(AXES):
            current=CURRENT[pid][axis];keys=list(OPTIONS[axis])[:3]
            old=keys[(keys.index(current)+1)%3] if axis=='planning' or (axis=='feedback' and pi%2==0) else current
            episode(j+1,axis,BASE[axis],old,'2026-01-10')
        for j,axis in enumerate(AXES):episode(j+6,axis,EXCEPT[axis],EXCEPTION[axis],'2026-02-15')
        episode(11,'evidence',PRIVATE_MISSING,'consent','2026-02-20')
        episode(12,'evidence',PRIVATE_GRANTED,'check','2026-02-21')
        for j,axis in enumerate(AXES):episode(j+13,axis,BASE[axis],CURRENT[pid][axis],'2026-03-12',axis=='planning' or (axis=='feedback' and pi%2==0))
        result[pid]={'schema_version':1,'sources':rows}
    return result


def case(axis,kind,question,rule,options=None):
    options=options or OPTIONS[axis];keys=list(options)
    scene='scene-'+digest(question)[:12]
    gold={pid:CURRENT[pid][axis] if rule=='current' else EXCEPTION[axis] if rule=='exception' else rule if rule in ('consent','check') else 'U' for pid in PEOPLE}
    if rule=='partial':
        gold={pid:CURRENT[pid][axis] if CURRENT[pid][axis]==EXCEPTION[axis] else 'U' for pid in PEOPLE}
    offset=int(digest(scene)[:2],16)%len(keys);keys=keys[offset:]+keys[:offset];orders=[]
    for i in range(len(keys)):
        order=keys[i:]+keys[:i]
        orders.append({'public':{'id':'q-'+digest(canonical([scene,i]))[:12],'scenario':question,'options':dict(zip('ABCDEFGH',[options[k] for k in order]))},'semantics':dict(zip('ABCDEFGH',order))})
    return {'scene':scene,'axis':axis,'kind':kind,'rule':rule,'question':question,'gold':gold,'orders':orders}


def world(fresh=False):
    rows=[]
    for axis in AXES:
        label=('未来架空'+TOPICS[axis][2]) if fresh else ('新的'+TOPICS[axis][1])
        rows.append(case(axis,'matched',label+'：'+BASE[axis],'current'))
    for axis in AXES:
        label=('另一次'+TOPICS[axis][0]) if fresh else ('跨领域'+TOPICS[axis][2])
        rows.append(case(axis,'exception',label+'：'+EXCEPT[axis],'exception'))
    changes={
      'planning':BASE['planning'].replace('没有截止压力','必须十分钟内交付' if fresh else '必须一小时内交付'),
      'automation':BASE['automation'].replace('约4%','约0.2%' if fresh else '约25%'),
      'feedback':BASE['feedback'].replace('一对一私聊','公开视频评议' if fresh else '公开十人评议'),
      'evidence':BASE['evidence'].replace('想法可撤回','内容永久不可删除或修改' if fresh else '观点发出后永久不可撤回'),
      'learning':BASE['learning'].replace('自己熟悉领域','自己完全陌生领域' if fresh else '完全陌生领域')}
    for axis,text in changes.items():rows.append(case(axis,'changed_condition',('另一个新任务：' if fresh else '这次的新情境：')+text,'unknown'))
    for axis in AXES:
        question=('题目再次省略信息。' if fresh else '题目省略一个条件。')+'本题仅可能对应两段记录情境之一：①'+BASE[axis]+'②'+EXCEPT[axis]+'没有其他可能。只问记录能否确定同一个选择，不问当事人面对信息不足时会创造什么新策略。'
        rows.append(case(axis,'partial',question,'partial'))
    rows.append(case('evidence','nested_exception',('新的资料汇总：' if fresh else '新的研究分享：')+PRIVATE_MISSING,'consent'))
    rows.append(case('evidence','exception_released',('另一次资料汇总：' if fresh else '另一次研究分享：')+PRIVATE_GRANTED,'check'))
    domain=[('晚餐偏好','同等价格营养和分量的晚餐，更喜欢哪种口味？',{'spicy':'微辣','mild':'清淡','sweet':'甜口'}),('约会偏好','条件相近且相互尊重的约会对象，更喜欢哪种日常兴趣？',{'outdoors':'户外旅行','cooking':'在家做饭','games':'桌游聚会'})]
    for axis,question,options in domain:rows.append(case(axis,'unobserved_domain',('另一个未给细节的问题：' if fresh else '')+question,'unknown',options))
    return {'people':PEOPLE,'cases':rows,'as_of':'2026-04-01','synthetic_only':True,'fresh_surface_not_new_policy':fresh}


def queries(world):
    rows=[];mapping={}
    # Orientations separated; all actions appear at every available label.
    for orientation in range(4):
        for c in world['cases']:
            if orientation>=len(c['orders']):continue
            public=c['orders'][orientation]['public'];key='q%02d'%(len(rows)+1)
            rows.append(dict(public,id=key));mapping[key]=public['id']
    return rows,mapping


def truth(value):
    return {pid:{q['public']['id']:('U' if c['gold'][pid]=='U' else next(label for label,meaning in q['semantics'].items() if meaning==c['gold'][pid])) for c in value['cases'] for q in c['orders']} for pid in PEOPLE}


def evaluate(value,answers):
    score={'known':{'planned':0,'correct':0,'false_abstention':0},'unknown':{'planned':0,'correct':0,'overreach':0},'order_consistent':0,'missing_variants':0,'by_kind':{},'by_axis':{},'by_person':{},'cases':{}}
    for pid in PEOPLE:
        for c in value['cases']:
            raw=[answers.get(pid,{}).get(q['public']['id']) for q in c['orders']]
            observed=[q['semantics'].get(v,v) for q,v in zip(c['orders'],raw)];gold=c['gold'][pid]
            valid=all(v=='U' or v in q['semantics'] for v,q in zip(raw,c['orders']))
            correct=valid and all(v==gold for v in observed);kind='unknown' if gold=='U' else 'known';item=score[kind];item['planned']+=1;item['correct']+=correct
            if kind=='known':item['false_abstention']+=any(v=='U' for v in raw)
            else:item['overreach']+=any(v is not None and v!='U' for v in raw)
            score['order_consistent']+=valid and len(set(observed))==1;score['missing_variants']+=sum(v is None for v in raw)
            for group,key in [('by_kind',c['kind']),('by_axis',c['axis']),('by_person',pid)]:
                row=score[group].setdefault(key,{'planned':0,'correct':0});row['planned']+=1;row['correct']+=correct
            score['cases'][pid+':'+c['scene']]={'person':pid,'kind':c['kind'],'axis':c['axis'],'gold':gold,'observed':observed,'correct':correct}
    score['strict_pass']=all(score[k]['correct']==score[k]['planned'] for k in ('known','unknown')) and score['missing_variants']==0
    return score
