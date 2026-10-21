"""New authored synthetic histories and finite scope tables; no model calls.

Policies/hand tables never enter extraction or reading requests. Histories and
held-out scenario prose are separate authored surfaces. This is a small synthetic
pilot, not a population sample or an external benchmark.
"""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from runaway.card import canonical,digest
from runaway.profile import validate_sources

PEOPLE=('t04a','t11b','t35c','t92d')
DONORS={'t04a':'t11b','t11b':'t04a','t35c':'t92d','t92d':'t35c'}
ACTIONS={
 'research':['标明暂定后立即分享','先补独立复核，再分享','只发研究问题，不发当前结论'],
 'collaboration':['先听完背景再给意见','先指出一个最关键问题','先问希望得到哪种反馈'],
 'relationship':['先发一句关心后等待对方开口','先问现在想独处还是聊聊','约好次日再聊，不继续发消息'],
 'travel':['现在订下并保留撤销机会','再比两家后决定','先不订，等行程完全确定']}
# State tuples are explicit finite observed conditions, not inferred monotonic rules.
STATES={
 'research':[(5,'internal','unverified','no_decision','no_confidential'),(5,'public','unverified','no_decision','no_confidential'),(5,'public','checked','no_decision','no_confidential')],
 'collaboration':[(30,'private','no_urgent','no_requested_style'),(30,'group','no_urgent','no_requested_style'),(10,'private','no_urgent','no_requested_style')],
 'relationship':[('vent','quiet','tonight','no_urgent'),('vent','quiet','tomorrow','no_urgent'),('vent','talk','tonight','no_urgent')],
 'travel':[(800,'refundable','uncertain','self'),(800,'nonrefundable','uncertain','self'),(1600,'refundable','uncertain','self')]}
# Authored decisions; no generated prompt or reader result changes these tables.
CHOICES={
 't04a':{'research':[0,1,0],'collaboration':[0,2,1]},
 't11b':{'research':[1,1,1],'collaboration':[1,1,1]},
 't35c':{'relationship':[0,0,1],'travel':[0,1,0]},
 't92d':{'relationship':[1,2,2],'travel':[2,2,2]}}
HISTORY_CONTEXT={
 'research':[
 '今天这份研究结论还没有独立复核，只给固定5人的研究小组内部看。大家知道是探索讨论，不据此作实际决策，也不涉及他人保密内容。',
 '这次研究仍未经独立复核，原固定5人小组转为向陌生人公开。仍只是探索讨论，不作实际决策，不涉他人保密。',
 '研究已经独立复核完成，原固定5人小组想向陌生人公开讨论。仍不会据此实际决策，也没有他人保密内容。'],
 'collaboration':[
 '今天有30分钟，在一对一私聊里给同事反馈；问题可以修改，没有紧急风险，对方没要求特定反馈方式。',
 '这次还是30分钟，但改成小组会上给同事反馈。问题可修改，没有紧急风险，对方没要求特定方式。',
 '今天反馈只留10分钟，仍是一对一私聊；问题可修改，没有紧急风险，对方没指定方式。'],
 'relationship':[
 '亲近的人只是在吐槽，没有要我出解决方案；明确说今晚想安静，没有紧急风险。',
 '亲近的人只吐槽、没要解决方案，明确说想安静。我准备次日再联系；没有紧急风险。',
 '亲近的人只是在吐槽、没要解决方案，明确说今晚想聊聊，没有紧急风险。'],
 'travel':[
 '我独自旅行，行程还没完全确定，房间每晚800元，能够免费取消。',
 '独自出行计划仍没完全定，房间每晚800元，一旦订下不能取消。',
 '独自旅行，行程还没完全定，这次房间1600元，可以免费取消。']}
SCENES={
 'research':[
 '一个天文分析的新结论尚未独立验证，只面向固定五人研究组内讨论；注明探索性质，不用于任何实际决策，也没有涉及别人的保密内容。会怎么分享？',
 '原来的固定五人研究组准备把未经独立复核的结论给陌生人公开看；明确只是探索性讨论、不据此行动，不含他人保密内容。会怎样做？',
 '固定五人研究组的一份新结果已完成独立复核，拟向陌生人公开；用途仍是探索交流，不用于实际决策，不涉他人保密。会怎么做？',
 '一项未经独立复核的结果只在固定六人研究组内部讨论；注明探索性质，不用于实际决策，不含他人保密。会怎么分享？',
 '未经独立复核的结果拟给固定五人研究组内部讨论，但这次会直接用于实际决策；不涉及他人保密。会怎么分享？',
 '材料已经明确本题只可能是两个已发生的情境之一：未独立复核、固定五人研究组内部交流；或同样未复核、原五人小组转为向陌生人公开。两种都仅供探索、不据此决策、不涉保密。没有其他可能，但没告诉你是哪一种。问记录能否确定一个相同做法。',
 '背景题材改为海洋观测：结果尚未独立复核，只给固定五人研究组内部探索讨论，不用于实际决策，不涉他人保密。投影采用深色背景。会怎样分享？',
 '未经独立复核的研究结果仅给固定五人组内探索讨论，不据此决策，不含保密内容。以下做法中，能否确定哪一个就是记录里的选择？'],
 'collaboration':[
 '为一个可修改的设计给同事反馈，有半小时，只有双方私聊，无紧急风险，也没指定反馈方式。会如何开场？',
 '在小组会上给同事一个能修改的工作反馈，留有半小时，无紧急风险，对方也没指定开场方式。会怎么开始？',
 '同事反馈需要在十分钟内聊完，只有双方私聊，问题可修改、没有紧急风险，也没指定开场方式。会怎样开场？',
 '双方私聊给同事可修改的工作反馈，这回留四十五分钟，没有紧急风险，也没指定开场方式。会怎么开始？',
 '有半小时一对一私聊，但反馈的问题现在有紧急风险，对方没指定开场方式。会怎样开场？',
 '只可能是两个已记录情境之一：留半小时、一对一私聊；或留半小时、在小组会上反馈。都针对可修改的问题，没有紧急风险，对方没指定方式。除此没有可能，但未说明是哪一个。现有记录能否确定相同开场？',
 '同事希望对可修改的配色工作给反馈，双方单独聊半小时，没有紧急风险，也未指定开场方式。座位旁摆着一盆绿植。会如何开场？',
 '双方私聊半小时，给同事可修改的工作反馈，没有紧急风险、没有指定开场方式。下面列出的做法，哪一个能够由记录确定？'],
 'relationship':[
 '关系亲近的人在倾诉烦恼，并没有请你解决问题；对方清楚表示今夜想自己安静，无紧急风险。此时会怎么联系？',
 '亲近的人只倾诉、没有要解决方案，明确想安静，无紧急风险。你要等到第二天再联系，会怎么做？',
 '亲近的人只是倾诉、没有请你解决问题，明确表示今天夜里想聊，无紧急风险。你会怎样联系？',
 '亲近的人只倾诉、没要解决方案，明确表示今晚想安静；这次有紧急风险。会怎么联系？',
 '亲近的人今晚明确想安静，但这次明确要你给解决方案，没有紧急风险。会怎样联系？',
 '本题只可能是两个已记录情境之一：亲近的人只吐槽、没要方案、明确想安静，你今晚联系；或同样条件下你次日联系。两者均无紧急风险，没有其他可能，但没说明是哪一种。问记录是否确定相同做法。',
 '亲近的人因新学的陶艺感到沮丧，只是倾诉、不需要方案，明确说今晚想安静，没有紧急风险。窗外正在下小雨。会怎么联系？',
 '亲近的人只在吐槽、不要解决方案，明确说今晚想安静，没有紧急风险。下面的做法里，能否确定哪一个就是本人已记录的选择？'],
 'travel':[
 '独自出行的安排仍未定妥，酒店一晚八百元，可以免费撤订。会怎么预订？',
 '一个人旅行的安排还不确定，一晚房价八百元，订后不能取消。会怎么预订？',
 '独自旅行的日程没完全确定，房间一晚一千六百元，可免费取消。会怎样预订？',
 '独自出行，行程仍未完全确定，房间一晚六百元，可免费取消。会怎样预订？',
 '这次和朋友一起旅行，行程还不确定，房间八百元，可免费取消。会怎么订？',
 '只有两种已记录可能：独自行程没定、房间八百元可免费取消；或同样独自行程没定、八百元但不能取消。除此没有可能，尚未告诉你是哪种。问记录能否确定同一做法。',
 '独自去看一个新展览，行程还没定妥，房间每晚八百元，可免费取消。订房网页使用橙色按钮。会怎么预订？',
 '独自旅行、计划没完全定，一间房八百元，可以免费取消。以下列出的做法里，能否确定哪一个就是本人已记录的选择？']}
# Independent hand table: action indices, U=unknown action, and scope state.
# For absent-option cases the offered list omits action0. Other-domain cases are U.
HAND={
 't04a':{'research':[0,1,0,'U','U','U',0,'U'],'collaboration':[0,2,1,'U','U','U',0,'U']},
 't11b':{'research':[1,1,1,'U','U',1,1,1],'collaboration':[1,1,1,'U','U',1,1,1]},
 't35c':{'relationship':[0,0,1,'U','U',0,0,'U'],'travel':[0,1,0,'U','U','U',0,'U']},
 't92d':{'relationship':[1,2,2,'U','U','U',1,1],'travel':[2,2,2,'U','U',2,2,2]}}
KINDS=('matched','paraphrase','exception','changed_number_or_risk','changed_required_condition','partial_exhaustive','irrelevant_detail','known_action_not_offered')


def fixtures():
 histories={};policies={};cases=[];queries=[]
 for pid in PEOPLE:
  records=[];effective=[]
  for axis,choices in CHOICES[pid].items():
   old_id=None
   for state_index,action in enumerate(choices):
    episode='e'+str(len(records)+1)
    def add(role,text):
     sid='s'+str(len(records)+1);records.append({'id':sid,'episode_id':episode,'role':role,'text':text});return sid
    add('user',HISTORY_CONTEXT[axis][state_index])
    # A superseded explicit user choice on the first branch, followed by a clear update.
    if state_index==0:
     old_id=add('user','我当时决定：'+ACTIONS[axis][(action+1)%3]+'。')
     add('assistant','也可以考虑'+ACTIONS[axis][(action+2)%3]+'，这是我的建议，不代表你已决定。')
     add('user','还是刚才同样的具体条件。我改主意了，上一个决定作废，现在我选：'+ACTIONS[axis][action]+'。')
    else:
     add('assistant','我的建议是'+ACTIONS[axis][(action+1)%3]+'。')
     add('user','这次我明确选：'+ACTIONS[axis][action]+'。我只记录这次具体条件下的选择。')
    effective.append({'axis':axis,'state':list(STATES[axis][state_index]),'action':action})
  histories[pid]={'schema_version':1,'sources':records};validate_sources(histories[pid]);policies[pid]=effective
 for axis,scenes in SCENES.items():
  for index,scene in enumerate(scenes):
   kinds=KINDS[index];states=[list(STATES[axis][k]) for k in ([0,1] if index==5 else [index if index<3 else 0])]
   if index in (3,4):states=[['unobserved_context_'+str(index)]]
   offered=list(range(1 if index==7 else 0,3));orders=[]
   for rotation in range(len(offered)):
    order=offered[rotation:]+offered[:rotation];qid='q'+digest(axis+':'+str(index)+':'+str(rotation))[:12]
    public={'id':qid,'scenario':scene,'options':dict(zip('ABC',[ACTIONS[axis][i] for i in order]))}
    orders.append({'public':public,'semantic_options':dict(zip('ABC',order))});queries.append(public)
   gold={};scope={}
   for pid in PEOPLE:
    matching=[];uncovered=False
    for state in states:
     hits=[r['action'] for r in policies[pid] if r['axis']==axis and r['state']==state]
     if not hits:uncovered=True
     matching+=hits
    scope[pid]='uncovered' if uncovered else 'determinate' if len(set(matching))==1 else 'ambiguous'
    gold[pid]=matching[0] if scope[pid]=='determinate' and matching[0] in offered else 'U'
    manual=HAND.get(pid,{}).get(axis,['U']*8)[index]
    if gold[pid]!=manual:raise ValueError('Oracle disagrees with independent hand table')
   cases.append({'id':axis+':'+str(index),'axis':axis,'kind':kinds,'possible_states':states,'gold':gold,'scope_gold':scope,'orders':orders})
 queries.sort(key=lambda q:digest(q['id']))
 return {'synthetic':True,'people':list(PEOPLE),'donors':DONORS,'histories':histories,'policies':policies,'hand_expected':HAND,'cases':cases,'queries':queries}


def evaluate(f,answers,scopes=None):
 counts={key:{'planned':0,'correct':0,'missing':0} for key in ['known','unknown','joint','scope','scope_choice_joint','order_consistent']};errors=[];by_kind={};by_person={};by_unknown_reason={}
 for case in f['cases']:
  for pid in PEOPLE:
   gold=case['gold'][pid];kind='known' if gold!='U' else 'unknown';observed=[];reported=[]
   for order in case['orders']:
    qid=order['public']['id'];v=answers.get(pid,{}).get(qid);observed.append(order['semantic_options'].get(v,v));reported.append((scopes or {}).get(pid,{}).get(qid))
   right=all(v==gold for v in observed);missing=any(v is None for v in observed);scope_right=all(v==case['scope_gold'][pid] for v in reported)
   for k,correct,miss in [(kind,right,missing),('joint',right,missing),('scope',scope_right,any(v is None for v in reported)),('scope_choice_joint',right and scope_right,missing or any(v is None for v in reported)),('order_consistent',not missing and len(set(observed))==1,missing)]:
    counts[k]['planned']+=1;counts[k]['correct']+=int(correct);counts[k]['missing']+=int(miss)
   reason='known' if gold!='U' else 'unobserved_domain' if case['axis'] not in CHOICES[pid] else 'known_action_not_offered' if case['scope_gold'][pid]=='determinate' else 'ambiguous' if case['scope_gold'][pid]=='ambiguous' else 'outside_observed_conditions'
   for table,key in [(by_kind,case['kind']),(by_person,pid),(by_unknown_reason,reason)]:
    row=table.setdefault(key,{'planned':0,'correct':0});row['planned']+=1;row['correct']+=int(right)
   if not right or (scopes is not None and not scope_right):errors.append({'person':pid,'case':case['id'],'kind':case['kind'],'gold':gold,'observed':observed,'scope_gold':case['scope_gold'][pid],'reported_scope':reported,'choice_correct':right,'scope_correct':scope_right})
 return {**counts,'by_kind':by_kind,'by_person':by_person,'by_unknown_reason':by_unknown_reason,'errors':errors,'strict_choice_pass':counts['joint']['correct']==counts['joint']['planned'] and not counts['joint']['missing'],'scope_measured':scopes is not None}

if __name__=='__main__':
 f=fixtures();print(json.dumps({'people':len(PEOPLE),'scenes':len(f['cases']),'queries_per_call':len(f['queries']),'cases':len(PEOPLE)*len(f['cases']),'known':sum(c['gold'][p]!='U' for c in f['cases'] for p in PEOPLE)},indent=2))
