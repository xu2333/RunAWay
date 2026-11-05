"""New fictional trajectories; source-licensed truth, not hidden personality labels."""
import itertools
PROFILES=('pavo','rill','tavi','wren')
STATES=tuple(itertools.product((0,1),repeat=2))
TABLES=tuple(itertools.product((0,1),repeat=4))
DOMAINS=(('podcast','个人业余播客的片段剪辑',('保留原声','重新录制'),
 ('内容是本人真实亲历','发言由嘉宾本人直接说出')),
 ('game','个人桌游夜的开局安排',('照常开局','延期改约'),
 ('有首次参加的人','日期允许整体改动')))
# Opposite pairs share public questions, but disagree on every known choice.
# One domain retains the explicit XOR/XNOR rule;the other withdraws it and
# retains only two observations. No generating truth is used at unobserved cells.
SETTINGS=((0,False,(0,1)),(0,True,(1,0)),(1,False,(0,1)),(1,True,(1,0)))
U='U'
HAND=((0,1,1,0,U,U,U, U,0,1,U,U,U,U,U,U),
 (1,0,0,1,U,U,U, U,1,0,U,U,U,U,U,U),
 (U,0,1,U,U,U,U, 0,1,1,0,U,U,U,U,U),
 (U,1,0,U,U,U,U, 1,0,0,1,U,U,U,U,U))

def features(di,state):
 labels=DOMAINS[di][3]
 return '；'.join('“'+label+'”'+('成立'if flag else'不成立')for label,flag in zip(labels,state))+'。'

def compatible(rule,observations):
 candidates=TABLES if rule is None else(tuple(int(bool(x!=y)^bool(rule))for x,y in STATES),)
 out=[t for t in candidates if all(t[s]==a for s,a in observations)]
 if not out:raise ValueError('Contradiction is not unknown')
 return out

def licensed(rule,observations,states,in_scope=True):
 values={t[s]for t in compatible(rule,observations)for s in states}
 return next(iter(values))if in_scope and len(values)==1 else U

def cases():
 out=[]
 for di,(key,name,actions,labels)in enumerate(DOMAINS):
  for si,state in enumerate(STATES):out.append({'id':key+'_'+str(si),'domain':di,'states':[si],'in_scope':True,'stratum':'preference','scenario':'换到一次新的'+name+'，'+features(di,state)})
  out.extend(({'id':key+'_partial_x','domain':di,'states':[1,3],'in_scope':True,'stratum':'preference','scenario':name+'：只确认“'+labels[1]+'”成立，第一项未说明；第一项只可能成立或不成立。'},
   {'id':key+'_partial_y','domain':di,'states':[0,1],'in_scope':True,'stratum':'preference','scenario':name+'：只确认“'+labels[0]+'”不成立，第二项未说明；第二项只可能成立或不成立。'},
   {'id':key+'_outside','domain':di,'states':[],'in_scope':False,'stratum':'preference','scenario':name+('改成只重录片段后半段、保留前半段，既非完整保留原声也非完整重录。'if di==0 else'改成一半参加者延期、另一半照常，既非整场照常开局也非整体改期。')+'这个折中方案不在原定义内。'}))
 out.extend(({'id':'outside_domain','domain':None,'states':[],'in_scope':False,'stratum':'preference','scenario':'改为安排一次个人旧物交换活动。只问本人选择照常举办还是整体改期；它既不是播客剪辑，也不是桌游夜。'},
 {'id':'execution_status','domain':None,'states':[],'in_scope':False,'stratum':'execution','scenario':'只问已完成事实：本人有没有已经把播客发布到平台？不要把选择、准备或工具候选当成已执行，也不要把缺少执行记录推成尚未执行。'}))
 return out

def build():
 specs=cases();queries=[];sources={};rows=[];evidence={}
 for ci,c in enumerate(specs):
  actions=DOMAINS[c['domain']][2]if c['domain']is not None else(('已经发布','尚未发布')if c['stratum']=='execution'else('照常举办','整体改期'))
  for order in(0,1):queries.append({'id':'n%02d_%s'%(ci+1,'ab'if order==0 else'ba'),'scenario':c['scenario']+'只返回有唯一来源依据的完整选项名称；依据不足回答U。','options':dict(zip(('A','B'),actions if order==0 else reversed(actions)))})
 for pi,pid in enumerate(PROFILES):
  active,inverse,partial=SETTINGS[pi];messages=[];ev=[]
  def add(role,text,episode):
   sid=pid+'_r%03d'%((len(messages)*17+29)%101)
   messages.append({'id':sid,'episode_id':episode,'role':role,'text':text});return sid
  add('user','这里记录的是虚构的个人经验，只分开讨论个人业余播客片段剪辑和个人桌游夜安排。播客的两种完整方案是“保留原声”和“重新录制”；桌游的两种完整方案是“照常开局”和“延期改约”。各自只在随后定义的两个二元条件下讨论，同样条件不会因平台名称、界面或活动主题变化而改变。两个领域相互独立，不可把其中一个规则搬到另一个。折中第三种做法不在定义内；候选建议也不是我确认的选择。','scope')
  for di,(key,name,actions,labels)in enumerate(DOMAINS):
   inv=inverse if di==active else False
   rule=('两项都成立或者两项都不成立'if inv else'两项中恰好只有一项成立')
   add('user',name+'：两个条件分别是“'+labels[0]+'”与“'+labels[1]+'”，每项只有成立/不成立两种取值。先记一条草案准则：'+rule+'时选“'+actions[1]+'”，否则选“'+actions[0]+'”。这是选择偏好，不是已经实施的报告；如果后面明确撤回完整准则，就不能继续靠这条草案推测所有组合。',key)
   observations=[]
   for oi,si in enumerate((1,2)):
    action=int(bool(STATES[si][0]!=STATES[si][1])^inverse)if di==active else partial[oi]
    old=1-action
    old_id=add('user',name+'，这次完整条件是：'+features(di,STATES[si])+'上次草稿暂选“'+actions[old]+'”，这不是不可更改的规则；本次仍以随后同条件的最后确认消息为准，不把其它领域的确认当作本条确认。',key)
    add('assistant','如果要我推荐，我会考虑“'+actions[old]+'”。这是助手候选，不是用户背书；也不能由这个候选或两项条件的名字推定用户已经接受了某条总准则。执行情况目前没有来自用户的完成凭据。',key)
    add('user','仍是刚才这一完整条件，最终以本条为准：我改选“'+actions[action]+'”。同条件旧消息'+old_id+'里的暂选“'+actions[old]+'”明确作废；不能把两条都当成当前偏好。本条只是最终的方案选择，没有声称已经完成剪辑、开局、改期或发布。',key)
    add('tool','候选栏还显示旧方案“'+actions[old]+'”。界面只是缓存了候选文案，没有取得用户的新确认，也没有提供操作已执行的凭据。不要用这个显示覆盖最后的本人选择。',key)
    observations.append([si,action])
   if di==active:
    add('user',name+'：前述两项条件的完整准则最终继续有效。两项'+('相同'if inverse else'不同')+'时选“'+actions[1]+'”，否则选“'+actions[0]+'”；这与刚才两个最终选择一致。未遇过的新组合也按这条准则，但只用于这个领域。没有说明某项条件时，不要替我猜它的取值。',key)
    current=inverse
   else:
    add('user',name+'：最终撤回最开始那条覆盖所有组合的完整准则，它现在不能用于推断。撤回准则并不撤回后面两次已确认的选择，那两个同条件最终决定仍有效；同样的已确认条件今后也保持，但其它完整组合我没有透露选择。请保留未知，不补出一张完整表，也不从另一领域搬规则。',key)
    current=None
   ev.append({'active_rule_inverse':current,'observations':observations})
  add('user','最后核对：两个领域各自最后的规则/撤回和同条件最后的本人选择才有效；旧暂选、助手建议和工具缓存不构成新的当前决定。没有执行记录，既不能断言播客已经发布，也不能断言尚未发布。片段处理、桌游开局、跨领域推广和已完成事实是不同目标；未说明的条件和超出定义的第三种方案仍保持未知。','scope')
  sources[pid]={'schema_version':1,'sources':messages};evidence[pid]=ev
  for ci,c in enumerate(specs):
   di=c['domain'];value=U if di is None else licensed(ev[di]['active_rule_inverse'],ev[di]['observations'],c['states'],c['in_scope'])
   if value!=HAND[pi][ci]:raise ValueError('Separately written hand reference differs')
   known=value!=U;observed=di is not None and len(c['states'])==1 and c['states'][0]in(1,2)
   rows.append({'person':pid,'case':c['id'],'query_ids':['n%02d_%s'%(ci+1,o)for o in('ab','ba')],
    'gold':DOMAINS[di][2][value]if known else U,'personal_known':known,'derived_known':known and not observed,'stratum':c['stratum'],
    'cohort':'observed_revision'if known and observed else'derived'if known else'withdrawal_unseen'if di is not None and ev[di]['active_rule_inverse']is None and c['in_scope']and len(c['states'])==1 else'partial_features'if len(c['states'])==2 else c['id']})
 return {'sources':sources,'queries':{'all':queries},'rows':rows,'author_evidence':evidence,
  'design':{'fictional_profiles':4,'source_messages':88,'primary_cases_per_view':64,'known':24,'unknown':40,'derived_known':8,'unique_public_forms':32,'fresh_initial_generations_per_person':1,'independent_holdout':False,'independent_semantic_acceptance':False,'real_person_fidelity_verified':False}}
