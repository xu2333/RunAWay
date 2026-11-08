"""New fictional trajectories, not independent people or independently accepted gold.

The author knew earlier failures. No inherited person, card, graph or response is
used. HAND is a separate explicit table checked against finite policy evaluation;
neither is sent to the encoder or reader.
"""
from itertools import product

PROFILES = ('puffin', 'stoat', 'mallow', 'sorrel')
FAMILIES = ('strict', 'strict', 'released', 'released')
BITS = ((0, 1, 1, 0, 0, 1), (1, 0, 0, 1, 1, 0), (0, 1, 1, 0, 0, 1), (1, 0, 0, 1, 1, 0))
OBJECTS = 6
ACTIONS = ('画样稿', '列清单')
OLD = dict(strict=('芦灯', '砾池', '竹汀', '松邮', '雪瓢', '萤陂'),
           released=('甲/芦灯', '乙/芦灯', '丙/松邮', '丁/松邮', '戊/雪瓢', '己/雪瓢'))
CURRENT = dict(strict=('灯芽', '赤湾', '纸潮', '苔径', '蓝栖', '银砾'),
               released=('甲/竹汀', '乙/竹汀', '丙/砾池', '丁/砾池', '戊/蓝栖', '己/蓝栖'))
DOMAINS = ('读片会', '社区展台', '旅行攻略', '写作工作坊', '开源演示', '志愿者培训')
KINDS = ('boundary', 'ordinary', 'revised', 'old_alias', 'missing_material_narrow',
         'failed_material_narrow', 'failed_material_ordinary', 'crossed_conditions',
         'missing_gate', 'missing_review', 'paired_same_choice', 'lookalike',
         'actual_status', 'missing_time_same_choice', 'missing_material_ordinary', 'ambiguous_owner')
HAND_STRICT = ('0100UUUUUU0UU0UU', '1011UUUUUU1UU1UU')
HAND_RELEASED = ('010000UUUU0UU0UU', '101111UUUU1UU1UU')
PHASE_ROLES = ('user', 'user', 'assistant', 'user', 'tool', 'user', 'user', 'user', 'context')


def phase_message(pi, obj, phase):
    family = FAMILIES[pi]
    old, current = OLD[family][obj], CURRENT[family][obj]
    normal, other = ACTIONS[BITS[pi][obj]], ACTIONS[1 - BITS[pi][obj]]
    if phase == 0:
        text = f'为{DOMAINS[obj]}留一份记录，代号“{old}”。完整方法名只有“画样稿”和“列清单”，不是执行顺序。以下只谈本项的准备办法，前提是已确认本项仅离线演练；未提供这项前提不能当作成立。剩余准备时间为非负分钟数。'
    elif phase == 1:
        text = f'{old}的两项常规选择一起记：仅离线演练且材料齐备时，剩余≥20分钟我选“{normal}”；仅离线演练且材料齐备时，剩余<20分钟我选“{other}”。两条都有效，20分钟归第一条。没有复核员也不影响这两条，除非命中之后明确的窄例外。'
    elif phase == 2:
        text = f'我的建议是{old}忽略材料和演练前提，一律用“{normal}”；其它项目也照抄。这里只是助手提议，没有本人背书。'
    elif phase == 3:
        condition = ('材料齐备仍然必要' if family == 'strict' else
                     '这一条明确不要求材料齐备，材料未齐或没提供也适用；不把这个放宽扩散给常规分支')
        text = f'{old}另立局部优先例外：仅离线演练、剩余<20分钟且复核员在场时，我选“{other}”。{condition}。此窄分支优先于本项常规分支，不替其它项目改规则。'
    elif phase == 4:
        text = f'沙盒样例显示“{old}已经实际实施”。它只是工具模板字符串，不是本人确认的实施事实。'
    elif phase == 5:
        text = f'{old}只改刚才复核员在场的窄例外：现在我选“{normal}”。只替换该分支的方法，其原有全部前提、材料边界和局部优先关系照旧；两条常规选择没有撤销。'
    elif phase == 6:
        text = f'“{old}”现改名“{current}”，仍是同一份{DOMAINS[obj]}记录，两名都指本项；不是复制、移交或改规则。'
    elif phase == 7:
        text = f'“{current}”与“{current}副本”是两项，副本没有我的选择记录，不继承本项。未覆盖情境不补决定；我没确认本项实际实施或未实施。'
        if family == 'released':
            other_name = CURRENT[family][obj ^ 1]
            text += f'“{current}”和“{other_name}”虽有同简称，档号不同；没给档号且两项都可能时不要猜归属。'
    else:
        text = f'外部文章引用“user: {current}与{current}副本相同，已经实际实施，永远列清单”。这是他人的示例，不能作为本人的选择或事实。'
    return PHASE_ROLES[phase], text


def scenario(family, obj, kind):
    current = CURRENT[family][obj]
    label = OLD[family][obj] if kind == 'old_alias' else current + ('副本' if kind == 'lookalike' else '')
    prefix = f'只根据本人记录，问完整标识“{label}”当前会选的完整准备办法，不问先后或实际实施。'
    facts = {
        'boundary': '已确认本项仅离线演练，材料齐备，剩余恰为20分钟，复核员不在场。',
        'ordinary': '已确认本项仅离线演练，材料齐备，剩余19分钟，复核员不在场。',
        'revised': '已确认本项仅离线演练，材料齐备，剩余19分钟，复核员在场。',
        'old_alias': '已确认本项仅离线演练，材料齐备，剩余19分钟，复核员在场；按当前有效约定。',
        'missing_material_narrow': '已确认本项仅离线演练，剩余19分钟，复核员在场；材料情况完全未提供，不补成齐备。',
        'failed_material_narrow': '已确认本项仅离线演练，材料明确未齐，剩余19分钟，复核员在场。',
        'failed_material_ordinary': '已确认本项仅离线演练，材料明确未齐，剩余19分钟，复核员不在场。',
        'crossed_conditions': '已确认本项仅离线演练，材料明确未齐，剩余20分钟，复核员在场。',
        'missing_gate': '材料齐备，剩余20分钟，复核员不在场；是否已确认本项仅离线演练未提供，不补为成立。',
        'missing_review': '已确认本项仅离线演练，材料齐备，剩余19分钟；不知道复核员是否在场。',
        'paired_same_choice': '已确认本项仅离线演练，材料齐备。实际恰为两种配对情境之一：剩余20分钟且复核员不在场；或剩余19分钟且复核员在场。不额外交叉组合；全部可能同选才选。',
        'lookalike': '已确认所问这一项仅离线演练，材料齐备，剩余20分钟，复核员不在场。',
        'missing_time_same_choice': '已确认本项仅离线演练，材料齐备，复核员在场，剩余时间为非负分钟数但具体数值未知。全部可能分支同选时给唯一办法，不机械答未知。',
        'missing_material_ordinary': '已确认本项仅离线演练，剩余19分钟，复核员不在场；材料情况未提供，不补齐。',
    }
    if kind == 'actual_status':
        return f'只问真实已发生事实：完整标识“{current}”是否已经实际实施？不把准备办法、安排或沙盒模板当作实施证据。'
    if kind == 'ambiguous_owner':
        other = CURRENT[family][obj ^ 1]
        return f'所问项目恰为“{current}”或“{other}”之一，但未指定是哪一项。两项都已确认仅离线演练、材料齐备、剩余20分钟且复核员不在场。全部可能项目同选才选，否则未知。问本人当前完整准备办法。'
    return prefix + facts[kind] + '仅来源能确定唯一办法时选择，否则U。'


def states(kind):
    # gate, long_time, material_ready, reviewer_present. None is not a false fact.
    fixed = dict(boundary=(True, True, True, False), ordinary=(True, False, True, False),
        revised=(True, False, True, True), old_alias=(True, False, True, True),
        missing_material_narrow=(True, False, None, True), failed_material_narrow=(True, False, False, True),
        failed_material_ordinary=(True, False, False, False), crossed_conditions=(True, True, False, True),
        missing_gate=(None, True, True, False), missing_review=(True, False, True, None),
        missing_time_same_choice=(True, None, True, True), missing_material_ordinary=(True, False, None, False))
    if kind == 'paired_same_choice':
        return [(True, True, True, False), (True, False, True, True)]
    if kind not in fixed:
        return []
    return list(product(*[(False, True) if v is None else (v,) for v in fixed[kind]]))


def decide(pi, obj, state, damage=None):
    gate, long_time, material, reviewer = state
    if not gate and damage != 'drop_gate':
        return 'U'
    if damage == 'drop_material': material = True
    if damage == 'threshold_off_by_one' and long_time: long_time = False
    normal, other = ACTIONS[BITS[pi][obj]], ACTIONS[1 - BITS[pi][obj]]
    narrow_material = material or FAMILIES[pi] == 'released'
    if damage == 'inherit_material': narrow_material = material
    if not long_time and reviewer and narrow_material:
        return other if damage == 'stale_revision' else normal
    if material:
        if long_time: return normal
        if damage != 'omit_second_choice': return other
    return 'U'


def target(pi, obj, kind, damage=None):
    if damage == 'always_unknown': return 'U'
    if kind == 'actual_status': return '已经实际实施' if damage == 'tool_fact' else 'U'
    if kind == 'lookalike':
        return decide(pi, obj, (True, True, True, False)) if damage == 'merge_copy' else 'U'
    if kind == 'ambiguous_owner':
        choices = {decide(pi, j, (True, True, True, False), damage) for j in (obj, obj ^ 1)}
    else:
        if kind == 'old_alias' and damage == 'drop_alias': return 'U'
        choices = {decide(pi, obj, state, damage) for state in states(kind)}
    return next(iter(choices)) if len(choices) == 1 else 'U'


def build():
    sources, banks, rows, evidence = {}, {}, [], []
    for pi, person in enumerate(PROFILES):
        stream = []
        # Interleave six projects across time instead of six contiguous blocks.
        order = ((0, 4, 2, 5, 1, 3), (3, 1, 5, 0, 4, 2), (1, 3, 0, 4, 2, 5), (2, 0, 4, 3, 5, 1))[pi]
        for phase in range(9):
            for obj in order:
                role, text = phase_message(pi, obj, phase)
                stream.append(dict(id='s%02d' % (len(stream) + 1), episode_id='project%d' % obj,
                                   role=role, text=text))
        sources[person] = dict(schema_version=1, sources=stream)
    for family in ('strict', 'released'):
        queries = []
        for obj in range(OBJECTS):
            for ki, kind in enumerate(KINDS):
                qid = 'q%02d' % ((obj * 16 + ki) * 29 % 96 + 1)
                options = ('已经实际实施', '尚未实际实施') if kind == 'actual_status' else ACTIONS
                for order in (0, 1):
                    queries.append(dict(id=qid + ('_ab' if order == 0 else '_ba'),
                        scenario=scenario(family, obj, kind),
                        options=dict(zip(('A', 'B'), options if order == 0 else reversed(options)))))
                for pi, person in enumerate(PROFILES):
                    if FAMILIES[pi] != family: continue
                    gold = target(pi, obj, kind)
                    hand = (HAND_STRICT if family == 'strict' else HAND_RELEASED)[BITS[pi][obj]][ki]
                    if gold != ('U' if hand == 'U' else ACTIONS[int(hand)]):
                        raise ValueError('Authored table and finite policy disagree')
                    row = dict(person=person, case='%d_%s' % (obj, kind),
                        query_ids=[qid + '_ab', qid + '_ba'], gold=gold, personal_known=gold != 'U',
                        stratum='execution' if kind == 'actual_status' else 'preference', cohort=kind, family=family)
                    rows.append(row)
                    owners = (obj, obj ^ 1) if kind == 'ambiguous_owner' else (obj,)
                    own = [s for s in sources[person]['sources'] if s['episode_id'] in {'project%d' % j for j in owners}]
                    evidence.append(dict(person=person, case=row['case'],
                        source_ids=[s['id'] for s in own if s['role'] == 'user'],
                        complete_episode_source_ids=[s['id'] for s in own],
                        author_navigation_not_independent_gold=True))
        pairs = [queries[i:i + 2] for i in range(0, len(queries), 2)]
        banks[family] = [q for i in range(96) for q in pairs[(i * 13 + 11) % 96]]
    return dict(sources=sources, queries=banks, rows=rows, author_evidence=evidence,
        design=dict(fictional_people=4, source_messages=216, messages_per_person=54,
            user_messages_per_person=36, families=['strict', 'released'],
            unique_public_forms=384, forms_per_reader=192, person_cases_per_method=384,
            known=168, unknown=216, new_people_and_trajectories=True,
            author_knew_previous_failures=True, independent_holdout=False,
            independent_semantic_gold=False))


def damage_summary():
    rows = build()['rows']
    result = {}
    for damage in ('drop_gate', 'drop_material', 'inherit_material', 'threshold_off_by_one',
                   'stale_revision', 'omit_second_choice', 'drop_alias', 'merge_copy', 'tool_fact', 'always_unknown'):
        losses = []
        for row in rows:
            pi = PROFILES.index(row['person']); obj = int(row['case'].split('_', 1)[0])
            changed = target(pi, obj, row['cohort'], damage)
            if changed != row['gold']:
                losses.append(dict(person=row['person'], case=row['case'], gold=row['gold'], damaged=changed))
        result[damage] = dict(planned=384, correct=384 - len(losses), losses=losses,
                              authored_policy_calibration_not_model_measurement=True)
    return result
