"""Versioned synthetic micro-world. Gold choices come from code, never an LLM judge."""
import random
from .card import canonical, digest

WORLD_VERSION = 1
AXES = ('planning', 'autonomy', 'feedback', 'revision')
POLICIES = [
    dict(trial=True, rollback_guard=True, automate=True, public_soft=True, revise=True),
    dict(trial=True, rollback_guard=False, automate=True, public_soft=True, revise=True),
    dict(trial=False, rollback_guard=True, automate=False, public_soft=True, revise=True),
    dict(trial=False, rollback_guard=True, automate=True, public_soft=True, revise=True),
    dict(trial=True, rollback_guard=True, automate=True, public_soft=False, revise=False),
    dict(trial=True, rollback_guard=True, automate=True, public_soft=True, revise=False),
]
TRAIN_CONTEXTS = {
    'planning': ['给虚构读书会做一个内部工具', '重新布置自己的书桌', '给内部简报设计版式'],
    'autonomy': ['给个人笔记加标签', '整理自己保存的网页', '把私人草稿归到文件夹'],
    'feedback': ['同伴请你评价一页活动说明', '同伴请你评价一张课程海报', '同伴请你评价一段小说开头'],
    'revision': ['把工具的导出按钮藏入二级菜单', '把查找入口收进折叠区', '把日历切换放进设置页'],
}
TEST_CONTEXTS = {
    'planning': ['为虚构的桌游社设计签到方式', '为自己搭建室内小花园', '为同好会设计道具摆放方案'],
    'autonomy': ['对自己的音乐片段分组', '为自己制作的像素画归档', '给私人菜谱添加分类'],
    'feedback': ['伙伴希望听你对播客片头的意见', '伙伴希望听你对展览导语的意见', '伙伴希望听你对社团介绍的意见'],
    'revision': ['把批量重命名藏入高级选项', '把切换字幕收进偏好设置', '把收藏夹入口放进第二层页面'],
}


def public_case(axis, flag, context, order, case_id):
    if axis == 'planning':
        question = context + '。目前方向尚未验证，两种方案都可完成，没有硬期限。' + (
            '一旦选定并执行，之后半年无法撤回或改动。' if flag else '试用后可当天免费撤回和改动。')
        options = {'trial': '先用轻量方案开始，观察效果再细化。', 'plan': '先把方案完整规划好，再开始执行。'}
    elif axis == 'autonomy':
        question = context + '。这是熟悉的重复操作，自动处理约有 5% 分错；逐项确认更准确但多一步。' + (
            '自动操作的结果无法撤销，也不能恢复原状。' if flag else '分错的项目可以一键撤销并恢复原状。')
        options = {'auto': '默认自动处理，减少每次确认。', 'ask': '保持逐项手动确认。'}
    elif axis == 'feedback':
        question = context + '。你发现一个重要但可以修正的问题，对方没有指定反馈方式，没有紧急风险。' + (
            '意见会在伙伴和其他成员都在的群聊中发出。' if flag else '意见通过只有你和伙伴的私聊发出。')
        options = {'direct': '第一句就点明问题，然后给修改建议。', 'soft': '先铺垫理解与肯定，再指出问题和建议。'}
    else:
        question = '你之前为了简洁，决定' + context + '。现在可以维持设计或把它放回显眼位置，代价都很小。' + (
            '多个使用者连续几周反复找不到它，并向你求助。' if flag else '目前只有一个使用者问过一次，尚无重复反馈。')
        options = {'restore': '把入口放回显眼位置，接受多一个控件。', 'keep': '继续保留简洁布局，让使用者适应入口位置。'}
    keys = list(options)
    if order:
        keys.reverse()
    return {'id': case_id, 'question': question, 'A': options[keys[0]], 'B': options[keys[1]]}, {'A': keys[0], 'B': keys[1]}


def action(policy, axis, flag):
    if axis == 'planning':
        return 'trial' if policy['trial'] and not (flag and policy['rollback_guard']) else 'plan'
    if axis == 'autonomy':
        return 'auto' if policy['automate'] and not flag else 'ask'
    if axis == 'feedback':
        return 'soft' if flag and policy['public_soft'] else 'direct'
    if axis == 'revision':
        return 'restore' if flag and policy['revise'] else 'keep'
    raise ValueError('Unknown synthetic axis')


def gold(policy, case):
    wanted = action(policy, case['axis'], case['flag'])
    return next(label for label, value in case['actions'].items() if value == wanted)


def feedback(policy, case, proposal):
    label = gold(policy, case)
    chosen = case['actions'][label]
    reasons = {
        'trial': '我愿意先开始观察，再根据实际效果细化。',
        'plan': '这次我宁愿先完整规划好再执行。',
        'auto': '这种熟悉的重复操作能撤销，我接受少量分错来省下每次确认。',
        'ask': '这次我要保留逐项确认，不把步骤自动省掉。',
        'direct': '我希望先把问题直接说明白，再讨论怎么改。',
        'soft': '当着其他成员，我会先让对方感到被理解，再说问题。',
        'restore': '反复出现的求助让我愿意改变原来追求简洁的决定。',
        'keep': '这次我仍愿意保留简洁布局，让人适应入口的位置。',
    }
    agreement = '就按你建议的来。' if proposal == label else '这里我会改选，不按刚才的建议走。'
    return agreement + '我的选择是 ' + label + '：' + case['public'][label] + reasons[chosen]


def oracle_memory(policy):
    return ('以下是虚构人物在本实验中的已知规则，仅用于解码上限对照。'
            + ('平时先尝试再细化；' if policy['trial'] else '平时先完整规划再开始；')
            + ('无法撤回时改为先完整规划。' if policy['rollback_guard'] else '即便无法撤回，也不改变上述规划倾向。')
            + ('熟悉重复任务只要能撤销就自动处理，否则逐项确认。' if policy['automate'] else '熟悉重复任务也保留逐项确认，无论能否撤销。')
            + ('私聊直接点明问题，群聊先铺垫再指出。' if policy['public_soft'] else '评价可修改的问题时，私聊群聊都直接点明。')
            + ('单次求助维持简洁，连续反复求助则恢复显眼入口。' if policy['revise'] else '面对单次或连续重复求助，都维持简洁布局。')
            + '没有给出的审美和生活偏好未知。')


def build_world(seed=41617):
    rng = random.Random(seed)
    personas = [{'id': f'p{i+1:02}', 'twin': f'p{(i ^ 1)+1:02}', 'policy': p} for i, p in enumerate(POLICIES)]
    train = []
    # Four tasks per round, independent new setting each round. All policies receive
    # exactly the same tasks; only their oracle's approvals/corrections differ.
    for round_no in range(3):
        for axis in AXES:
            flag = round_no == 1
            case_id = 'tr-' + digest(f'{seed}-{round_no}-{axis}')[:10]
            public, actions = public_case(axis, flag, TRAIN_CONTEXTS[axis][round_no], rng.randrange(2), case_id)
            train.append({'axis': axis, 'flag': flag, 'round': round_no, 'public': public, 'actions': actions})
    test = []
    for axis in AXES:
        for i, context in enumerate(TEST_CONTEXTS[axis]):
            order = rng.randrange(2)
            pair = f'{axis}-{i}'
            for flag in (False, True):
                case_id = 'q-' + digest(f'{seed}-{pair}-{flag}')[:10]
                public, actions = public_case(axis, flag, context, order, case_id)
                # A separate renderer for held-out questions; no copied training sentences.
                settings = {
                    'planning': context+'：你在开始前比较两种做法，没有到期压力，也还没验证方向。'+('方案落实后六个月都不能调整，选错也只能继续用。' if flag else '先做的版本可以零成本当天改掉，试错完全可逆。'),
                    'autonomy': context+'，工作熟悉但重复。系统能替你分组，准确率为 95%；人工逐个点选更准，也更费步骤。'+('这次没有恢复功能，自动分错就不能回到原状。' if flag else '这次有恢复功能，自动分错随时一键恢复。'),
                    'feedback': context+'。作品有需要修改之处，对方没说希望你怎样提意见，也没有紧急风险。'+('交流场合是有其他成员旁观的群组。' if flag else '交流场合是一对一的私人消息。'),
                    'revision': '为了界面简洁，你此前决定'+context+'。调整回去只需一点成本。'+('接下来几周不止一位使用者持续为找入口来问你。' if flag else '接下来只有一位使用者问了一回，没有后续反复求助。'),
                }
                public['question'] = settings[axis]
                alternate = {'trial':'用一个小版本开始，从使用效果中迭代。','plan':'先形成完整的设计，再着手实施。','auto':'让系统直接替我完成分类。','ask':'每一项都先由我确认。','direct':'开头直接指出哪里有问题，再给建议。','soft':'先表达理解和肯定，之后进入问题与建议。','restore':'增加一个显眼入口，方便大家直接找到。','keep':'保留原布局，继续让大家熟悉它。'}
                public.update({label: alternate[value] for label,value in actions.items()})
                test.append({'axis': axis, 'flag': flag, 'pair': pair, 'kind': 'heldout', 'public': public, 'actions': actions})
    # Four exact action-order reversals measure label bias, not extra independent tasks.
    for original in [test[0], test[6], test[12], test[18]]:
        c = original['public']
        test.append({**original, 'kind': 'order_swap', 'original_id': c['id'],
                     'public': {'id': 'q-' + digest(c['id'] + '-swap')[:10], 'question': c['question'], 'A': c['B'], 'B': c['A']},
                     'actions': {'A': original['actions']['B'], 'B': original['actions']['A']}})
    for i, (question, a, b) in enumerate([
        ('挑选一个同样好用、同样便宜的马克杯，没有送礼或搭配要求。这个人更喜欢哪个颜色？', '蓝色', '橙色'),
        ('独处休息，无其他限制。这个人更想听哪种背景音乐？', '爵士乐', '电子乐'),
    ]):
        test.append({'axis': 'unobserved', 'kind': 'unobserved', 'public': {'id': 'q-'+digest(f'{seed}-unknown-{i}')[:10], 'question': question, 'A': a, 'B': b}})
    rng.shuffle(test)
    body = {'schema_version': 1, 'world_version': WORLD_VERSION, 'origin': 'fully_synthetic',
            'seed': seed, 'personas': personas, 'training': train, 'test': test}
    return {**body, 'id': digest(canonical(body))}


def synthetic_sources(world, persona, rounds):
    sources = []
    for case in world['training']:
        q = case['public']
        prediction = rounds[case['round']][q['id']]
        episode = q['id']
        for role, suffix, text in [
            ('user', 'task', '【合成交互，非真人】'+q['question']+'\nA：'+q['A']+'\nB：'+q['B']),
            ('assistant', 'proposal', '我的建议是 '+prediction+'。'),
            ('user', 'correction', feedback(persona['policy'], case, prediction)),
        ]:
            sources.append({'id': episode+'-'+suffix, 'episode_id': episode, 'role': role, 'text': text})
    return {'schema_version': 1, 'sources': sources}
