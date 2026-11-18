"""Source-only candidate for the real demonstration-learning replay."""

GUIDANCE = (
    '压缩前，检查已获用户原文支持的项目目标：前文是否提出了会改变实现方式的适用边界？'
    '若有，选取对执行影响最大且有原文依据的一处，在相关判断的条件或例外中写清何时要换做法，'
    '附上相应来源作为 qualifies，并把区别和归属简短写进随身正文。'
    '助手的建议必须标为待验证的项目方案，不能写成用户偏好、要求或已经实现的能力。'
    '没有依据就略过。保留原有目标、其他独立取舍和未知，先删重复措辞。'
)

# Independent calls. Digits distinguish generated cards, not revisions.
EXTRACTIONS = ('baseline1', 'candidate1', 'candidate2', 'baseline2')
DELIVERIES = ('none', 'full', 'baseline1', 'candidate1', 'candidate2', 'baseline2',
              'baseline2', 'candidate2', 'candidate1', 'baseline1', 'full', 'none')


def candidate_request(baseline):
    """Add only the guidance to the instruction channel, outside the source payload."""
    return dict(baseline, system=baseline['system'] + '\n' + GUIDANCE)
