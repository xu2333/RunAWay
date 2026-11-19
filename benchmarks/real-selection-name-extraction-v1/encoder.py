"""Compare two source-only extraction requests with the same portable reader."""

GUIDANCE = (
    '回看有来源依据的取舍：若一处专名决定哪些对象符合条件，把它换成泛称会改变范围或让人无法判断，'
    '就在详细主张和最终随身正文中保留原名，并写明它限定的对象和用途。'
    '只保留理解决定所需的名称；原文未指定名称时保留未知。'
)

EXTRACTIONS = ('original1', 'candidate1', 'candidate2', 'original2')
FIRST_READS = ('candidate2', 'original1', 'original2', 'candidate1')
DELIVERIES = FIRST_READS + FIRST_READS[::-1]


def candidate_request(original):
    return dict(original, system=original['system'] + '\n' + GUIDANCE)


def endpoints(criteria):
    required = ('quality', 'population', 'calibration', 'timing', 'independence')
    core = all(criteria[key] == 'met' for key in required)
    return {'core': core, 'core_and_ranking': core and criteria['ranking'] == 'met'}
