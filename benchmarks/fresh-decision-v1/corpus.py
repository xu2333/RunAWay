"""Prospective, procedurally authored fiction; not independently authored holdout."""
PROFILES = ('auri', 'bryn', 'cato', 'dune')
SETTINGS = ((0, 0, 0, 0), (1, 1, 1, 1), (0, 1, 0, 1), (1, 0, 1, 0))
DOMAINS = (
    {'id': 'draft', 'name': '共同写稿时的交付形态',
     'actions': ('先交结构稿', '先交完整成稿'),
     'base': '熟悉的内部合作者愿意讨论，双方能当天来回沟通，交付形态没有硬性规定',
     'exception': '对方第一次与我合作，而且只能隔天异步回复',
     'override': '对方已经列清三个具体分歧，并同意本轮只解决这三个分歧',
     'tradeoff': '结构稿更容易暴露分歧，完整成稿更容易让人看到语气和上下文；两种都能按时交，我并不是在比较谁更勤奋。',
     'unknown': ('若两款写作软件功能、价格和协作能力相同，只问本人更偏爱哪款软件；不问交付形态。', ('偏爱纸桥', '偏爱青岚'))},
    {'id': 'roster', 'name': '周末互助活动的分工方式',
     'actions': ('提前固定分工', '到场后认领任务'),
     'base': '参加者彼此熟悉、出席比较稳定，两种分工方式都能覆盖所有任务',
     'exception': '这次报名人数临近活动时仍会明显变化',
     'override': '同一个统筹者已经连续负责过两场，并主动承诺承担本场的临时协调',
     'tradeoff': '固定分工省去现场商量，到场认领更能利用当天状态；我不认为其中一个永远高级，也不把习惯解释成是否信任大家。',
     'unknown': ('只问已完成事实：本人是否已经把本月活动的正式分工表提交了；不要把偏好或拟议做法当作提交记录。', ('已经提交分工表', '尚未提交分工表'))},
    {'id': 'support', 'name': '朋友来聊烦恼时的回应起点',
     'actions': ('先听完整叙述', '先一起列可行动的步骤'),
     'base': '面对面聊近期的小烦恼，没有紧急危险，朋友没有限定我必须用哪种回应方式',
     'exception': '交流改成文字，而且消息断断续续、上下文尚未连起来',
     'override': '朋友已经完整讲过来龙去脉，我也复述并确认自己理解准确',
     'tradeoff': '听完可能让对方感觉被理解，先列步骤也可能帮助整理思绪；我不会把我喜欢的顺序当作对方永远需要的顺序。',
     'unknown': ('若两处见面地点都安静、方便且没有费用差别，只问本人更偏爱哪种地点；不问回应朋友的先后。', ('偏爱安静咖啡馆', '偏爱安静公园'))},
    {'id': 'research', 'name': '研究小问题时的切入方式',
     'actions': ('先独立推导再查相关工作', '先查相关工作再独立推导'),
     'base': '问题和符号都熟悉，没有截止日压力，两条路径都被允许',
     'exception': '问题使用的符号体系对我完全陌生',
     'override': '本轮只需要找到一个反例，而且约定今晚的草稿可以整体丢弃',
     'tradeoff': '独立推导能暴露自己的直觉，先查资料能减少重复劳动；这里讨论探索顺序，不是论文引用是否完整或已经证明了什么。',
     'unknown': ('只问本人记录数学草稿时长期偏爱哪种载体；不问先推导还是先查资料，两种载体都能完成任务。', ('偏爱纸笔草稿', '偏爱电子草稿'))},
)
# Separately written labels check the constructor; they are not independent gold.
HAND = (
    (0, 1, 0, 'U', 0, 1, 0, 'U', 0, 1, 0, 'U', 0, 1, 0, 'U'),
    (1, 0, 1, 'U', 1, 0, 1, 'U', 1, 0, 1, 'U', 1, 0, 1, 'U'),
    (0, 1, 0, 'U', 1, 0, 1, 'U', 0, 1, 0, 'U', 1, 0, 1, 'U'),
    (1, 0, 1, 'U', 0, 1, 0, 'U', 1, 0, 1, 'U', 0, 1, 0, 'U'),
)


def build():
    sources, rows, queries, evidence = {}, [], [], {}
    for di, domain in enumerate(DOMAINS):
        scenarios = (
            domain['name'] + '：' + domain['base'] + '；没有后述特殊情况。只问本人会选哪种完整方案。',
            domain['name'] + '：' + domain['exception'] + '；未满足后来补充的特殊约定，其余资源允许两种方案。只问本人会选哪种完整方案。',
            domain['name'] + '：' + domain['exception'] + '；同时，' + domain['override'] + '。这次条件组合没有被逐字演示，请依据本人最后保留的适用条件判断完整方案。',
            domain['unknown'][0],
        )
        for ci, scenario in enumerate(scenarios):
            actions = domain['actions'] if ci < 3 else domain['unknown'][1]
            for order in (0, 1):
                queries.append({'id': '%s_%s_%s' % (domain['id'], ci, 'ab' if order == 0 else 'ba'),
                                'scenario': scenario,
                                'options': dict(zip(('A', 'B'), actions if order == 0 else reversed(actions)))})
    for pi, pid in enumerate(PROFILES):
        messages, anchors = [], {}
        for di, domain in enumerate(DOMAINS):
            actions = domain['actions']
            normal, changed = actions[SETTINGS[pi][di]], actions[1 - SETTINGS[pi][di]]

            def add(role, text):
                sid = '%s_m%02d' % (pid, len(messages) + 1)
                messages.append({'id': sid, 'episode_id': domain['id'], 'role': role, 'text': text})
                return sid

            add('assistant', '关于' + domain['name'] + '，我可以建议先采用“' + changed +
                '”。这只是助手候选，还没有获得用户确认；不能用我的推荐填补用户没有表达的偏好，也没有任何工具执行或完成凭据。')
            base_id = add('user', domain['name'] + '：' + domain['base'] + '时，我会选“' + normal +
                '”。我确实比较喜欢这个起点，但不是说另一种不能做好。' + domain['tradeoff'] +
                '请把这条记在这个具体目标下，不要凭我的一段话给我贴一个能包办所有生活决定的类型标签。')
            change_id = add('user', '补充' + domain['name'] + '的一个例外：如果' + domain['exception'] +
                '，我就改用“' + changed + '”。这是该条件下的方案变化，没撤回普通条件下的“' + normal +
                '”。也不是把助手刚才的建议整体收下；只有我在这一条说到的范围才有效，不把它搬到别的活动或关系里。')
            override_id = add('user', '再缩小刚才的例外：只要' + domain['override'] + '，我仍选“' + normal +
                '”，哪怕同时存在“' + domain['exception'] + '”这一条件。这个补充优先于上一条例外，但只在这里列出的完整条件下成立。'
                '其它情形没有一起改口；现在只是记录我会选的方案，没有声称任务已执行、分工已提交或任何结果已经得到验证。')
            anchors[domain['id']] = [base_id, change_id, override_id]
            for ci in range(4):
                target = 'U' if ci == 3 else SETTINGS[pi][di] if ci in (0, 2) else 1 - SETTINGS[pi][di]
                if target != HAND[pi][di * 4 + ci]:
                    raise ValueError('Hand reference differs')
                case = '%s_%d' % (domain['id'], ci)
                rows.append({'person': pid, 'case': case,
                             'query_ids': [case + '_ab', case + '_ba'],
                             'gold': actions[target] if target != 'U' else 'U',
                             'personal_known': target != 'U', 'derived_known': ci == 2,
                             'stratum': 'execution' if domain['id'] == 'roster' and ci == 3 else 'preference',
                             'cohort': ('ordinary', 'changed_condition', 'compositional_override', 'unrecorded_target')[ci]})
        sources[pid] = {'schema_version': 1, 'sources': messages}
        evidence[pid] = anchors
    return {'sources': sources, 'queries': {'all': queries}, 'rows': rows,
            'author_evidence': evidence,
            'design': {'fictional_people': 4, 'source_messages': 64, 'public_question_forms': 32,
                       'unique_person_cases_per_view': 64, 'known': 48, 'unknown': 16,
                       'derived_known': 16, 'opposite_pairs': [['auri', 'bryn'], ['cato', 'dune']],
                       'procedurally_authored_fiction': True, 'independently_authored_holdout': False,
                       'source_reference_semantics_verified': False, 'real_person_fidelity_verified': False}}
