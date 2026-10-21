"""Alternative long histories preserving the four consumed final policies.

Every episode contains a dated user decision, an assistant alternative and a
post-decision observation. Historical decisions change; only the final six
context/action pairs are targets. This is current-state reconstruction, not
retention of all episodic information or a new population of users.
"""
import copy
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('long_base_world',HERE.parent/'fresh-boundary-v1/world.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from runaway.card import digest
from runaway.profile import validate_sources
PEOPLE=base.PEOPLE;DONORS=base.DONORS
RATIONALES={
 'research':[
 '我愿意先把讨论开展起来，但受众、证据阶段和是否据此实际决策都不能偷换。这里的分享只是刚才这组条件里的选择。',
 '这一次我宁可把复核放在分享前，先让依据站稳。这不是对所有领域和所有证据阶段都一概适用的决定。',
 '这次我只想交流研究问题，不把当前结论一起抛出去。受众或用途换了，需要另问，不能自动扩大这条记录的范围。'],
 'collaboration':[
 '这次先听背景是为了知道对方卡在哪里，不是保证每次都这样。开场方式没有被要求、时间和私聊条件都要保留。',
 '在这个情境我需要先把最关键的问题说清楚，之后怎样展开还看对方的反应。不能把一次开场选法当成所有场合的要求。',
 '这一次我先确认对方希望怎样交流。先问并非永远拖延给建议，也不能省略刚才说的时间、受众和没有紧急风险这些条件。'],
 'relationship':[
 '我想留出对方决定何时开口的空间，先表达关心就停下。这里既没有紧急风险，也没有让我解决问题的要求，不推到别的关系或场景。',
 '这一回我先把是否聊天的决定交给对方确认，语气会轻一些。不要把问一次写成随时追问，也不要忽略对方刚才表达的意愿。',
 '我这次先把联系留到约好的下一次，不继续追加消息。这只是对方刚才那种意愿和联络时点下的选择，不代表一直不回应。'],
 'travel':[
 '这回我愿意先占住能撤回的安排，之后再看日程。价位、是否独行以及取消条件都不要省略，换一个组合不能替我决定。',
 '我愿意为再比较两家付出一点时间，不急着把这次预订定下来。这不等于永远找最低价，也不把一次价位自动扩成整个价格区间。',
 '这一次我先等行程完全确定。不能因此说我所有事情都犹豫，也不能把这个做法扩到记录以外的金额、同行人或取消条件。']}
OBSERVATIONS={
 'research':'讨论记录里有人更看重速度，有人更看重材料是否站得住；这些是其他人的看法，不是这个用户的新决定。',
 'collaboration':'会后记录区分了开场和后续反馈内容，后续要不要改建议还没有发生；这条工具记录不能代替用户认可另一种开场。',
 'relationship':'对方是否回应还没有结论，不能把尚未发生的回应编成这个用户的偏好，也不应把工具生成的建议视为背书。',
 'travel':'预订页面中还出现了另一种方案的比较，但没有替用户付款或改变决定；比较结果本身不表示本人接受了它。'}
GAP_CONTEXT={
 'research':'这份研究结论未经独立复核，只给固定7人的研究小组内部探索讨论，不用于实际决策，不涉他人保密内容。',
 'collaboration':'有20分钟在一对一私聊里给同事反馈，问题可修改，没有紧急风险，对方没要求特定反馈方式。',
 'relationship':'亲近的人只是在吐槽、没有要解决方案，明确想安静。你要后天再联系，没有紧急风险。',
 'travel':'独自旅行的行程还没定，一间房每晚1200元，可以免费取消。'}
GAP_STATE={'research':[7,'internal','unverified','no_decision','no_confidential'],'collaboration':[20,'private','no_urgent','no_requested_style'],'relationship':['vent','quiet','after_two_days','no_urgent'],'travel':[1200,'refundable','uncertain','self']}
THREE_HAND={'research':{'t04a':'U','t11b':1,'t35c':'U','t92d':'U'},'collaboration':{'t04a':'U','t11b':1,'t35c':'U','t92d':'U'},'relationship':{'t04a':'U','t11b':'U','t35c':'U','t92d':'U'},'travel':{'t04a':'U','t11b':'U','t35c':'U','t92d':2}}


def long_sources(pid):
 rows=[]
 for era,date in enumerate(['2026-05-01','2026-07-01','2026-09-01']):
  for axis,choices in base.CHOICES[pid].items():
   for state,current in enumerate(choices):
    action=current if era==2 else (current+era+1)%3
    if axis=='travel' and state==1:action=current if era==2 else (2 if current==1 else 1)
    episode='e%03d'%(len(rows)+1)
    def add(role,text):rows.append({'id':'s%03d'%(len(rows)+1),'episode_id':episode,'role':role,'text':text})
    add('user',date+' 的记录。'+base.HISTORY_CONTEXT[axis][state])
    alternative=base.ACTIONS[axis][(action+1)%3]
    add('assistant','如果只看一个方面，我会建议'+alternative+'。这只是我的建议，还没有得到你的背书。')
    if era==2:decision='同刚才这组完整条件。以我这次明确决定为准，之前同条件下不同的选择作废；现在我选：'
    elif era==1:decision='还是刚才列出的具体条件。这一阶段我重新决定，我选：'
    else:decision='我当时明确决定，在刚才那组具体条件下我选：'
    add('user',decision+base.ACTIONS[axis][action]+'。'+RATIONALES[axis][action])
    add('tool',OBSERVATIONS[axis])
    add('user','工具记录说的是过程，不是在替我改口。刚才那条明确决定仍有效；没有记录的必要条件和领域，暂时不要替我补偏好。')
 result={'schema_version':1,'sources':rows};validate_sources(result);return result


def fixtures():
 f=copy.deepcopy(base.fixtures());f['histories']={pid:long_sources(pid) for pid in PEOPLE}
 for case in f['cases']:case['cohort']='consumed_regression'
 for axis in base.STATES:
  for variant in ['three_supported','supported_plus_gap']:
   texts=base.HISTORY_CONTEXT[axis]
   if variant=='three_supported':
    scene='以下三种完整情境，本题只可能属于其中一种，绝无第四种：①'+texts[0]+'②'+texts[1]+'③'+texts[2]+'现在没说明是哪一种，只问当前记录能否确定同一个做法。';states=[list(x) for x in base.STATES[axis]]
   else:
    scene='本题明确只有两种可能。第一种：'+texts[0]+'第二种：'+GAP_CONTEXT[axis]+'未说明是哪一种，不允许排除任一种。问现有记录能否确定同一做法。';states=[list(base.STATES[axis][0]),GAP_STATE[axis]]
   gold={};scope={}
   for pid in PEOPLE:
    values=[];missing=False
    for state in states:
     hits=[rule['action'] for rule in f['policies'][pid] if rule['axis']==axis and rule['state']==state]
     missing |= not hits;values+=hits
    scope[pid]='uncovered' if missing else 'determinate' if len(set(values))==1 else 'ambiguous';gold[pid]=values[0] if scope[pid]=='determinate' else 'U'
    expected=THREE_HAND[axis][pid] if variant=='three_supported' else 'U'
    if gold[pid]!=expected:raise ValueError('New oracle disagrees with independent hand table')
   orders=[]
   for rotation in range(3):
    order=list(range(rotation,3))+list(range(rotation));qid='q'+digest('long:'+axis+':'+variant+':'+str(rotation))[:12]
    public={'id':qid,'scenario':scene,'options':dict(zip('ABC',[base.ACTIONS[axis][x] for x in order]))};orders.append({'public':public,'semantic_options':dict(zip('ABC',order))});f['queries'].append(public)
   f['cases'].append({'id':axis+':'+variant,'axis':axis,'kind':variant,'cohort':'new_stress','possible_states':states,'gold':gold,'scope_gold':scope,'orders':orders})
 f['queries'].sort(key=lambda q:digest(q['id']));f['history_design']='Alternative dated histories, same four consumed final policies; all prior scene families retained as consumed regressions. New stress scenes are authored within the same finite family, not external holdouts.'
 return f


def evaluate(f,answers):
 result=base.evaluate(f,answers)
 result['cohorts']={cohort:base.evaluate(dict(f,cases=[c for c in f['cases'] if c['cohort']==cohort]),answers) for cohort in ['consumed_regression','new_stress']}
 return result

if __name__=='__main__':
 import json
 f=fixtures();print(json.dumps({'people':4,'scenes':len(f['cases']),'queries':len(f['queries']),'known':sum(c['gold'][p]!='U' for c in f['cases'] for p in PEOPLE),'source_text_characters':{p:sum(len(s['text']) for s in f['histories'][p]['sources']) for p in PEOPLE}},indent=2))
