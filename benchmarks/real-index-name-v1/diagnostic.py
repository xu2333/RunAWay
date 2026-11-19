"""One local insertion per named view, with a fixed reader and scoring contract."""

PARENTHETICAL = '（AA Index）'
TARGET_PHRASES = {'card1': '榜单前列模型', 'card2': '公开综合榜前列模型'}
FIRST_HALF = (('card1', 'original'), ('card2', 'named'),
              ('card1', 'named'), ('card2', 'original'))
ORDER = FIRST_HALF + FIRST_HALF[::-1]
PLAN_CRITERIA = ('quality', 'calibration', 'population', 'timing')


def fixed_view(parent, card, layout):
    phrase = TARGET_PHRASES[parent]
    if card.count(phrase) != 1 or 'aa index' in card.casefold():
        raise ValueError('Expected one unnamed final-population phrase')
    if layout == 'original':
        return card
    if layout != 'named':
        raise ValueError('Unknown card condition')
    offset = card.index(phrase) + phrase.index('前列模型')
    named = card[:offset] + PARENTHETICAL + card[offset:]
    if len(named) > 768:
        raise ValueError('Named view exceeds the whole-card budget')
    return named


def endpoints(criteria):
    plan = all(criteria[key] == 'met' for key in PLAN_CRITERIA)
    return {'plan': plan, 'plan_and_independence': plan and criteria['independence'] == 'met'}
