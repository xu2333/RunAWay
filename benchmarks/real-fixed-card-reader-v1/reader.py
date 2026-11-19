"""Reader-only comparison. Each condition uses an unchanged archived card."""

GUIDANCE = (
    '交付前对照当前请求和随身材料，找出会改变本次答案的目标、取舍与限制。'
    '对每个相关项，检查正文里哪一个具体设计决定体现了它，'
    '并确认这个决定的适用范围与材料一致。如果只有笼统表态，补足对做法的实际影响。'
    '区分已确认的要求、别人提出的方案和未知；省略与当前任务无关的条目。'
    '直接交付答案，不输出核对过程。'
)

# Each method and card appear once per half, in reversed order in the second half.
ORDER = (
    ('575', 'old'), ('572', 'new'), ('575', 'new'), ('572', 'old'),
    ('572', 'old'), ('575', 'new'), ('572', 'new'), ('575', 'old'),
)


def revised_request(original):
    return dict(original, system=original['system'] + '\n' + GUIDANCE)
