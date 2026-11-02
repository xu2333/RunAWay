"""Controlled long-context derivative of task-scenarios-v1, not a new holdout."""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('long_task_short_bank', HERE.parent / 'task-scenarios-v1/corpus.py')
short = importlib.util.module_from_spec(spec)
spec.loader.exec_module(short)
PROFILES = tuple(d[0] + str(side) for d in short.DOMAINS for side in (0, 1))
FAMILY = {p: p[:-1] for p in PROFILES}
PAIRS = {p: p[:-1] + str(1 - int(p[-1])) for p in PROFILES}

# Fixed before any model response. They describe operational context rather than
# repeat a reference. Four entries are replaced by the original user decisions.
CONTEXT = (
 ('user', '报名表里的联系电话已经由我逐个核过，纸本只保留一份放在前台，线上表格不再转给临时帮忙的人。有人填错日期时先联系本人，不能拿去年名单覆盖。今年第一次来的参与者很多，门口还需要一张清楚的路线图。'),
 ('assistant', '场地布置可以先画一张草图：入口处留出等候位置，桌边放说明卡，通道不要被临时箱子挡住。遇到东西放不下的情况，可以减少装饰。我建议再问问邻近场地的管理员有没有多余的夹板，但这还只是建议。'),
 ('user', '说明卡这一版字太小了，我会自己重新排一次。最上面先写活动日期，联系方式移到背面；正文不用加宣传口号。打印机的黑墨余量不多，这回只做黑白稿，不代表以后所有材料都只能黑白。'),
 ('assistant', '我把这一轮材料制作拆成排版、核对和打印三步，排版稿还没有确认，所以不替你发出去。桌号贴纸和路线图可以分开准备，免得改日期时要把所有文件一起重印。前台那份纸本仍按你先前说的保管。'),
 ('user', '今天两个人临时说会迟到，签到表上的预计到达时间我已经另起一栏。这个到达时间只用于今天安排座位，不作为下次的默认出席习惯。若有人提前离开，把实际时间补在原表上，不要在群里猜原因。'),
 ('assistant', '照明有两种可调位置，靠窗那边上午会比较亮，下午可能反光。我建议试拍一张桌面照片再决定说明卡摆向。这个建议只涉及可读性，并没有替你决定活动采用哪套流程或接受新的排班安排。'),
 ('user', '上次借来的延长线已经由值班室签收，那张签收单只证明延长线这一件东西。其他器材或样本的状态各自看自己的记录。打印好的路线图还留在柜子里，等日期最后确认后我再拿出来贴。'),
 ('assistant', '如果临时需要补印，可以先把需要修改的页码列出来，避免重新输出整套文件。群公告里可以只放一个下载入口，不附未经确认的参与者名单。是否补印以及印多少份，仍等你确认这一轮的实际人数。'),
 ('user', '入口的指示牌我改成了两行，第一行给第一次来的人看，第二行写楼层。上一版的房间号有误，旧图已经撤下。这个更正只改路线图，不把先前记录的活动选择、执行记录或新安排决定一起改掉。'),
 ('assistant', '关于现场提问，我可以帮你收集问题并按对象分组，但不会把我提出的应急办法自动当成你的承诺。有人问到尚未确认的安排时，先说明还在等答复，比替你答应一个时间更稳妥。'),
 ('user', '资料袋里有一页重复打印，已经取出来了。剩下的材料按日期装好，封面不写参与者住址。桌上那份草图是讨论用的，不是已经执行的现场记录；需要查实际发生过什么时，还是找对应的原始登记。'),
 ('assistant', '午间的现场工作人员可能换班，我建议把钥匙交接写到单独一张纸上，别混进参与者名单。这里的换班只是人员协调，不能从有人愿意帮忙推断你本人已经同意某个额外安排。'),
 ('user', '我把活动前后要搬的箱子数量清点了一次，空箱和装了资料的箱子分开放。没有编号的先不带出门。这个清点结果只管箱子，并不能代替其他对象的借用、入库或返还状态，后者还要各自核对。'),
 ('assistant', '说明卡的最新版已收进排版文件夹，旧版另放归档目录。文件夹里出现一个方案名，不表示那个方案已经被你采用。要回答你的选择，仍须看你自己的决定，以及那条决定当时说的适用条件。'),
 ('user', '当天的临时联络电话已经写在值班纸上，我会在活动后收回来。有人想提前看材料，只能发不含个人信息的公开版本。这条约定只处理资料发送，不扩展为我对未讨论过的场地或排班状态都有既定偏好。'),
 ('assistant', '天气预报可能变化，我可以准备一个室内路线说明的草稿。草稿尚未取得任何额外许可，不会改变既有许可要求。后面如果你更正某一份具体记录，我会按对象分别处理，不把相邻聊天的建议当成那条更正。'),
 ('user', '活动结束后我只收集愿意填写的反馈，空白表不记成负面评价。两份写了相反意见的表也先都留着，不为了写一段漂亮的总结就删掉其中一份。正式整理还没开始，这不是对下次活动流程的新决定。'),
 ('assistant', '反馈可以先保留原话，再整理大家重复提到的地方。这里的重复不等于独立人数，写摘要时也不该把我补充的例子当成参与者真实说过的话。如果有更正，原始版本和更正记录可以同时留着。'),
 ('user', '我今天把剩余纸张装进防潮袋，贴了实际数量，之后再印东西时重新清点。不要把今天纸张够用推成任何条件下都够用。钥匙还放在约定的抽屉里，取走时请在值班纸上登记这一次的时间。'),
 ('assistant', '收尾时可以检查通道、门窗和材料是否归位，再把未完成事项逐项写下来。没有答复的事项继续留空，不把空白改成同意。需要回顾本人决定时，应区分已经确认的选择、被更正的旧稿和我这边的建议。'),
)


def build():
    original = short.build()
    sources, queries, rows, placement = {}, {}, [], {}
    for family_index, domain in enumerate(short.DOMAINS):
        family, activity, permission, names, orders, states, past_object, proposal = domain
        queries[family] = copy.deepcopy(original['questions'][family + '0'])
        for side in (0, 1):
            pid = family + str(side)
            own = original['sources'][pid]
            entries = {s['id']: s for s in own['sources']}
            # Each decision role appears once at each recency rank across families.
            positions = {role: 5 + 6 * ((index + family_index) % 4) + side
                         for index, role in enumerate(('choice', 'past', 'order', 'commitment'))}
            active = {
                positions['choice']: ('u1', '同一许可范围的旧方案偏好到此撤销；从现在起按这条更正：'),
                positions['past']: ('u2', '核对原始登记后，更正那份临时转抄：'),
                positions['order']: ('u3', '执行记录也核过了，以这条纠正为准：'),
                positions['commitment']: ('u4', '关于刚才提出的新安排，我本人现在的答复是：'),
            }
            texts = [
                ('user', f'我在筹备{activity}，这次把报名、资料和现场工作陆续放在这里讨论。聊天里有未核对的草稿，也会有后续更正，请保留来龙去脉。场地的{permission}需要单独确认，不能拿借到其他东西或有人愿意帮忙来代替。'),
                ('assistant', entries['a1']['text'] + '还可以顺手整理签到纸、路线图和材料袋。我提出的这些办法先作为备选，不代表你已经答应。后续若有你自己的确认或更正，再以你自己的表述为依据。'),
                ('user', f'先记旧稿：{permission}已落实时，下次{activity}原来偏向“{names[1-side]}”。第一版执行转抄暂记“{orders[1-side]}”，还得回头核对原始登记。两者是不同对象，之后可能分别更正，别因为有一个“先”字就把方案全名当作已经执行过的顺序。'),
                ('user', f'{past_object}那一栏，手头临时转抄是“{states[1-side]}”，但我还没核对原始凭据，先标作待核。这里说的是那一次的事实记录，跟下次会选择哪套活动方案无关。等我查清楚会在这段聊天里单独更正，不直接拿草稿作最终结论。'),
            ]
            anchors = {}
            for number in range(5, 25):
                if number in active:
                    old_id, prefix = active[number]
                    texts.append(('user', prefix + entries[old_id]['text']))
                    anchors[old_id] = 'm%02d' % number
                else:
                    texts.append(CONTEXT[number - 5])
            pack = {'schema_version': 1, 'sources': [
                {'id': 'm%02d' % (i + 1), 'episode_id': 'long-trace', 'role': role, 'text': text}
                for i, (role, text) in enumerate(texts)]}
            sources[pid] = pack
            placement[pid] = positions
            for row in original['rows']:
                if row['profile'] != pid:
                    continue
                contract = copy.deepcopy(row['contract'])
                for anchor in contract['support']:
                    anchor['source_id'] = anchors[anchor['source_id']]
                short.authoring.validate(contract, pack)
                rows.append({'person': pid, 'case': row['case'], 'gold': contract['reference'],
                             'query_ids': row['query_ids'], 'personal_known': contract['reference'] != 'U',
                             'stratum': 'execution' if row['case'] == 'order' else 'untyped',
                             'task': contract['intent'], 'support': contract['support']})
    return {'sources': sources, 'queries': queries, 'rows': rows,
            'legacy_rows': copy.deepcopy(rows), 'disputed_rows': [],
            'design': {'kind': 'controlled_long_context_derivative', 'fictional_profiles': 8,
                       'dependent_template_families': 4, 'source_messages': 192,
                       'cases': 40, 'known': 28, 'unknown': 12,
                       'active_user_message_positions': placement,
                       'new_reference_labels_or_question_wording': False,
                       'independent_holdout': False, 'naturalistic_human_trajectories': False,
                       'placement_counterbalanced_by_role_not_sampled_from_real_histories': True,
                       'independent_semantic_acceptance': False}}
