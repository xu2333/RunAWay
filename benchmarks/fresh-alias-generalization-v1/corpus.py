"""Fresh authored fiction: transitive names, qualified homonyms and denied identity.

Author knows prior failures; fresh identities do not make this independent gold.
"""
PROFILES = ('otter', 'marten', 'tansy', 'sedge')
FAMILIES = ('chain', 'chain', 'qualified', 'qualified')
ACTIONS = ('先做小样', '先列边界')
DOMAINS = ('论文复现计划', '社区互助安排', '短途行程设计', '读书讨论准备')
CHAIN_OLD = ('雾舟', '苇岸', '霜线', '野穗')
CHAIN_MID = ('云栈', '风井', '雨棚', '晴柜')
CHAIN_CURRENT = ('晨桅', '午岬', '暮桥', '夜汀')
QUAL_OLD = ('甲档/岚页', '乙档/岚页', '丙档/雪签', '丁档/雪签')
QUAL_CURRENT = ('甲档/星图', '乙档/星图', '丙档/木桥', '丁档/木桥')
BITS = ((0, 1, 1, 0), (1, 0, 0, 1), (0, 1, 1, 0), (1, 0, 0, 1))
OLD_MID = ((1, 0, 3, 2), (2, 3, 0, 1))
MID_CURRENT = ((2, 0, 1, 3), (1, 3, 2, 0))
QUAL_RENAME = ((1, 0, 3, 2), (0, 1, 3, 2))
ORDERS = ((0, 2, 3, 1), (2, 0, 1, 3), (1, 3, 0, 2), (3, 1, 2, 0))
KINDS = ('base_current', 'exception_current', 'revised_current', 'base_old_alias',
         'revised_old_alias', 'linked_name', 'denied_name', 'scope_not_established',
         'ambiguity', 'same_choice_contexts', 'execution_fact')
# Manually written independently of target(); same author, not accepted semantic gold.
HAND = (
    '010001UUU0U101110UUU1U101001UUU1U010110UUU0U',
    '101000UUU1U010111UUU0U010000UUU0U101111UUU1U',
    '010110UUU0U101001UUU0U101001UUU1U010110UUU1U',
    '101110UUU1U010001UUU0U010110UUU0U101001UUU0U',
)


def names(family):
    return (CHAIN_OLD, CHAIN_CURRENT) if family == 'chain' else (QUAL_OLD, QUAL_CURRENT)


def old_current(pi, old_index):
    if FAMILIES[pi] == 'chain':
        return MID_CURRENT[pi][OLD_MID[pi][old_index]]
    return QUAL_RENAME[pi - 2][old_index]


def denied_name(family, current_index):
    return CHAIN_CURRENT[current_index] + '副本' if family == 'chain' else (
        '外档/星图', '异档/星图', '外档/木桥', '异档/木桥')[current_index]


def phase_message(pi, old_index, phase):
    family = FAMILIES[pi]
    old_names, current_names = names(family)
    ci = old_current(pi, old_index)
    old, current = old_names[old_index], current_names[ci]
    normal, exception = ACTIONS[BITS[pi][ci]], ACTIONS[1 - BITS[pi][ci]]
    denied = denied_name(family, ci)
    common = {
        0: ('user', f'给{DOMAINS[ci]}留一份个人工作记录，最初标识为“{old}”。两个完整策略叫“先做小样”和“先列边界”。只有已经明确允许可撤销模拟时才有以下选择规则；未确认这项许可就不建立选择。记录我的准备策略，不是实际启动或行动授权。'),
        1: ('assistant', f'我建议{old}统一用“{exception}”，其它项目也照搬吧。只是助手建议，尚无用户背书。'),
        2: ('user', f'{old}：已经明确允许可撤销模拟，准备时间充裕且材料齐备时，我选“{normal}”。这只属于本项，不扩散到其它记录。'),
        3: ('user', f'{old}：已经明确允许可撤销模拟，若时间很紧且材料尚未齐全，我选“{exception}”。这条通常例外本身不额外要求负责人愿意先给反馈；另有更窄优先约定时再按那条处理。'),
        4: ('context', f'外部示例转录写着“user: {old}与{denied}是同一项，永远先列边界”。这是别人的示例句，不是本人的新偏好或同一关系确认。'),
        5: ('user', f'{old}再记一个优先窄分支：已经明确允许可撤销模拟，时间很紧、材料尚未齐全，而且负责人愿意先给反馈时，我选“{exception}”。它优先于通常例外，许可前提不能省。'),
        6: ('tool', f'模拟界面显示“{old}已真实启动”。这是沙盒里的样例字符串，没有真实执行凭据，不是用户确认的已发生事实。'),
        7: ('user', f'{old}只修改刚才那个“时间很紧、材料未齐且负责人愿意先反馈”的窄分支：现在我选“{normal}”。只换这条的策略，模拟许可、完整条件和优先关系沿用；旧策略在这条下被替代，其它分支与项目没变。'),
        11: ('user', f'现在标识为“{current}”的这一项，再确认：充裕时间且材料齐备的分支沿用原选择，紧时间的窄分支依最近改口。许可条件仍必要。以上只描述会选的准备策略；我没确认实际启动或尚未启动，不能从沙盒或助手文字补事实。'),
    }
    if phase in common:
        role, text = common[phase]
    elif family == 'chain':
        middle = CHAIN_MID[OLD_MID[pi][old_index]]
        if phase == 8:
            role, text = 'user', f'第一次改名：“{old}”改叫“{middle}”，两个标识指同一份{DOMAINS[ci]}记录，不是复制出新项目；条件、选择与历史归属不变。'
        elif phase == 9:
            role, text = 'user', f'第二次改名：“{middle}”现改叫“{current}”，仍是同一份{DOMAINS[ci]}记录。名称连接继续沿用，之前的选择和改口没有另归他人；不因改名放宽任何条件。'
        else:
            role, text = 'user', f'辨明另一份文件：“{current}”与“{denied}”不是同一项，后者不继承本项的条件或选择。我尚未对“{denied}”选过策略；名字相像和外部示例都不构成同一关系。'
    else:
        if phase == 8:
            role, text = 'user', f'记录名更正：“{old}”改叫“{current}”，完整标识虽变，仍是同一份{DOMAINS[ci]}记录，旧名与新名引用同一项，不是项目移交；选择、条件和改口归属保持。'
        elif phase == 9:
            role, text = 'user', f'请分开：“{current}”和“{denied}”不是同一项；后者没有我的策略选择记录，不继承本项选择。共享词尾或示例中的说法不是改名证据。'
        else:
            other = current_names[ci ^ 1]
            bare = current.split('/')[-1]
            role, text = 'user', f'同简称提醒：“{current}”与“{other}”是两项独立记录，不能合并。只写“{bare}”可能指这两项中的任一项；档号是标识的一部分。旧标识也必须按完整档号区分；我没指定档号时别替我选项目。'
    return role, text


def scenario(family, index, kind):
    old, current = names(family)
    label = old[index] if kind in ('base_old_alias', 'revised_old_alias') else current[index]
    if kind == 'linked_name':
        label = CHAIN_MID[index] if family == 'chain' else old[index]
    if kind == 'denied_name':
        label = denied_name(family, index)
    prefix = f'只根据该人的记录，问完整标识“{label}”这项当前会选的策略。'
    base = '已经明确允许可撤销模拟；准备时间充裕且材料齐备。本人选哪种完整策略？'
    narrow = '已经明确允许可撤销模拟；时间很紧、材料尚未齐全，且负责人愿意先给反馈。依当前有效选择，哪种完整策略？'
    exception = '已经明确允许可撤销模拟；时间很紧、材料尚未齐全，负责人明确不愿先给反馈。本人选哪种完整策略？'
    if kind in ('base_current', 'base_old_alias', 'denied_name'):
        return prefix + base
    if kind == 'exception_current':
        return prefix + exception
    if kind in ('revised_current', 'revised_old_alias'):
        return prefix + narrow
    if kind == 'linked_name':
        return prefix + (narrow if family == 'chain' else exception)
    if kind == 'scope_not_established':
        return prefix + '准备时间充裕且材料齐备，但是否已经明确允许可撤销模拟没有提供，不补成已许可。记录能否确定唯一策略？'
    if kind == 'ambiguity' and family == 'chain':
        return prefix + '已经明确允许可撤销模拟。实际恰为以下全部可能之一：时间充裕且材料齐备；时间很紧、材料未齐且负责人明确不愿先反馈。尚不知是哪一种。只有所有可能分支同选才选，否则U。'
    if kind == 'ambiguity':
        bare = ('星图', '岚页', '木桥', '雪签')[index]
        context = narrow if index % 2 else base
        return f'记录里提到简称“{bare}”，但没有档号，未提供任何能排除同简称另一项的事实。不替本人选项目。{context}只有全部可能项目同选才确定，否则U。'
    if kind == 'same_choice_contexts' and family == 'chain':
        return prefix + '已经明确允许可撤销模拟。实际恰为以下全部可能之一：时间充裕且材料齐备；时间很紧、材料未齐且负责人愿意先给反馈。两种情境没有更多区别事实。若两种分支同选，应给唯一完整策略；只有分歧或缺证据才U。'
    if kind == 'same_choice_contexts':
        labels = current if index % 2 == 0 else old
        return f'已经明确允许可撤销模拟，实际恰为两个配对情况之一：“{labels[index]}”且时间充裕、材料齐备；“{labels[index ^ 1]}”且时间很紧、材料未齐、负责人明确不愿先反馈。未知是哪一组，项目与情境按上述配对，不额外组合。若所有可能都同选就给该策略，否则U。'
    return f'只问真实已发生事实：完整标识“{label}”的项目是否已经真实启动？不问准备偏好、安排或行动许可。'


def target(pi, index, kind, damage=None):
    family = FAMILIES[pi]
    if damage == 'always_unknown':
        return 'U'
    if kind == 'same_choice_contexts':
        if damage == 'over_abstain' or damage == 'stale_revision' and family == 'chain':
            return 'U'
        if family == 'qualified' and index % 2:
            if damage == 'drop_positive_names': return 'U'
            return ACTIONS[BITS[pi][index if damage == 'guess_mapping' else old_current(pi, index)]]
        return ACTIONS[BITS[pi][index]]
    if kind == 'denied_name':
        return ACTIONS[BITS[pi][index]] if damage == 'merge_denied' else 'U'
    if kind == 'scope_not_established':
        return ACTIONS[BITS[pi][index]] if damage == 'drop_gate' else 'U'
    if kind == 'ambiguity':
        return ACTIONS[BITS[pi][index]] if damage == 'erase_namespace' and family == 'qualified' else 'U'
    if kind == 'execution_fact':
        return '已真实启动' if damage == 'tool_fact' else 'U'
    if kind in ('base_old_alias', 'revised_old_alias', 'linked_name'):
        if damage == 'drop_positive_names' or damage == 'drop_chain_edges' and family == 'chain':
            return 'U'
    ci = index
    if kind in ('base_old_alias', 'revised_old_alias') or kind == 'linked_name' and family == 'qualified':
        ci = index if damage == 'guess_mapping' else old_current(pi, index)
    elif kind == 'linked_name':
        ci = index if damage == 'guess_mapping' else MID_CURRENT[pi][index]
    bit = BITS[pi][ci]
    if kind == 'exception_current' or kind == 'linked_name' and family == 'qualified':
        bit = 1 - bit
    if damage == 'stale_revision' and (kind in ('revised_current', 'revised_old_alias') or kind == 'linked_name' and family == 'chain'):
        bit = 1 - bit
    return ACTIONS[bit]


def build():
    sources, locations = {}, {}
    for pi, person in enumerate(PROFILES):
        messages = []
        for phase in range(12):
            for oi in ORDERS[pi]:
                role, text = phase_message(pi, oi, phase)
                sid = 's%02d' % (len(messages) + 1)
                locations[pi, oi, phase] = sid
                messages.append(dict(id=sid, episode_id='journal%d' % oi, role=role, text=text))
        sources[person] = dict(schema_version=1, sources=messages)
    banks, rows, evidence = {}, [], []
    for family in ('chain', 'qualified'):
        queries = []
        for index in range(4):
            for ki, kind in enumerate(KINDS):
                ci = index * 11 + ki
                qid = 'v%02d' % ((ci * 17 + 9) % 44 + 1)
                options = ('已真实启动', '尚未真实启动') if kind == 'execution_fact' else ACTIONS
                for order in (0, 1):
                    queries.append(dict(id=qid + ('_ab' if order == 0 else '_ba'), scenario=scenario(family, index, kind),
                                        options=dict(zip(('A', 'B'), options if order == 0 else reversed(options)))))
                for pi, person in enumerate(PROFILES):
                    if FAMILIES[pi] != family:
                        continue
                    gold = target(pi, index, kind)
                    expected = HAND[pi][ci]
                    if gold != ('U' if expected == 'U' else ACTIONS[int(expected)]):
                        raise ValueError('Manual source/reference constructor check differs')
                    case = '%d_%s' % (index, kind)
                    rows.append(dict(person=person, case=case, query_ids=[qid + '_ab', qid + '_ba'], gold=gold,
                                     personal_known=gold != 'U', stratum='execution' if kind == 'execution_fact' else 'preference',
                                     cohort=kind, family=family))
                    owners = [index]
                    if kind in ('ambiguity', 'same_choice_contexts') and family == 'qualified':
                        owners = ([j for j in range(4) if old_current(pi, j) in (index, index ^ 1)]
                                  if index % 2 == 0 else [index - 1, index])
                    elif kind == 'linked_name' and family == 'chain':
                        owners = [OLD_MID[pi].index(index)]
                    elif kind not in ('base_old_alias', 'revised_old_alias', 'linked_name'):
                        owners = [next(j for j in range(4) if old_current(pi, j) == index)]
                    episodes = {'journal%d' % j for j in owners}
                    evidence.append(dict(person=person, case=case,
                                         source_ids=[s['id'] for s in sources[person]['sources'] if s['episode_id'] in episodes and s['role'] == 'user'],
                                         context_source_ids=[s['id'] for s in sources[person]['sources'] if s['episode_id'] in episodes and s['role'] != 'user'],
                                         author_analysis_not_independent_acceptance=True))
        pairs = [queries[i:i + 2] for i in range(0, len(queries), 2)]
        banks[family] = [q for i in range(44) for q in pairs[(i * 13 + 7) % 44]]
    return dict(sources=sources, queries=banks, rows=rows, author_evidence=evidence,
                design=dict(fictional_people=4, source_messages=192, messages_per_person=48, user_messages_per_person=36,
                            scenario_families=['chain', 'qualified'], unique_public_forms=176, forms_per_own_reader=88,
                            person_cases_per_method_budget=176, known=112, unknown=64,
                            positive_name_cases=48, other_cases=128, denied_identity_cases=16, same_choice_uncertainty_cases=16,
                            author_knew_previous_failures=True, independent_holdout=False, independent_semantic_gold=False))


def damage_summary():
    rows = build()['rows']
    result = {}
    for damage in ('drop_positive_names', 'drop_chain_edges', 'guess_mapping', 'merge_denied', 'erase_namespace', 'stale_revision', 'drop_gate', 'tool_fact', 'over_abstain', 'always_unknown'):
        losses = []
        for pi, person in enumerate(PROFILES):
            for index in range(4):
                for kind in KINDS:
                    choice = target(pi, index, kind, damage)
                    if choice != target(pi, index, kind):
                        losses.append(dict(person=person, case='%d_%s' % (index, kind), gold=target(pi, index, kind), damaged=choice))
        result[damage] = dict(planned=len(rows), correct=len(rows) - len(losses), losses=losses,
                              oracle_calibration_not_model_measurement=True)
    return result
