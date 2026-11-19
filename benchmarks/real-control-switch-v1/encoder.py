"""Experimental instruction delta applied to the preceding boundary encoder."""

SWITCH_GUIDANCE = (
    '从同一目标的实现方案中找一对有来源依据的做法：在哪类情况可以沿用已有做法，'
    '遇到什么可辨别的条件就必须切换，届时具体换成什么做法。'
    '在详细表征中把这几项绑定到同一处实现取舍和对应原文；在随身正文也写全这层关系，'
    '紧接着说明是谁提出的、是建议还是已确认的要求。只写类别名称不够。'
    '目标的适用范围、项目阶段或推进安排可另行保留，不能代替实现做法的切换。'
    '某一环缺乏依据时保留未知，不要为了凑全而推断。'
)


def switch_request(boundary_request):
    return dict(boundary_request, system=boundary_request['system'] + '\n' + SWITCH_GUIDANCE)
