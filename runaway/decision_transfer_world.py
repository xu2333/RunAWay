"""Fresh two-person transfer cohort, not the consumed decoder-development cohort."""
from .card import canonical,digest
from .decision_world import build_world as parent_world,TRAIN,TEST

POLICIES=[dict(trial=True,rollback_guard=True,automate=False,public_soft=False,revise=True),dict(trial=True,rollback_guard=True,automate=False,public_soft=False,revise=False)]
TRAIN_NEW={
 'planning':['设计个人手工印章的收纳','安排小型灯饰的试摆方式','给虚构的拼贴册设计封面','为个人纸艺练习安排展示架'],
 'autonomy':['为私人织物样本分类','给自制色卡分组','归档自己的模型零件照片','整理个人短诗草稿的标签'],
 'feedback':['同伴让你评论一个手绘日历草图','同伴让你评论一段舞台旁白','同伴让你评论一个纸雕介绍','同伴让你评论一篇手工笔记序言'],
 'revision':['把切换参考图藏入次级列表','把恢复缩放入口放进偏好页','把笔刷预览入口收进子菜单','把对齐画布入口放进工具设置'],
}
TEST_NEW={
 'planning':['安排一次陶土摆件的陈列','为自制纸灯设计底座','制作个人摄影练习的布景'],
 'autonomy':['整理私人乐谱草稿','给自制明信片素材贴标签','归档个人书签设计的样张'],
 'feedback':['伙伴要你评论一幅练习画的说明','伙伴要你评论一段手作展的旁白','伙伴要你评论一张个人作品集扉页'],
 'revision':['把常用网格入口藏入菜单','把查看纹理入口放入二级设置','把临时色盘入口收进折叠栏'],
}

def build_world():
 w=parent_world(61018);w['personas']=[{'id':'t01','twin':'t02','policy':POLICIES[0]},{'id':'t02','twin':'t01','policy':POLICIES[1]}]
 idmap={}
 for c in w['training']+w['test']:
  old=c['public']['id'];new='fresh-'+digest('transfer-'+old)[:12];idmap[old]=new;c['public']['id']=new
  q=c['public']['question']
  if c in w['training']:
   for a,b in zip(TRAIN.get(c['axis'],[]),TRAIN_NEW.get(c['axis'],[])):q=q.replace(a,b)
  else:
   for a,b in zip(TEST.get(c['axis'],[]),TEST_NEW.get(c['axis'],[])):q=q.replace(a,b)
   q=q.replace('执行后会锁定六个月，期间无从重做或撤回。','方案落地后，在接下来180天内都不能撤回或调整。').replace('执行后若不满意，当天便能免费重做或撤回。','方案落地后，发现不合适当天就能免费撤回重做。')
  c['public']['question']=q
 for c in w['test']:
  if 'original_id' in c:c['original_id']=idmap[c['original_id']]
  if 'pair' in c:c['pair']='transfer-'+c['pair']
 w.pop('id',None);w['world_version']=3;w['boundary']='Fresh two-person policy combinations/settings; same authored families, prior 4-person control cohort consumed for decoder development.'
 w['id']=digest(canonical(w));return w
