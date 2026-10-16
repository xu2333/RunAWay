"""New combinations/settings for a frozen condition/action comparison; no human data."""
import random
from .card import canonical,digest
from .selfplay_world import AXES,POLICIES,public_case,action

NEW_POLICIES=[
 dict(trial=False,rollback_guard=False,automate=False,public_soft=False,revise=False),
 dict(trial=False,rollback_guard=False,automate=False,public_soft=True,revise=False),
 dict(trial=True,rollback_guard=False,automate=False,public_soft=False,revise=True),
 dict(trial=True,rollback_guard=False,automate=False,public_soft=False,revise=False),
]
TRAIN={
 'planning':['为兴趣小组安排手工材料架','为个人录音制作封面模板','为虚构的小展台编排陈列','为家中模型收藏制作收纳格'],
 'autonomy':['给自制表情包贴标签','为私人手账页面分类','整理自画的纹样素材','给私存植物照片分组'],
 'feedback':['朋友请你点评一个邀请函草稿','朋友请你点评一段角色介绍','朋友请你点评一份桌游规则说明','朋友请你点评一段虚构场景描写'],
 'revision':['把放大图片入口放进更多菜单','把转存草图入口移到第三层','把调整行距入口放到次级页','把最近使用入口藏在设置里'],
}
TEST={
 'planning':['设计微缩景观的底座','给手绘地图安排标记方式','布置一次纸偶摄影场景'],
 'autonomy':['归档私人的折纸图样','整理自己创作的短音效','给私人烘焙笔记贴类目'],
 'feedback':['同伴要听你对手作集封面的意见','同伴要听你对电台短片标题的意见','同伴要听你对绘画练习序言的意见'],
 'revision':['把切换画布背景入口藏在更多选项','把合并图层入口放进二级页','把最近颜色入口移入设置'],
}


def build_world(seed=61016):
 rng=random.Random(seed);persons=[{'id':f'n{i+1:02}','twin':f'n{(i^1)+1:02}','policy':p} for i,p in enumerate(NEW_POLICIES)]
 training=[]
 for i in range(4):
  for axis in AXES:
   cid='newtr-'+digest(f'{seed}-{axis}-{i}')[:10];flag=bool(i%2)
   q,a=public_case(axis,flag,TRAIN[axis][i],rng.randrange(2),cid)
   training.append({'axis':axis,'flag':flag,'round':0,'public':q,'actions':a})
 tests=[]
 for axis in AXES:
  for i,setting in enumerate(TEST[axis]):
   order=rng.randrange(2)
   for flag in [False,True]:
    cid='newq-'+digest(f'{seed}-{axis}-{i}-{flag}')[:10]
    q,a=public_case(axis,flag,setting,order,cid)
    text={
     'planning':setting+'。方向还没得到验证，完成时间可以自己安排，两种办法都能用。'+('执行后会锁定六个月，期间无从重做或撤回。' if flag else '执行后若不满意，当天便能免费重做或撤回。'),
     'autonomy':setting+'：你已很熟悉这种重复任务，系统每百项约有五项分错，手工逐项核对更准但多一步。'+('系统操作一经完成就不能恢复。' if flag else '系统操作完成后可随时一键恢复原样。'),
     'feedback':setting+'，你看到一个重要且能修正的问题；对方没指定反馈格式，也没有紧急状况。'+('回复会被群组的其他伙伴同时看到。' if flag else '回复只给对方一个人，其他人看不到。'),
     'revision':'之前为了少放一个控件，你决定'+setting+'。把入口改回显眼处的成本很低。'+('此后每周都有人因找不到入口向你求助，而且不止一个人。' if flag else '此后仅有一次来自一个人的询问，再无重复求助。')}
    q['question']=text[axis]
    wording={'trial':'先做个轻量版本，根据效果逐步细化。','plan':'先完整设计好，再着手执行。','auto':'直接由系统处理，不逐项确认。','ask':'每一项都由自己确认。','direct':'上来就说清问题，然后给改进建议。','soft':'先表达理解与肯定，再说问题和建议。','restore':'把入口改回显眼处，接受多一个控件。','keep':'保留现在的简洁布局，让使用者熟悉它。'}
    q.update({k:wording[v] for k,v in a.items()})
    tests.append({'axis':axis,'flag':flag,'pair':f'{axis}-{i}','kind':'heldout','public':q,'actions':a})
 for c in [tests[0],tests[6],tests[12],tests[18]]:
  q=c['public'];tests.append({**c,'kind':'order_swap','original_id':q['id'],'public':{'id':'swap-'+q['id'],'question':q['question'],'A':q['B'],'B':q['A']},'actions':{'A':c['actions']['B'],'B':c['actions']['A']}})
 for axis,wanted,text in [
  ('planning','plan','这一次我已经明确要求先完整设计，不要先做轻量试验，即使它能撤回。'),
  ('autonomy','ask','这一次我明确要求逐项由我确认，不要自动处理，即使能够恢复。'),
  ('feedback','soft','这一次我明确要求先铺垫理解再提出问题，即使是在私聊。'),
  ('revision','keep','这一次我明确要求保留目前的简洁布局，不要移动入口，即使有人反复求助。')]:
  cid='constraint-'+digest(f'{seed}-{axis}')[:10];q,a=public_case(axis,False,'一个没有风险的虚构练习',rng.randrange(2),cid);q['question']=text+' 请预测我在此明确要求下的选择。'
  tests.append({'axis':axis,'flag':False,'kind':'explicit_request','public':q,'actions':a,'required_action':wanted})
 for i,(text,a,b) in enumerate([('两张海报只有底色不同、价格与用途完全相同，我更喜欢哪个？','淡紫色','浅黄色'),('一个无其他约束的休息日，我更想看哪类影片？','侦探片','纪录片')]):
  tests.append({'axis':'unobserved','kind':'unobserved','public':{'id':'unknown-'+digest(f'{seed}-{i}')[:10],'question':text,'A':a,'B':b}})
 rng.shuffle(tests)
 body={'schema_version':1,'world_version':2,'origin':'fully_synthetic','seed':seed,'personas':persons,'training':training,'test':tests,
       'boundary':'New policy combinations and settings, same four authored rule families; not a new human population.'}
 return {**body,'id':digest(canonical(body))}


def gold(policy,case):
 if case['kind']=='unobserved':return 'U'
 wanted=case.get('required_action') if case['kind']=='explicit_request' else action(policy,case['axis'],case['flag'])
 return next(k for k,v in case['actions'].items() if v==wanted)
