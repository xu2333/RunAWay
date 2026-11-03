"""Unmeasured source-only coverage guidance; original wire and compiler retained."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('object_coverage_original', HERE.parent / 'source-order-v3/candidate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
VERSION, SCHEMA = base.VERSION, base.SCHEMA
METHOD_ID = 'object-coverage-guidance-v1'
GUIDANCE = '''补充来源覆盖核对（不增加新偏好）：
先逐一核对全部用户来源里的独立范围、对象及其当前已确认选择，再组织对象表和节点。只在对象表、name或tagline提到一个范围，不等于已保存该范围的选择；不要写完第一个范围就结束。
对每个来源支持的已知决策范围，保留与相应对象、问题相连的明确选择和必要条件；对象彼此独立时，即使动作相似，也不能只给其中一个对象写节点。删除对象条目或重复堆节点都不等于来源覆盖。
未决条件、撤回的完整性保证、候选讨论和助手建议继续按原指导处理，不为了凑节点把未知变成已知；没有已知选择的对象允许保留未知边界。预算不足时先精炼重复措辞，不能静默丢掉整个有已知选择的范围；命名和标语不能代替决策内容。提交前对照全部用户来源复核，而不是只核对自己已列出的对象表。'''


def make_request(sources, budget=1536):
    request = base.make_request(sources, budget)
    request['prompt'] = GUIDANCE + '\n' + request['prompt']
    return request


bind = base.bind
