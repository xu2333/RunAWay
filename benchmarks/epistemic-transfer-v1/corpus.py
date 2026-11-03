"""Finite, source-licensed inference; hidden generating rules are not reference truth."""
import itertools

PROFILES = ('a8r', 'b6t', 'c2v', 'd9n', 'e4q', 'f7s', 'g1w', 'h3k')
STATES = tuple(itertools.product((0, 1), repeat=2))  # entirely local, fully reversible
RULE_TABLES = ((1, 1, 1, 1), (0, 0, 1, 1), (0, 1, 0, 1), (0, 0, 0, 1))
ALL_TABLES = tuple(itertools.product((0, 1), repeat=4))
DOMAINS = (
    ('notes', '个人生活笔记的自动整理', ('保持手动整理', '启用自动整理')),
    ('signup', '个人活动报名记录的自动分组', ('保持手动分组', '启用自动分组')),
)
# Each policy value occurs with two different other-domain policies, in both
# directions. These are eight selected joint settings, not independent authors.
POLICIES = ((0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 3))
GUARANTEES = ((True, True), (False, True), (True, False), (False, False),
              (True, True), (True, False), (False, True), (True, True))
OBSERVED = (((1, 2), (1, 2)), ((1, 2), (1, 2)), ((1,), (1, 2)), ((1, 2), (1, 2)),
            ((1,), (1,)), ((1, 2), (1, 2)), ((1,), (1, 2)), ((1, 2), (1,)))
# Withdrawn domains deliberately include rules outside the illustrative family.
# Their disclosed decisions match the listed observation signature; unobserved
# generating truth is not allowed to determine source-supported gold.
OUTSIDE_TABLES = {(1, 0): (0, 1, 1, 0), (2, 1): (0, 1, 1, 0),
                  (3, 0): (1, 0, 1, 0), (3, 1): (1, 1, 0, 0),
                  (5, 1): (0, 0, 0, 0), (6, 0): (1, 0, 0, 1)}
GENERATING_TABLES = tuple(tuple(OUTSIDE_TABLES.get((pi, di), RULE_TABLES[rule])
                               for di, rule in enumerate(pair)) for pi, pair in enumerate(POLICIES))
U = 'U'
# Separately written semantic reference rows: four complete, two partial, one
# out-of-vocabulary case/domain, then one unobserved-domain case. 0/1 are actions.
HAND_GOLD = (
    (1,1,1,1,1,1,U, 1,1,1,1,1,1,U, U),
    (U,1,1,U,U,U,U, 0,0,1,1,U,0,U, U),
    (0,0,U,1,U,0,U, U,1,1,U,U,U,U, U),
    (U,0,1,U,U,U,U, U,1,0,U,U,U,U, U),
    (U,1,U,1,1,U,U, 0,0,U,1,U,0,U, U),
    (0,1,0,1,1,U,U, U,0,0,U,U,U,U, U),
    (U,0,U,U,U,U,U, 0,1,0,1,1,U,U, U),
    (0,0,0,1,U,0,U, 0,0,U,1,U,0,U, U),
)


def predict(rule, state):
    local, undo = state
    return int((True, bool(local), bool(undo), bool(local and undo))[rule])


def compatible(evidence):
    """Use only disclosed guarantee and decisions, never the generating policy."""
    if type(evidence['guarantee']) is not bool:
        raise ValueError('Guarantee must be explicit boolean')
    candidates = RULE_TABLES if evidence['guarantee'] else ALL_TABLES
    observations = evidence['observations']
    for state, action in observations:
        if type(state) is not int or state not in range(4) or type(action) is not int or action not in (0, 1):
            raise ValueError('Invalid observation')
    result = [table for table in candidates if all(table[s] == a for s, a in observations)]
    if not result:
        raise ValueError('Contradictory evidence is not an unknown preference')
    return result


def oracle(evidence, case):
    candidates = compatible(evidence)
    if not case['in_scope']:
        return U
    values = {table[state] for table in candidates for state in case['states']}
    return next(iter(values)) if len(values) == 1 else U


def features(state, question=False):
    local, undo = state
    return (('全部内容只留在本机，完全不外发' if local else '完整内容会传到外部服务') + '；' +
            ('任何改动都能一步完整恢复' if undo else '任何改动都不能撤销，也找不回原数据') + '。')


def family_text(domain):
    _, name, actions = domain
    manual, auto = actions
    return (name + '，先把讨论过的四种候选说完整：甲是不论这两项取值都选“' + auto +
            '”；乙当且仅当全部内容留在本机时选“' + auto + '”，否则选“' + manual +
            '”；丙当且仅当改动可完整恢复时选“' + auto + '”，否则选“' + manual +
            '”；丁当且仅当内容完全留在本机、而且改动可完整恢复时选“' + auto +
            '”，否则选“' + manual + '”。我先保证自己在这个范围固定采用其中一条，但不透露是哪一条。')


def case_specs():
    cases = []
    for di, (key, name, actions) in enumerate(DOMAINS):
        for si, state in enumerate(STATES):
            cases.append({'id': key + '_complete_' + str(si), 'domain': di, 'states': [si],
                'in_scope': True, 'kind': 'complete', 'scenario': '换一款新界面处理' + name + '。' + features(state, True)})
        cases += [
            {'id': key + '_partial_local', 'domain': di, 'states': [1, 3], 'in_scope': True,
             'kind': 'partial_features', 'scenario': name + '：所有改动可一步完整恢复，没有说明内容是否外发；外发只可能是完整外发或完全本机这两种。'},
            {'id': key + '_partial_undo', 'domain': di, 'states': [0, 1], 'in_scope': True,
             'kind': 'partial_features', 'scenario': name + '：完整内容会传到外部服务，没有说明能否撤销；撤销只可能是完整恢复或完全不能恢复这两种。'},
            {'id': key + '_outside_feature', 'domain': di, 'states': [], 'in_scope': False,
             'kind': 'outside_feature', 'scenario': name + '：可以完整恢复，只向外部发摘要，既不是完整外发也不是完全不外发。'},
        ]
    cases.append({'id': 'outside_domain', 'domain': None, 'states': [], 'in_scope': False,
                  'kind': 'outside_domain', 'scenario': '现在改成自动向群聊发布动态，既不是个人笔记整理，也不是个人报名记录分组。内容仅在本机、改动可完整恢复。'})
    return cases


def build(generating_tables=None):
    for rule in range(4):
        if tuple(predict(rule, state) for state in STATES) != RULE_TABLES[rule]:
            raise ValueError('Hand truth table differs')
    generating_tables = GENERATING_TABLES if generating_tables is None else generating_tables
    for pi, pair in enumerate(generating_tables):
        for di, table in enumerate(pair):
            if len(table) != 4 or any(type(a) is not int or a not in (0, 1) for a in table):
                raise ValueError('Generating table must define four binary actions')
            if GUARANTEES[pi][di] and table not in RULE_TABLES:
                raise ValueError('Active family guarantee conflicts with generating truth')
    specs = case_specs()
    queries = []
    for index, case in enumerate(specs):
        actions = DOMAINS[case['domain']][2] if case['domain'] is not None else ('保持手动发布', '启用自动发布')
        for order in (0, 1):
            options = actions if order == 0 else tuple(reversed(actions))
            queries.append({'id': 'e%02d_%s' % (index + 1, 'ab' if order == 0 else 'ba'),
                'scenario': case['scenario'] + '只问本人在这些条件下会选择哪种做法；没有唯一有依据的选择则回答U。',
                'options': dict(zip(('A', 'B'), options))})
    sources, rows, author = {}, [], {}
    for pi, pid in enumerate(PROFILES):
        messages, evidence = [], {}
        def add(role, text, episode):
            messages.append({'id': 'm%02d' % (len(messages) + 1), 'episode_id': episode, 'role': role, 'text': text})
        add('user', '这里分开讨论两件低风险软件选择：个人生活笔记的自动整理、个人活动报名记录的自动分组。在各自范围内，只根据是否完整外发、能否完整恢复这两个二元特征决定；同样的特征组合不因应用名字、题材、界面或设备改变。但两个范围不保证采用同一准则。外发只定义完整外发或完全本机，恢复只定义全部可恢复或全部不可恢复；摘要外发、部分恢复不在定义范围。已作废的旧决定和未获我确认的候选不算有效观察。', 'scope')
        for di, domain in enumerate(DOMAINS):
            key, name, actions = domain
            add('user', family_text(domain), key)
            observations = []
            for si in (1, 2):
                action = generating_tables[pi][di][si]
                suggestion = (si + di) % 2  # independent of the hidden rule/action
                add('user', '这一次在“' + name + '”里比较两种做法。' + features(STATES[si]) + '本条只列条件，还没有选择；这次条件只用于这个范围，别把另一个范围的决定挪过来。', key)
                add('assistant', '我的建议是“' + actions[suggestion] + '”。这只是我提出的一种候选，不代表用户已接受；我也不能根据候选名字替用户认定采用了哪条准则。', key)
                if si in OBSERVED[pi][di]:
                    add('user', '同样的完整条件，以我现在最后确认的为准：我明确选“' + actions[action] + '”。如果此前草稿里写过另一种做法，那条作废；不要把助手的另一种建议当成我同时也接受了它。', key)
                    observations.append([si, action])
                else:
                    add('user', '这次我只比较过候选，还没有作出决定。不要把助手推荐或界面显示当成我的选择，也不要替我补一个确认；这个条件组合目前没有有效的本人决定记录。', key)
                add('tool', '界面候选栏仍显示“' + actions[suggestion] + '”。这只是候选列表记录，没有执行动作，没有用户确认，也没有替用户改变最后的决定。', key)
            if GUARANTEES[pi][di]:
                add('user', name + '这一范围，前面说的“四个候选之一”这个完整性保证继续有效；只是在四者中到底哪条，我仍不直接透露。前面有效的本人决定继续保留。相同特征组合会遵循同一个固定准则，不按题材临时改。', key)
            else:
                add('user', name + '这一范围要更正一个保证：前面四种只当讨论例子，我撤回“我的准则一定只从这四种中选”的完整性保证。并不是说原来已确认的选择作废；那些有效决定继续保留。同特征组合仍稳定，但别替我补出尚未透露的完整规则或未决定的新组合。', key)
            evidence[di] = {'guarantee': GUARANTEES[pi][di], 'observations': observations}
        add('user', '最后再确认两个范围是独立记录的：不能因为笔记整理用了某种方式，就默认报名分组也相同。当前有效的是各自范围的最后保证和本人明确决定；工具与助手的候选不增加新的本人决定。定义之外的做法没有在这段记录中建立规则。', 'scope')
        sources[pid] = {'schema_version': 1, 'sources': messages}
        author[pid] = {'hidden_generating_tables_not_reference_truth': [list(t) for t in generating_tables[pi]],
                       'public_evidence': [evidence[di] for di in range(2)],
                       'compatible_tables': [[list(t) for t in compatible(evidence[di])] for di in range(2)]}
        for ci, case in enumerate(specs):
            di = case['domain']
            ev = evidence[di] if di is not None else {'guarantee': False, 'observations': []}
            value = oracle(ev, case)
            if value != HAND_GOLD[pi][ci]:
                raise ValueError('Separately written hand reference differs: ' + pid + ':' + case['id'])
            actions = DOMAINS[di][2] if di is not None else ('保持手动发布', '启用自动发布')
            known = value != U
            no_obs = oracle({'guarantee': ev['guarantee'], 'observations': []}, case)
            observed = case['kind'] == 'complete' and case['states'][0] in {s for s, _ in ev['observations']}
            cohort = ('observed_decision' if observed else 'undecided_training_condition'
                      if case['kind'] == 'complete' and case['states'][0] in (1, 2)
                      else 'unseen_combination' if case['kind'] == 'complete' else case['kind'])
            stale = oracle({'guarantee': True, 'observations': ev['observations']}, case) if di is not None else U
            rows.append({'person': pid, 'case': case['id'], 'gold': U if not known else actions[value],
                'query_ids': ['e%02d_%s' % (ci + 1, order) for order in ('ab', 'ba')],
                'personal_known': known and no_obs != value, 'structural_known': known and no_obs == value,
                'derived_known': known and not observed, 'guarantee_withdrawal_sensitive': not ev['guarantee'] and stale != value,
                'stratum': 'preference', 'cohort': cohort})
    counts = {'known': sum(r['gold'] != U for r in rows), 'unknown': sum(r['gold'] == U for r in rows),
              'personal_known': sum(r['personal_known'] for r in rows),
              'structural_known': sum(r['structural_known'] for r in rows),
              'derived_known': sum(r['derived_known'] for r in rows),
              'withdrawal_sensitive': sum(r['guarantee_withdrawal_sensitive'] for r in rows)}
    if counts != {'known': 58, 'unknown': 62, 'personal_known': 48, 'structural_known': 10,
                  'derived_known': 31, 'withdrawal_sensitive': 20}:
        raise ValueError('Predeclared population counts differ')
    return {'sources': sources, 'queries': {'all': queries}, 'rows': rows, 'author_parameters': author,
            'design': {'kind': 'finite_source_licensed_transfer_stress', 'fictional_profiles': 8,
                'domains': 2, 'source_messages': 176, 'primary_cases': 120, **counts,
                'unique_public_forms': 30, 'person_form_combinations': 240,
                'external_reader_decoder': False, 'hidden_policy_used_for_reference': False,
                'independent_semantic_acceptance': False, 'independent_holdout': False,
                'naturalistic_human_fidelity': False}}
