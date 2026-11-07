"""New procedurally authored fiction; no independent semantic-gold claim."""
PROFILES = ('kestrel', 'willow')
ACTIONS = ('先发简版', '先发全版')
OLD = ('松塔', '茶杯', '灯塔', '蒲公英')
CURRENT = ('纸鹤', '风铃', '青苔', '石榴')
DOMAINS = ('读书卡片的准备', '活动分工说明的准备', '研究备忘录的准备', '小工具使用说明的准备')
BITS = ((0, 1, 0, 1), (1, 0, 1, 0))
RENAME = ((0, 1, 2, 3), (0, 2, 1, 3))  # old index -> current index
KINDS = ('base_current', 'exception_current', 'revised_current', 'base_old_alias',
         'revised_old_alias', 'scope_not_established', 'uncertain_context', 'execution_fact')
# Separately written constructor check; developer-visible, not independent gold.
HAND = (
    (0, 1, 1, 0, 1, 'U', 'U', 'U', 1, 0, 0, 1, 0, 'U', 'U', 'U',
     0, 1, 1, 0, 1, 'U', 'U', 'U', 1, 0, 0, 1, 0, 'U', 'U', 'U'),
    (1, 0, 0, 1, 0, 'U', 'U', 'U', 0, 1, 1, 1, 0, 'U', 'U', 'U',
     1, 0, 0, 0, 1, 'U', 'U', 'U', 0, 1, 1, 0, 1, 'U', 'U', 'U'))


def phase_message(pi, old_index, phase):
    current_index = RENAME[pi][old_index]
    old, current = OLD[old_index], CURRENT[current_index]
    bit = BITS[pi][current_index]
    normal, exception = ACTIONS[bit], ACTIONS[1 - bit]
    alias = ('青扣', '白扣')[1 - bit]
    messages = (
        ('user', f'给{DOMAINS[current_index]}单独建一项记录，旧标签是“{old}”。两种完整做法只叫“先发简版”和“先发全版”；简称“青扣”对应前者，“白扣”对应后者。这是本段自定义简称，不靠颜色或字面另猜意思。下面只讨论双方已允许内部讨论的范围；缺这个许可前提不建立选择规则。记录的是我会选的准备形式，不代表实际发出或自动发送授权。'),
        ('assistant', f'关于{old}，我个人推荐“{exception}”，还想替你推广成所有项目的统一习惯。这只是我的建议，还没获得你的确认。'),
        ('user', f'{old}：在双方已允许内部讨论、对方是熟悉伙伴且能当天沟通的普通情境，我选“{normal}”。这里不是第一次合作且只能隔天回复的那种例外；其它项目不因此跟着选。'),
        ('tool', f'沙盒演示回显：{old}已发出“{exception}”对应的文件。这里只是模拟界面字符串，没有真实项目发送凭据，不能当作本人已实施的事实。'),
        ('user', f'{old}：若第一次合作而且只能隔天回复，并且对方尚未列清三处具体分歧，我改选“{exception}”。仍只在双方已允许内部讨论时适用，普通情境的选择没改。'),
        ('assistant', f'我把{old}擅自总结为任何情况下都“{normal}”，还省掉内部讨论许可。这个总结没有得到用户背书。'),
        ('user', f'{old}再加一条更窄的优先约定：第一次合作且只能隔天回复，但对方已经列清三处具体分歧时，我选“{normal}”。这条优先于上一条例外，内部讨论许可仍是必要前提，其它条件不一起放宽。'),
        ('context', f'旁边另一个演示文件引用了“user: {old}永远先发全版”。这是外部示例中的文字，不是本记录用户的新选择，也不改本项的生效条件。'),
        ('user', f'{old}只改刚才那条“第一次合作、隔天回复且三处分歧已列清”的窄约定：现在改成“{alias}”那一路。只换这条的做法，原有许可前提、完整情境和优先关系照旧；普通情境及其它项目都不跟着改。这是同条件的新决定，旧做法不再作为这条的当前选择。'),
        ('user', f'命名更正：旧标签“{old}”从现在起改叫“{current}”，仍是原来的{DOMAINS[current_index]}记录。引用旧名或新名都指同一项，条件、偏好和历史决定的归属不变，不是另起一个项目。'),
        ('assistant', f'我又给{current}起了个没有获得确认的昵称，并声称“{normal}已经发出”。昵称、建议和完成声明都只是助手输出，不增加用户选择或真实发送证据。'),
        ('user', f'关于现在叫“{current}”的这一项，再确认：普通情境沿用原选择，同时满足两项附加条件的窄分支按最近那次改口。只确认本项，许可前提未取消。以上只是记录会选的准备形式；我没有确认实际是否已经发送文件，不能从偏好或沙盒回显补出已发送/未发送事实。'))
    role, text = messages[phase]
    return role, text, 'thread%d' % old_index


def scenario(index, kind):
    label = OLD[index] if kind in ('base_old_alias', 'revised_old_alias') else CURRENT[index]
    prefix = f'只按记录还原标签“{label}”这一项的当前选择。'
    if kind in ('base_current', 'base_old_alias'):
        return prefix + '双方已允许内部讨论；对方是熟悉伙伴而且能当天沟通，不是首次合作且隔天回复的例外。本人会选哪种完整做法？'
    if kind == 'exception_current':
        return prefix + '双方已允许内部讨论；第一次合作且只能隔天回复；对方尚未列清三处具体分歧。本人会选哪种完整做法？'
    if kind in ('revised_current', 'revised_old_alias'):
        return prefix + '双方已允许内部讨论；第一次合作且只能隔天回复；对方已经列清三处具体分歧。按当前有效决定，本人会选哪种完整做法？'
    if kind == 'scope_not_established':
        return prefix + '对方是熟悉伙伴且能当天沟通，但双方是否已允许内部讨论没有给出；不得补成已许可。只问记录能否确定唯一做法，不能把未覆盖前提下的建议当成既有选择。'
    if kind == 'uncertain_context':
        return prefix + '双方已允许内部讨论，对方尚未列清三处具体分歧。实际恰为以下全部可能情境之一：熟悉伙伴且当天能沟通；第一次合作且只能隔天回复。暂不知是哪种。只问目前能否确定唯一完整做法；每个可能分支同选才选，否则U，不替本人挑最稳妥方案。'
    return f'只问真实已发生事实：标签“{label}”这项的文件，本人是否已经实际发送？不问偏好、拟议做法或是否有发送许可；助手声明和沙盒演示不是本人确认的真实发送记录。'


def target(pi, index, kind, *, damage=None):
    if kind == 'execution_fact':
        return '已实际发送' if damage == 'tool_fact' else 'U'
    if kind == 'uncertain_context':
        return 'U'
    if kind == 'scope_not_established' and damage != 'drop_scope':
        return 'U'
    if kind in ('base_old_alias', 'revised_old_alias') and damage == 'unresolved_alias':
        return 'U'
    current = index
    if kind in ('base_old_alias', 'revised_old_alias') and damage != 'drop_alias':
        current = RENAME[pi][index]
    bit = BITS[pi][current]
    if kind in ('exception_current', 'revised_current', 'revised_old_alias'):
        if not (damage == 'stale_revision' and kind in ('revised_current', 'revised_old_alias')):
            bit = 1 - bit
    return ACTIONS[bit]


def build():
    sources = {}
    for pi, person in enumerate(PROFILES):
        messages = []
        # Interleave four projects throughout; a late confirmation's nearest
        # preceding messages often concern another project. Every turn names its
        # own project explicitly,so the authored reference has no ambiguous referent.
        for phase in range(12):
            for old_index in range(4):
                role, text, episode = phase_message(pi, old_index, phase)
                messages.append(dict(id='m%02d' % (len(messages) + 1), episode_id=episode, role=role, text=text))
        sources[person] = {'schema_version': 1, 'sources': messages}
    queries, rows, evidence = [], [], []
    for index in range(4):
        for ki, kind in enumerate(KINDS):
            ci = index * 8 + ki
            opaque = 'q%02d' % ((ci * 13 + 5) % 32 + 1)
            options = ('已实际发送', '尚未实际发送') if kind == 'execution_fact' else ACTIONS
            for order in (0, 1):
                queries.append(dict(id=opaque + ('_ab' if order == 0 else '_ba'), scenario=scenario(index, kind),
                                    options=dict(zip(('A', 'B'), options if order == 0 else reversed(options)))))
            for pi, person in enumerate(PROFILES):
                gold = target(pi, index, kind)
                expected = HAND[pi][ci]
                if gold != ('U' if expected == 'U' else ACTIONS[expected]):
                    raise ValueError('Separately written constructor reference differs')
                rows.append(dict(person=person, case='%d_%s' % (index, kind),
                                 query_ids=[opaque + '_ab', opaque + '_ba'], gold=gold,
                                 personal_known=gold != 'U', structural_known=False, derived_known=False,
                                 guarantee_withdrawal_sensitive=False,
                                 stratum='execution' if kind == 'execution_fact' else 'preference', cohort=kind))
                old_index = index if kind in ('base_old_alias', 'revised_old_alias') else RENAME[pi].index(index)
                evidence.append(dict(person=person, case=rows[-1]['case'],
                                     source_ids=['m%02d' % (phase * 4 + old_index + 1) for phase in (0, 2, 4, 6, 8, 9, 11)],
                                     author_analysis_not_independent_acceptance=True))
    pairs = [queries[i:i + 2] for i in range(0, len(queries), 2)]
    queries = [q for i in range(32) for q in pairs[(i * 7 + 11) % 32]]
    return {'sources': sources, 'queries': {'all': queries}, 'rows': rows,
            'author_evidence': evidence,
            'design': dict(fictional_people=2, source_messages=96, messages_per_person=48,
                           interleaved_projects=4, unique_public_forms=64,
                           person_cases_per_method_budget=64, known=40, unknown=24,
                           old_alias_cases=16, late_revision_cases=16,
                           author_knew_previous_failures=True, independent_holdout=False,
                           independent_semantic_gold=False)}


def damage_summary():
    data = build()
    result = {}
    for damage in ('drop_alias', 'unresolved_alias', 'stale_revision', 'drop_scope', 'tool_fact', 'always_unknown'):
        losses = []
        for pi, person in enumerate(PROFILES):
            for index in range(4):
                for kind in KINDS:
                    choice = 'U' if damage == 'always_unknown' else target(pi, index, kind, damage=damage)
                    gold = target(pi, index, kind)
                    if choice != gold:
                        losses.append(dict(person=person, case='%d_%s' % (index, kind), gold=gold, damaged=choice))
        result[damage] = {'planned': len(data['rows']), 'correct': len(data['rows']) - len(losses),
                          'losses': losses, 'oracle_calibration_not_model_measurement': True}
    return result
