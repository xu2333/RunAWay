"""Reader-only intervention on two archived, automatically generated cards."""

GUIDANCE = (
    '把随身材料中的限制放到它实际约束的决策步骤上。'
    '如果一条限制会排除某个看似可行的做法，在交付中说明什么情况下会遇到这个选择、'
    '你会采取或排除什么行动。沿用材料里的适用范围和提出者身份；缺少依据时保留未知。'
)

FIRST_HALF = (('candidate1', 'prior'), ('candidate2', 'revised'),
              ('candidate1', 'revised'), ('candidate2', 'prior'))
ORDER = FIRST_HALF + FIRST_HALF[::-1]


def revised_request(prior):
    return dict(prior, system=prior['system'] + '\n' + GUIDANCE)
