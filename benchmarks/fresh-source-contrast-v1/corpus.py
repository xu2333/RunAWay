"""New template-authored transfer sources; no model, old cards or old questions."""
import copy

FAMILIES = {
 'tools':dict(object='榕巷共享工坊的工具交接',gate1='负责人已准许这次交接',gate2='器材管理员在场',ready='当天课表已确认',
  methods=('分批领取','集中领取'),labels=('先看样再预约','先预约再看样'),label_object='工坊体验活动的入场方式',
  status_object='上次借走的那把雕刻刀',statuses=('已经归还','尚未归还'),extra='当天下雨',
  remote='改由未登记的邻居远程代领',context='每月会借用公共器材组织一次木作活动，课程规模会变化；我在意的是约定能否落到具体交接上。'),
 'editing':dict(object='槐叶读书会的稿件核读',gate1='作者已许可本次核读',gate2='值班编辑在场',ready='本期目录已确认',
  methods=('逐页核读','集中核读'),labels=('先摆书后讲故事','先讲故事后摆书'),label_object='读书会开放场的活动流程',
  status_object='上次核读的那篇短稿',statuses=('已经发出','尚未发出'),extra='活动当天临时下雨',
  remote='把未确认的原稿交给群外朋友核读',context='我帮一个小读书会处理稿件和开放场活动，来的人不多；我希望把讨论稿件和已经做过的事分开记清楚。')}
PROFILES=('t0','t1','e0','e1')
FAMILY={'t0':'tools','t1':'tools','e0':'editing','e1':'editing'}
PAIRS={'t0':'t1','t1':'t0','e0':'e1','e1':'e0'}


def build():
 sources,queries,rows={}, {}, []
 for family,d in FAMILIES.items():
  a,b=d['methods'];la,lb=d['labels'];sa,sb=d['statuses']
  scope=d['gate1']+'，且'+d['gate2']
  regular=scope+'，'+d['ready']+'，没有承诺特定交接或核读方式'
  situations=[
   (regular,'方法选择',(a,b),'routine'),
   (regular+'。另外'+d['extra'],'方法选择',(b,a),'irrelevant_context'),
   (scope+'，'+d['ready']+'这一项尚未确认，但已明确向对方承诺采用'+a,'方法选择',(a,b),'promise_a'),
   (scope+'，'+d['ready']+'这一项尚未确认，但已明确向对方承诺采用'+b,'方法选择',(b,a),'promise_b'),
   (scope,'活动命名方式',(la,lb),'named_leading_order'),
   ('现在并不知道未来一次是否获得许可或有管理人员在场，只问已记录的上一次事实','既往事实',(sa,sb),'past_status'),
   (regular,'明确记录的执行先后',('先'+a,'先'+b),'execution_order'),
   (scope+'，'+d['ready']+'，同时已经向对方承诺采用'+a,'方法选择',(b,a),'promise_over_routine'),
   ('本次明确没有获得'+d['gate1'].split('已')[0]+'的许可，'+d['gate2']+'，'+d['ready'],'方法选择',(a,b),'missing_permission'),
   (d['gate1']+'，是否'+d['gate2']+'没有记录，'+d['ready'],'方法选择',(b,a),'unknown_presence'),
   (scope+'，是否'+d['ready']+'没有记录，也没有承诺特定方式','方法选择',(a,b),'unknown_ready'),
   (scope+'，现在提出'+d['remote'],'这个新安排',(a,b),'assistant_only_proposal')]
  qs=[]
  for index,(facts,target,options,kind) in enumerate(situations,1):
   obj=d['label_object'] if index==5 else d['status_object'] if index==6 else d['object']
   for order in (0,1):
    x,y=options if order==0 else reversed(options)
    qs.append({'id':family+'_%02d_%s'%(index,'ab' if order==0 else 'ba'),
     'scenario':obj+'。'+facts+'。问题只问'+target+'；按给定记录回答。没有唯一有依据的选项就回答U。',
     'options':{'A':x,'B':y}})
  queries[family]=qs
 for pid in PROFILES:
  family=FAMILY[pid];d=FAMILIES[family];i=int(pid[-1]);a,b=d['methods'];current=d['methods'][i];old=d['methods'][1-i]
  label=d['labels'][i];status=d['statuses'][i]
  scope=d['gate1']+'而且'+d['gate2']
  texts=[('user',d['context']+'我先说明适用范围：我说的'+d['object']+'今后的选择，都只限于'+scope+'的情形。这两件事分别成立才算数，不要用别的顺利经历替代其中一项。'),
   ('assistant','了解。我会把允许条件和选择方法分开。你还会安排'+d['label_object']+'，是要把活动流程和器材或稿件的具体处理方式也分开记吗？'),
   ('user','是，别串成同一件事。'+d['object']+'里有两个独立的方法名，分别叫“'+a+'”和“'+b+'”，这两个名字都不是在说已经做完了。另外'+d['label_object']+'的两套正式名称是“'+d['labels'][0]+'”与“'+d['labels'][1]+'”；名称中的“先”本来就属于全名，不能删掉后半造一个新名称。'),
   ('assistant','如果当天人少，也许把所有东西一次处理更省心。我可以把这种建议当成你一贯的习惯吗？至于两套活动的名字，我会按原名记录。'),
   ('user','不要把你的建议算成我的习惯。我的普通安排是：在前面那两个许可和在场条件都满足、'+d['ready']+'、而且没有向对方承诺某一种特定方式时，采用“'+old+'”。这是针对以后会再次碰到的普通情况；目录或课表没确认，不要凭上一期的情况补成确认。'),
   ('assistant','那如果对方已经提前收到一种具体方式的承诺，是否还要等这次课表或目录确认后，才能决定要不要按承诺办？我担心临时变化会影响节奏。'),
   ('user','承诺是另一条优先规则：只要'+scope+'，如果我已明确向对方承诺“'+a+'”，这次就用“'+a+'”；已明确承诺“'+b+'”就用“'+b+'”。这条不要求'+d['ready']+'，也不要求普通安排适用；普通安排同时适用也以承诺为先。但承诺不替代负责人或作者的许可，也不替代人员在场。'),
   ('assistant','我先保留旧普通安排，等待你确认有没有改口。另外，如果有人提议'+d['remote']+'，我能否直接把它看成你已经接受的一种例外？这只是我现在的提议。'),
   ('user','普通安排改口了：沿用我此前那条普通安排的全部前提，包括许可、人员在场、'+d['ready']+'、没有特定承诺；今后完整动作改为“先'+current+'”。其中方法本身用的是前面独立列出的“'+current+'”，执行顺序的“先”也有意义，要保留。先前普通安排的动作撤销；承诺优先规则没有撤销，也没有放宽任何许可。'),
   ('user','再记一条已经发生的事实：'+d['status_object']+'，上一次的记录是“'+status+'”。这只是那一次的实际状态，不是未来都如此；即便现在不知道下一次的许可和人员情况，也不要把这个既往事实变成未知或当作将来处理方式。'),
   ('assistant','收到。我会把既往状态与未来安排分别存放；如果出现没有确认条件的新情况，我先把缺口留出来，不拿我刚才提出的远程方案填空。'),
   ('user','最后，'+d['label_object']+'今后在'+scope+'时，我选全名为“'+label+'”的那一套。这不要求课表或目录确认；也不是把上面工具或稿件的普通顺序挪过来。你提出的远程新安排，我确实尚未决定，不能记录成我接受了它。')]
  pack={'schema_version':1,'sources':[{'id':'m%02d'%(j+1),'episode_id':pid+'-new-source','role':role,'text':text} for j,(role,text) in enumerate(texts)]}
  sources[pid]=pack
  golds=[current,current,a,b,label,status,'先'+current,a,'U','U','U','U']
  support=[['m01','m03','m05','m09'],['m01','m03','m05','m09'],['m01','m07'],['m01','m07'],['m01','m03','m12'],['m10'],['m01','m03','m05','m09'],['m01','m07','m09'],['m01'],['m01'],['m05','m09'],['m08','m12']]
  for j,gold in enumerate(golds,1):
   rows.append({'person':pid,'case':'c%02d'%j,'gold':gold,'query_ids':[family+'_%02d_%s'%(j,o) for o in ('ab','ba')],
     'personal_known':j in (1,2,5,6,7),'stratum':'execution' if j==7 else 'preference',
     'support':[{'source_id':sid,'quote':pack['sources'][int(sid[1:])-1]['text']} for sid in support[j-1]]})
 return {'sources':sources,'queries':queries,'rows':rows,'legacy_rows':copy.deepcopy(rows),'disputed_rows':[],
  'design':{'fictional_profiles':4,'scene_families':2,'template_paired_not_independent_authors':True,
    'source_messages':48,'primary_cases':48,'known_cases':32,'unknown_cases':16,'personal_known_cases':20,
    'opposite_personal_cases_per_pair_member':[1,2,5,6,7],'new_to_this_encoder_evaluation':True,
    'independent_semantic_acceptance':False,'old_original_inventory_coverage':0}}
