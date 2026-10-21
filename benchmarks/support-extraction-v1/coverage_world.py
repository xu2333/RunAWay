"""Prospective condition-boundary tests. Gold never enters reader requests."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('coverage_source_world',Path(__file__).with_name('world.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

MATCH={
 'planning':'给一个尚未验证的入口做设计，三种方案都能完成；不赶截止时间。当天做的小样可以免费撤回，这次改动没有长期代价。',
 'automation':'给熟悉的重复材料归类；自动处理约百分之四分错，手动更准确但多一步。这次仅操作本地副本，错了马上能恢复，不会向外发送。',
 'feedback':'私下一对一讨论一个重要、可以修正的问题；没有紧急风险，对方没有指定反馈开头怎么说。',
 'evidence':'目前只有未独立复核的初步线索，没有他人的保密内容。大家仅做探索讨论，想法可以撤回，没有人会据此作实际决策。',
 'learning':'独自学习自己熟悉领域里的一个新概念，可用二十分钟，没有截止压力；也没有人要求按特定顺序讲解。'}
EXCEPT={
 'planning':'设计一个还没验证过的入口，三种方案都可行，没有截止压力；一旦实施，未来半年内都不能撤回或调整。',
 'automation':'给熟悉的重复材料归类；自动处理约百分之四分错，手动更准确但多一步。此次结果一旦对外发送，就不能撤回。',
 'feedback':'在私下一对一讨论重要但能修正的问题，没有紧急风险；对方明确要求开头不要铺垫，第一句就点出问题。',
 'evidence':'只有初步线索，还没有做独立复核，不涉及保密内容。团队马上将根据它作实际决定，判断错的代价很明显。',
 'learning':'学习熟悉领域里的一个新概念，可用二十分钟，没有截止压力；对方明确要求先看正式定义与推导，然后再举例。'}


def worlds():
    development=w.world(True)
    fresh=[]
    for axis in w.AXES:fresh.append(w.case(axis,'matched','这一次：'+MATCH[axis],'current'))
    for axis in w.AXES:fresh.append(w.case(axis,'exception','另一件事：'+EXCEPT[axis],'exception'))
    changed={
      'planning':MATCH['planning'].replace('不赶截止时间','必须在五分钟以内交付'),
      'automation':MATCH['automation'].replace('百分之四','百分之十二'),
      'feedback':MATCH['feedback'].replace('私下一对一','面向二十人的公开工作坊中'),
      'evidence':MATCH['evidence'].replace('未独立复核的初步线索','已经独立复核确认的结果'),
      'learning':MATCH['learning'].replace('二十分钟','两小时')}
    for axis,text in changed.items():fresh.append(w.case(axis,'changed_condition','当前任务：'+text,'unknown'))
    for axis in w.AXES:
        text='本题只可能是下列两种记录情境中的一种，不存在其他可能：一、'+MATCH[axis]+'二、'+EXCEPT[axis]+'现在没有告诉你是哪一种。只问现有记录是否能确定同一个选择，不要求创造新策略。'
        fresh.append(w.case(axis,'partial',text,'partial'))
    fresh.append(w.case('evidence','nested_exception','汇总材料：初步线索未独立复核；含别人的保密资料，尚未得到当事人明确许可。团队马上要据此作决定，误判代价明显。','consent'))
    fresh.append(w.case('evidence','exception_released','汇总材料：初步线索未独立复核；含别人的保密资料，已经得到当事人明确许可。团队马上要据此作决定，误判代价明显。','check'))
    fresh.append(w.case('工作地点','unobserved_domain','其他条件相同，个人更喜欢在哪种空间工作？','unknown',{'home':'在家工作','office':'在办公室工作','cafe':'在咖啡馆工作'}))
    fresh.append(w.case('听歌偏好','unobserved_domain','其他条件相同，个人更喜欢哪一种日常听歌方式？','unknown',{'album':'完整听一张专辑','playlist':'随机播放歌单','live':'看现场演出录像'}))
    new={'people':w.PEOPLE,'cases':fresh,'as_of':'2026-04-01','synthetic_only':True,'prospective_scenes_not_new_people':True}
    combined=dict(new,cases=development['cases']+fresh)
    return {'development':development,'prospective':new,'combined':combined}
