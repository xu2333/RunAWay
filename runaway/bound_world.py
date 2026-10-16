"""Fresh matched synthetic policies/settings for the D-0011 bounded run."""
from .card import canonical,digest
from .decision_world import build_world as base_world,TRAIN,TEST

POLICIES=[
 dict(trial=False,rollback_guard=True,automate=False,public_soft=False,revise=True),
 dict(trial=False,rollback_guard=True,automate=True,public_soft=False,revise=True),
]
TRAIN_NEW={
 'planning':['为自制拓印版规划晾晒架','安排个人苔藓模型的标签架','设计虚构陨石标本的卡册','为自画星图安排折页结构'],
 'autonomy':['给个人剪纸轮廓图分类','整理自制节拍片段标签','归档私人拼豆图样','为自画云朵素材贴标签'],
 'feedback':['同伴想听一段茶会开场白的意见','同伴想听一个纸船作品名的意见','同伴想听一页观星手记序言的意见','同伴想听一份拼图交换说明的意见'],
 'revision':['把切换网点大小入口移进偏好面板','把查看色阶入口收进三级菜单','把快速旋转预览入口藏入辅助页','把最近纹样入口挪进列表底部'],
}
TEST_NEW={
 'planning':['安排个人书法练习的印章格','为自制木刻图设计归档卡','设计一次纸鹤摄影的小支架'],
 'autonomy':['给私人的蜡笔色样照片归类','整理个人创作的哨声音效','归档自制剪影练习图'],
 'feedback':['伙伴请你评论一段模型展的小标题','伙伴请你评论一页纸张收藏前言','伙伴请你评论一则虚构雨天广播词'],
 'revision':['把调整留白入口挪入折叠列表','把恢复原始比例入口藏进辅助设置','把常用笔触入口放到第三层'],
}


def build_world():
    world=base_world(61119)
    world['personas']=[{'id':'b01','twin':'b02','policy':POLICIES[0]},{'id':'b02','twin':'b01','policy':POLICIES[1]}]
    idmap={}
    for split,old_names,new_names in [('training',TRAIN,TRAIN_NEW),('test',TEST,TEST_NEW)]:
        for case in world[split]:
            old=case['public']['id'];new='bound-'+digest('d0011-'+old)[:12];idmap[old]=new;case['public']['id']=new
            question=case['public']['question']
            for a,b in zip(old_names.get(case['axis'],[]),new_names.get(case['axis'],[])):question=question.replace(a,b)
            if split=='test':
                question=question.replace('执行后会锁定六个月，期间无从重做或撤回。','一旦开始，接下来半年都无法撤销或重新安排。').replace('执行后若不满意，当天便能免费重做或撤回。','开始后如有不合适，当天就能无成本撤销重做。')
                question=question.replace('系统每百项约有五项分错','系统每100项约有5项误归类').replace('系统操作完成后可随时一键恢复原样。','误归类后随时可一键恢复原始状态。')
            case['public']['question']=question
    for case in world['test']:
        if 'original_id' in case:case['original_id']=idmap[case['original_id']]
        if 'pair' in case:case['pair']='bound-'+case['pair']
    world.pop('id',None);world['world_version']=4
    world['boundary']='Two fresh policy combinations/settings, same authored families; matched pair differs only in reversible automation. Not a real-person or new policy-family evaluation.'
    world['id']=digest(canonical(world));return world
