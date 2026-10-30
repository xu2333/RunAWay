"""Build disclosed fictional development truth, not a model benchmark result."""
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway import grouped_support as grouped

sources = []
rules = []


def source(sid, episode, role, text):
    sources.append({'id': sid, 'episode_id': episode, 'role': role, 'text': text})


def rule(rid, target, sid, value, requires=None, priority=0, supersedes=None):
    text = next(s['text'] for s in sources if s['id'] == sid)
    rules.append({'id': rid, 'target': target, 'source_id': sid, 'quote': text,
                  'value': value, 'requires': requires or {}, 'priority': priority,
                  'supersedes': supersedes or []})


source('s1', 'bag', 'user', '只说这次周末帆布包选款，我之前选灰色帆布包。')
rule('bag_old', 'bag_choice', 's1', '灰色帆布包', {'this_bag': True})
source('s2', 'bag', 'user', '这次周末帆布包改选蓝色帆布包，之前的灰色选择作废；改动只限选款。')
rule('bag_now', 'bag_choice', 's2', '蓝色帆布包', {'this_bag': True}, supersedes=['bag_old'])
source('s3', 'bag', 'user', '这笔订单在尺寸尚未核对时，先存草稿，暂不下单。没有说核对后就自动授权下单。')
rule('bag_wait', 'bag_execution', 's3', '先存草稿，暂不下单', {'size_pending': True})
source('s4', 'bag', 'assistant', '我建议选灰色帆布包，并直接下单；这两项建议都没获用户认可。')
rule('assistant_bag', 'bag_choice', 's4', '灰色帆布包', {'this_bag': True}, priority=9)
rule('assistant_order', 'bag_execution', 's4', '直接下单', {'size_pending': True}, priority=9)
source('s5', 'bag', 'tool', '界面默认选款显示灰色帆布包，下单按钮已自动勾选直接下单；不是用户决定。')
rule('tool_bag', 'bag_choice', 's5', '灰色帆布包', {'this_bag': True}, priority=8)
rule('tool_order', 'bag_execution', 's5', '直接下单', {'size_pending': True}, priority=8)
source('s6', 'lamp', 'user', '这盏书桌台灯在晚上读纸书时选暖光，我认可这项安排。')
rule('lamp_warm', 'lamp_choice', 's6', '暖光', {'paper_reading': True})
source('s7', 'lamp', 'user', '同一盏灯、同样晚上读纸书的条件下，我也认可选冷光；没有撤销暖光安排或排优先级，现在还没定。')
rule('lamp_cold', 'lamp_choice', 's7', '冷光', {'paper_reading': True})
source('s8', 'poster', 'user', '这次室内海报只有确认墨水耐光时才选海蓝色；检测结果缺失或不耐光时，我没有定选色。')
rule('poster', 'poster_choice', 's8', '海蓝色', {'lightfast_confirmed': True})
source('s9', 'discussion', 'user', '这轮讨论只考虑会议室可用或不可用两种情况。可用时选先发书面意见。')
rule('discussion_room', 'discussion_choice', 's9', '先发书面意见', {'room_available': True})
source('s10', 'discussion', 'user', '同一轮讨论，会议室不可用时也选先发书面意见。这两个分支都已决定。')
rule('discussion_no_room', 'discussion_choice', 's10', '先发书面意见', {'room_available': False})
source('s11', 'walk', 'user', '这次小区散步只考虑下雨或不下雨：下雨时走连廊，不下雨时走园径。没有别的候选情境。')
rule('walk_rain', 'walk_choice', 's11', '走连廊', {'raining': True})
rule('walk_dry', 'walk_choice', 's11', '走园径', {'raining': False})
source('s12', 'sample', 'user', '这次样书快递的交付地点选楼下服务台。这个选择本身已经定了。')
rule('sample_place', 'sample_choice', 's12', '楼下服务台', {'this_sample': True})
source('s13', 'sample', 'user', '这次样书快递，收件地址未确认时先存草稿；没有说明确认后就可以自动寄出。')
rule('sample_wait', 'sample_execution', 's13', '先存草稿', {'address_pending': True})
source('s14', 'wall', 'user', '展示墙的蓝底和灰底都允许做样片，选款还没决定；施工安排只做样片，暂不搭建。')
rule('wall_prototype', 'wall_execution', 's14', '只做样片，暂不搭建')

queries = []


def query(qid, target, facts, scenario, a, b, expected, stratum):
    queries.append({'public': {'id': qid, 'scenario': scenario, 'options': {'A': a, 'B': b}},
                    'target': target, 'facts': facts, 'expected': expected, 'stratum': stratum})


query('q01', 'bag_choice', {'this_bag': True}, '这次周末帆布包目前选了哪款？', '蓝色帆布包', '灰色帆布包', '蓝色帆布包', 'preference')
query('q02', 'bag_execution', {'size_pending': True}, '这笔帆布包订单的尺寸尚未核对，现在怎样处理？', '先存草稿，暂不下单', '直接下单', '先存草稿，暂不下单', 'execution')
query('q03', 'bag_execution', {'size_pending': False}, '这笔帆布包订单尺寸已经核对，记录是否确定下一步处理？', '先存草稿，暂不下单', '直接下单', 'U', 'execution')
query('q04', 'poster_choice', {}, '这次室内海报，墨水检测尚未有结果，选什么颜色？', '海蓝色', '浅米色', 'U', 'preference')
query('q05', 'poster_choice', {'lightfast_confirmed': True}, '这次室内海报墨水已确认耐光，选什么颜色？', '海蓝色', '浅米色', '海蓝色', 'preference')
query('q06', 'lamp_choice', {'paper_reading': True}, '同一盏书桌台灯，晚上读纸书，按现有安排选什么光？', '暖光', '冷光', 'U', 'preference')
query('q07', 'discussion_choice', {}, '这轮讨论尚未确认会议室能否使用，采用哪种沟通方式？', '先发书面意见', '先开语音讨论', '先发书面意见', 'preference')
query('q08', 'discussion_choice', {'room_available': False}, '这轮讨论会议室不可用，采用哪种沟通方式？', '先发书面意见', '先开语音讨论', '先发书面意见', 'preference')
query('q09', 'walk_choice', {}, '这次小区散步天气尚未确认，会选哪条路线？', '走园径', '走连廊', 'U', 'preference')
query('q10', 'walk_choice', {'raining': True}, '这次小区散步已经确定下雨，选哪条路线？', '走园径', '走连廊', '走连廊', 'preference')
query('q11', 'sample_choice', {'this_sample': True}, '这次样书快递的交付地点选哪里？', '楼下服务台', '门口快递柜', '楼下服务台', 'preference')
query('q12', 'sample_execution', {'address_pending': True}, '这次样书快递地址还没确认，订单怎样处理？', '先存草稿', '直接寄出', '先存草稿', 'execution')
query('q13', 'sample_execution', {'address_pending': False}, '这次样书快递地址已经确认，是否已有明确的寄出安排？', '先存草稿', '直接寄出', 'U', 'execution')
query('q14', 'wall_choice', {}, '展示墙目前更偏好哪种底色？', '蓝底', '灰底', 'U', 'preference')
query('q15', 'wall_execution', {}, '展示墙当前的制作安排是什么？', '只做样片，暂不搭建', '直接搭建', '只做样片，暂不搭建', 'execution')
query('q16', 'shoe_choice', {}, '新的徒步鞋选款目前选了哪款？', '低帮鞋', '高帮鞋', 'U', 'preference')

packet = {'kind': 'authored_decision_target_development_not_holdout',
          'sources': {'schema_version': 1, 'sources': sources}, 'rules': rules, 'queries': queries,
          'facts_and_targets_are_author_annotations_not_NLU': True,
          'real_model_performance_measured': False, 'independent_semantic_acceptance': False}


def anchor(sid):
    return {'source_id': sid, 'quote': next(s['text'] for s in sources if s['id'] == sid)}


answer = {'name': '不抢单的小团子', 'tagline': '颜色我选好了，下单等你点头。',
          'groups': [
              {'scope': '这次周末帆布包的选款', 'contexts': [anchor('s1')],
               'rules': [{'when': '决定颜色', 'choose': '蓝色帆布包', 'priority': 0,
                          'decisions': [anchor('s2')], 'contexts': [anchor('s1')], 'supersedes': ['s1']}]},
              {'scope': '同一帆布包订单的执行安排', 'contexts': [anchor('s3')],
               'rules': [{'when': '尺寸尚未核对', 'choose': '先存草稿，暂不下单', 'priority': 0,
                          'decisions': [anchor('s3')], 'contexts': [anchor('s3')], 'supersedes': []}]},
          ], 'unknowns': ['尺寸核对后的下单安排及其它未记录选择仍未知。']}


def main():
    files = grouped.bind(answer, packet['sources'], 1536)
    compact = copy.deepcopy(answer)
    compact['groups'] = [{'scope': '这次周末帆布包', 'contexts': [anchor('s1'), anchor('s3')],
                          'rules': [copy.deepcopy(answer['groups'][0]['rules'][0]), copy.deepcopy(answer['groups'][1]['rules'][0])]}]
    compact['groups'][0]['rules'][0]['when'] = '所问为选款'
    compact['groups'][0]['rules'][1]['when'] = '所问为执行安排，尺寸尚未核对'
    compact_files = grouped.bind(compact, packet['sources'], 1536)
    outputs = {'development.synthetic.json': packet, 'examples/partial-answer.synthetic.json': answer,
               'examples/partial-answer-compact.synthetic.json': compact}
    for filename, value in outputs.items():
        (HERE / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (HERE / 'examples/partial-card.txt').write_text(files['prompt.md'], encoding='utf-8')
    (HERE / 'examples/partial-card-compact.txt').write_text(compact_files['prompt.md'], encoding='utf-8')
    (HERE / 'development.synthetic.sha256').write_text(hashlib.sha256((HERE / 'development.synthetic.json').read_bytes()).hexdigest() + '\n')
    print(json.dumps({'sources': len(sources), 'queries': len(queries),
                      'partial_example_characters': len(files['prompt.md']),
                      'compact_example_characters': len(compact_files['prompt.md']), 'model_calls': 0}))


if __name__ == '__main__':
    main()
