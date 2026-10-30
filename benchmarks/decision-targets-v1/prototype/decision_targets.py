"""Unmeasured source-only candidate. No backend, decoder or default switch."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE_FILE = ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py'
spec = importlib.util.spec_from_file_location('decision_targets_scope_base', BASE_FILE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
REVISION = 'decision-target-instructions-v1'
RULES = '''\nDECISION_TARGET_REVISION_V1\n
先从来源识别每个用户断言在回答什么决策问题。偏好或方案选择、执行许可、已发生状态不是同一个问题；即使涉及同一对象、同一时间，也不能把它们当作互斥选择。用现有group.scope简短写清本组回答的问题及共有适用范围，不新增schema字段、标签词典或解码器。
公开组须保留不同决策问题的区分。用户已经选定的方案与尚不允许执行该方案可以同时成立；后者不能自动撤销前者，前者也不授予执行许可。仍需保留有来源依据的拒绝、等待和授权边界，不把它们从公开卡中删除或只留私有锚点。
受现有组数或字符预算约束而共用同一对象范围时，scope只写真正共有条件，每条when要明确自己回答的决策问题；仅问题和适用条件都相同的行才可能相互冲突。不能通过省略问题区分来节省字符，也不能超过原12组上限或删掉真实限制。
不要机械移走所有看似许可或等待的条件。如果用户把某项确认、许可或限制明确作为选择本身的必要前提，保留在该选择规则内。来源没说明两个问题是否独立时，不自行拆分成已知选择，也不把未知许可补成允许或拒绝。
同优先级冲突、例外优先和局部改口都要在同一实际决策问题及适用情境内核对。不能靠改组名、便签编号、措辞或记录先后把同一问题的真实冲突隐藏掉；另一问题的较晚状态不自动覆盖仍有效的选择。
仅把用户明确选择或背书绑定为决策证据。助手建议、工具状态和机器默认值不补偏好或授权；保留旧规则的必要条件、未覆盖分支和未知边界，不整体放松弃权。原schema、字段长度、公开头部、指南、渲染器及整卡字符预算均不变。
只基于输入来源组织这些问题，不根据外部题目、选项、得分、参考或旧卡决定分组。\nEND_DECISION_TARGET_REVISION_V1\n'''


def make_request(sources, budget=1536):
    request = base.make_request(sources, budget)
    marker = '\nEXTRACTION_INPUT_JSON:\n'
    prefix, body = request['prompt'].split(marker, 1)
    return {'schema': request['schema'], 'prompt': prefix + RULES + marker + body}


def bind(answer, sources, budget=1536):
    return base.bind(answer, sources, budget)
