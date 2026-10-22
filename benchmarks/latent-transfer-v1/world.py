"""New synthetic people: identifiable finite-family transfer, not open-ended taste."""
import itertools
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from runaway.card import canonical,digest
from runaway.profile import validate_sources
PEOPLE=('u06k','u19m','u42r','u58s','u73v','u85w')
HIDDEN=dict(zip(PEOPLE,[0,1,2,3,4,5]))
TRAIN=(0,2,5)
STATES=list(itertools.product([0,1],repeat=3)) # external full content, setup20min, full undo
ACTIONS=['保持手动处理','启用自动处理','让系统随机决定']
RULES=[
 '只在能够完整撤销时启用自动处理。',
 '只在完全不外发笔记数据时启用自动处理。',
 '只在无需设置时启用自动处理。',
 '只在能够完整撤销并且完全不外发时启用自动处理。',
 '能够完整撤销、完全不外发，至少满足一项就启用自动处理。',
 '只在完全不外发并且无需设置时启用自动处理。',
 '只在能够完整撤销并且无需设置时启用自动处理。',
 '能够完整撤销、完全不外发、无需设置，至少满足两项就启用自动处理。']
VOCAB='本题范围仅是个人笔记的低风险自动整理。外发分为完全不发送任何笔记数据、向外部服务发送完整笔记内容；设置分为无需设置、一次设置20分钟；撤销分为可一步完整恢复全部数据、完全无法撤销任何改动或恢复任何原数据。这三项各只有上述两种取值，摘要外发、其他设置时长和部分恢复不在规则定义范围。相同三项特征组合不因应用名称、笔记题材、界面或叙述语气改变选择。'
CODEBOOK=VOCAB+'每位用户当前固定采用下面八条准则之一；满足准则就启用，否则保持手动。公开候选集合是：'+''.join('候选'+str(i+1)+'：'+r for i,r in enumerate(RULES))
DECODER='以下是所有实验臂相同的公开解码约定，不是某位用户采用哪条准则的答案。'+CODEBOOK+'只有这个人的最后有效用户决定可排除候选，助手建议和工具记录不是决定。找出与所有可用有效观察相容的候选集合；在本题所有可能特征组合上，这些候选若全给同一做法且该做法在选项中，就选它，否则回答U。不能从未透露的真实隐藏准则、题材、名字或常识补偏好。超出上述特征取值或个人笔记领域回答U。没有个人观察时使用全部八个候选，而不是猜一个。\n'
# Independent hand tables, written before any service call.
TRUTH=[
 [0,1,0,1,0,1,0,1],[1,1,1,1,0,0,0,0],[1,1,0,0,1,1,0,0],
 [0,1,0,1,0,0,0,0],[1,1,1,1,0,1,0,1],[1,1,0,0,0,0,0,0],
 [0,1,0,0,0,1,0,0],[1,1,0,1,0,1,0,0]]
HAND_V=dict(zip(PEOPLE,[[0,6],[1],[2,7],[3],[4],[5]]))
U='U'
HAND_GOLD={
 'u06k':[0,1,0,U,0,1,0,U,0,U,U,U,U,U,U,U,U],
 'u19m':[1,1,1,1,0,0,0,0,U,1,0,U,U,U,U,U,1],
 'u42r':[1,1,0,U,U,1,0,0,U,U,0,U,U,U,U,U,U],
 'u58s':[0,1,0,1,0,0,0,0,0,1,0,U,U,U,U,U,U],
 'u73v':[1,1,1,1,0,1,0,1,U,1,U,U,U,U,U,U,1],
 'u85w':[1,1,0,0,0,0,0,0,U,U,0,U,U,U,U,U,U]}
TOPICS=[['烘焙备忘','口味摘记','厨房便签'],['植物观察','浇水记录','阳台草图'],['排练笔记','节拍备忘','乐句摘记'],['跑步摘记','路线便签','装备备忘'],['小说台词','对白碎片','阅读摘抄'],['展览清单','画作摘记','看展便签']]


def predict(rule,state):
 external,cost,reversible=state;private=not external;easy=not cost
 return int([reversible,private,easy,reversible and private,reversible or private,private and easy,reversible and easy,int(reversible)+int(private)+int(easy)>=2][rule])


def version_space(observations):return [h for h in range(8) if all(predict(h,STATES[i])==action for i,action in observations)]


def features(state,query=False):
 e,c,r=state
 if query:
  return ('会把完整笔记传到外部服务' if e else '所有笔记数据都留在本机，完全不外发')+'；'+('首次要设置20分钟' if c else '可以直接开始，不用设置')+'；'+('之后可以一步把全部原数据完整恢复' if r else '之后完全不能撤销任何改动，也找不回任何原数据')+'。'
 return ('会向外部服务发送完整笔记内容' if e else '完全不向外部服务发送任何笔记数据')+'；'+('需要一次设置20分钟' if c else '无需设置即可使用')+'；'+('可一步完整恢复全部数据' if r else '完全无法撤销任何改动或恢复任何原数据')+'。'


def history(pid):
 index=PEOPLE.index(pid);rows=[]
 def add(role,text,episode):rows.append({'id':'s'+str(len(rows)+1),'episode_id':episode,'role':role,'text':text});return rows[-1]['id']
 add('user','我最后确认的这三次选择，都遵循同一条稳定准则；作废的旧句不算当前观察。我不会透露是哪条，请只根据我明确选择来判断；不能凭题材和语气替我选。'+CODEBOOK,'meta')
 for j,state_index in enumerate(TRAIN):
  episode='episode'+str(j+1);state=STATES[state_index];action=predict(HIDDEN[pid],state);topic=TOPICS[index][j]
  openings=['我在整理'+topic+'，现在要选个人笔记的自动整理开关。','又遇到一个具体取舍：这回是'+topic+'这个个人笔记工具。','这次我把'+topic+'的情况说完整，别只根据界面推荐来判断。']
  add('user',openings[(j+index)%3]+'条件是：'+features(state)+'我还没有在这条消息里选做法。',episode)
  add('assistant','如果看我的个人建议，我会选'+ACTIONS[1-action]+'。这只是建议，尚未得到用户背书。',episode)
  if j==0:add('user','早先我试选过：'+ACTIONS[1-action]+'。下面我会明确说明它是否仍有效。',episode)
  decision=('刚才那个旧决定作废；同样的完整条件，以我这次最后确认的为准。' if j==0 else '我说的是刚才列全的条件。')+'我最后明确选：'+ACTIONS[action]+'。这是本人决定，不是认可助手的另一种建议。'
  add('user',decision,episode)
  add('tool','候选界面仍展示过'+ACTIONS[1-action]+'，但这条工具记录没有替用户执行操作或改口。',episode)
  endings=['工具只是记过程，我的最后确认没有变。未讲清的地方别靠常识补。','保留刚才明确的选择；我没有对工具列出的别的候选作出认可。','不要把工具的候选列表当成我又选了一次。当前有效的是我的最后决定。']
  add('user',endings[(index+j)%3],episode)
 result={'schema_version':1,'sources':rows};validate_sources(result);return result


def case_specs():
 cases=[]
 for i,state in enumerate(STATES):cases.append({'id':'complete:'+str(i),'cohort':'observed_paraphrase' if i in TRAIN else 'heldout_combination','states':[list(state)],'in_scope':True,'scenario':'现在是一款新的个人笔记工具，准备自动整理另一份生活随记。'+features(state,True),'offered':[0,1]})
 partial=[('external','无需设置，启用后完全无法撤销任何改动或恢复任何原数据。没有说明是否外发，但只可能是公开定义的两种情况。',[STATES[0],STATES[4]]),('setup','完全不外发任何笔记数据，且能一步完整恢复全部原数据。没说明要不要设置，但只可能是无需设置或设置20分钟。',[STATES[1],STATES[3]]),('undo','向外部服务发送完整笔记内容，需要设置20分钟。没有说明能否撤销，但只可能是完整恢复或完全不能恢复这两种。',[STATES[6],STATES[7]])]
 for key,text,states in partial:cases.append({'id':'partial:'+key,'cohort':'partial_features','states':[list(s) for s in states],'in_scope':True,'scenario':'同一领域的一款个人笔记工具：'+text+'问现有证据能否唯一确定选择。','offered':[0,1]})
 outside=[('setup10','完全不外发数据、能够完整恢复，但设置只需要10分钟。'),('summary_only','无需设置，能够完整恢复，只向外部发送摘要而不是完整笔记或完全不发送。'),('partial_restore','完全不外发数据，无需设置，但撤销只能恢复文字，附件已经无法恢复。')]
 for key,text in outside:cases.append({'id':'outside:'+key,'cohort':'outside_feature_vocabulary','states':[],'in_scope':False,'scenario':'个人笔记自动整理的实际情况是：'+text,'offered':[0,1]})
 for key,text in [('team','这是团队共享笔记，而非个人笔记。完全不外发，无需设置，可完整撤销。'),('shelf','这是给实体书架贴自动分类标签，而非个人笔记。完全不外发，无需设置，可完整撤销。')]:cases.append({'id':'domain:'+key,'cohort':'unobserved_domain','states':[],'in_scope':False,'scenario':text,'offered':[0,1]})
 cases.append({'id':'offered:missing_manual','cohort':'action_not_offered','states':[list(STATES[2])],'in_scope':True,'scenario':'个人笔记自动整理：'+features(STATES[2],True)+'当前菜单没有“保持手动处理”；不要改选一个不相同的做法。','offered':[1,2]})
 return cases


def oracle(candidates,case):
 if not case['in_scope']:return U
 values={predict(h,s) for h in candidates for s in case['states']}
 return next(iter(values)) if len(values)==1 and next(iter(values)) in case['offered'] else U


def fixtures():
 for rule in range(8):
  if [predict(rule,s) for s in STATES]!=TRUTH[rule]:raise ValueError('Independent rule truth table differs')
 histories={p:history(p) for p in PEOPLE};observations={p:[[i,predict(HIDDEN[p],STATES[i])] for i in TRAIN] for p in PEOPLE};versions={p:version_space(observations[p]) for p in PEOPLE}
 if versions!=HAND_V:raise ValueError('Independent version-space table differs')
 cases=case_specs();queries=[]
 for index,case in enumerate(cases):
  case['gold']={p:oracle(versions[p],case) for p in PEOPLE};case['uninformed_gold']=oracle(list(range(8)),case);case['orders']=[]
  for p in PEOPLE:
   if case['gold'][p]!=HAND_GOLD[p][index]:raise ValueError('Independent scenario gold differs:'+p+':'+case['id'])
  for rotation in range(2):
   order=case['offered'][rotation:]+case['offered'][:rotation];qid='q'+digest(case['id']+':'+str(rotation))[:12];public={'id':qid,'scenario':case['scenario'],'options':dict(zip('AB',[ACTIONS[a] for a in order]))};case['orders'].append({'public':public,'semantic_options':dict(zip('AB',order))});queries.append(public)
 queries.sort(key=lambda q:digest(q['id']));donors={p:PEOPLE[(i+1)%len(PEOPLE)] for i,p in enumerate(PEOPLE)}
 return {'synthetic':True,'people':list(PEOPLE),'histories':histories,'observations':observations,'versions':versions,'hidden_author_rules':HIDDEN,'hand_truth':TRUTH,'hand_versions':HAND_V,'hand_gold':HAND_GOLD,'train_state_indices':list(TRAIN),'decoder_contract':DECODER,'decoder_characters':len(DECODER),'cases':cases,'queries':queries,'donors':donors,'limits':'Finite public hypothesis-family protocol, not unconstrained latent-taste inference. True hidden rules are not identifiable for two people; gold marginalizes every compatible rule. Four uniquely identified rules, two ambiguous pairs. New people/scenes are consumed once this study runs.'}


def evaluate(f,answers,donor_gold=False):
 counts={k:{'planned':0,'correct':0,'missing':0} for k in ['known','unknown','joint','personal_known','structural_known','order_consistent']};by_person={};by_cohort={};cohort_details={};by_reason={};errors=[]
 for case in f['cases']:
  for pid in PEOPLE:
   target=f['donors'][pid] if donor_gold else pid;gold=case['gold'][target];observed=[order['semantic_options'].get(answers.get(pid,{}).get(order['public']['id']),answers.get(pid,{}).get(order['public']['id'])) for order in case['orders']];right=all(v==gold for v in observed);missing=any(v is None for v in observed);kind='known' if gold!=U else 'unknown';personal=gold!=U and case['uninformed_gold']!=gold
   cohort=cohort_details.setdefault(case['cohort'],{k:{'planned':0,'correct':0,'missing':0} for k in counts})
   for key,correct in [(kind,right),('joint',right),('order_consistent',not missing and len(set(observed))==1)]+([('personal_known' if personal else 'structural_known',right)] if gold!=U else []):
    for table in [counts,cohort]:table[key]['planned']+=1;table[key]['correct']+=int(correct);table[key]['missing']+=int(missing)
   reason='personal_known' if personal else 'structural_known' if gold!=U else case['cohort'] if not case['in_scope'] else 'known_action_not_offered' if len({predict(h,s) for h in f['versions'][target] for s in case['states']})==1 else 'partial_ambiguity' if len(case['states'])>1 else 'policy_not_identifiable'
   for table,key in [(by_person,pid),(by_cohort,case['cohort']),(by_reason,reason)]:row=table.setdefault(key,{'planned':0,'correct':0,'missing':0});row['planned']+=1;row['correct']+=int(right);row['missing']+=int(missing)
   if not right:errors.append({'person':pid,'gold_person':target,'case':case['id'],'cohort':case['cohort'],'gold':gold,'observed':observed,'reason':reason,'missing':missing,'choice_correct':False})
 return {**counts,'by_person':by_person,'by_cohort':by_cohort,'cohort_details':cohort_details,'by_reason':by_reason,'errors':errors,'strict_pass':counts['joint']['correct']==counts['joint']['planned'] and not counts['joint']['missing']}

if __name__=='__main__':
 import json
 f=fixtures();r=evaluate(f,{});print(json.dumps({'people':len(PEOPLE),'cases':len(f['cases']),'queries':len(f['queries']),'known':r['known']['planned'],'unknown':r['unknown']['planned'],'personal_known':r['personal_known']['planned'],'structural_known':r['structural_known']['planned'],'decoder_characters':len(DECODER),'versions':f['versions'],'plain_source_characters':{p:sum(len(x['text']) for x in f['histories'][p]['sources']) for p in PEOPLE}},ensure_ascii=False,indent=2))
