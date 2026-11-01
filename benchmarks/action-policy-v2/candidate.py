"""Unmeasured source-only encoding guidance; original graph/compiler unchanged."""
import copy
import importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('action_policy_original_graph', HERE.parent / 'action-revision-graph-v1/candidate.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
VERSION = 'owned_action_policy_graph_v2'
SCHEMA = copy.deepcopy(base.SCHEMA)
SCHEMA['properties']['version']['enum'] = [VERSION]
GUIDANCE = '''补充编码约束（仍只依据本次来源）：
把“选择哪种做法”的完整核心名称与理由、义务说明、适用范围、期限、恢复条件及执行安排分清。来源已明确列出候选做法时，优先沿用它的完整称呼；后续确实出现新做法则保留新做法，不映射回过期候选。不要在action里附加履约理由、适用周或恢复后的规则，使一个已给出的选择看起来变成未列出的另一个选择。这些信息仍须完整留在自己的条件、对象/决策目标、既往事实或未知边界中。不能机械删除“先”或其他顺序词；若它区分做法或约束执行顺序，完整保留。
区分完整政策重述与同情境只改动作：当用户明确把通常规则和例外完整重述，并把政策推广到同类未来情况时，按该段自足的必要条件建立当前base；更早具体实例的背景不能自动升级成该政策的普遍门槛。不能仅因一句话较晚就假定它放宽所有原条件。只有明确的同情境动作改口才使用action_revision，继续由原编译器逐项继承父条件，尤其保留许可和授权前提。无法可靠区分则保留未知，不伪造放宽。
独立优先例外只保留例外自己必需的前提；不要把通常分支的可行性或设备状态自动带入例外。真正跨分支必要的条件仍保留。以上是提炼约束，不构成语义正确性的程序证明。'''


def make_request(sources, budget=1536):
    request = base.make_request(sources, budget)
    request['schema'] = copy.deepcopy(SCHEMA)
    request['prompt'] = GUIDANCE+'\n'+request['prompt']
    return request


def bind(answer, sources, budget=1536):
    base.b.check(answer, SCHEMA)
    normalized = copy.deepcopy(answer); normalized['version'] = base.VERSION
    files = base.bind(normalized, sources, budget)
    files['policy-encoder.private.json'] = {'version': VERSION, 'answer': copy.deepcopy(answer),
                                          'semantic_guidance_verified': False}
    return files
