"""Unmeasured budget-aware encoder request; wire and compiler stay unchanged."""
import copy
import importlib.util
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('budgeted_table_wire', HERE.parent / 'owned-object-table-v1/candidate.py')
table = importlib.util.module_from_spec(spec)
spec.loader.exec_module(table)
VERSION, SCHEMA = table.VERSION, copy.deepcopy(table.SCHEMA)
REQUEST_VERSION = 'budgeted-object-table-encoder-v1'
expand, bind = table.expand, table.bind
GUIDANCE = '''本次编码器能看到最终整卡字符上限与固定公开前缀。预算包括name、tagline、guide、所有范围/条件/动作，以及可能内嵌的无损词典；私有引用和对象索引不是公开解码器，不得靠它们代替公开语义。
先完整恢复每条规则的条件归属，再用自足的短语表达。question只标识所问的决策目标与层次，例如字号、字体、接口方案、执行许可；不要把通常/例外/触发条件或完整问句重复塞进question。同一对象同一决策目标的各分支复用相同question，触发条件只放在各行requires。不同目标仍须区分，不能把字号与字体、方案选择与执行许可混成竞争动作。
对象名称和条件采用短而明确的自然语言，保留必要对象、否定、时间、用途、数值、受众及可逆性；不要重复“用户会”“今后的安排是”等无新增语义的套话。不能靠删除约束、遗漏规则、合并不同动作、伪造优先级或将未知改为已知来满足预算。有意义的顺序限制也不得抹去。
程序会按对象分组，把共同条件与行内剩余条件分别渲染；每行还会加“所问为”及question。无需在question和action里重述requires。只生成合法wire，不报告或伪造字符计数。若仍无法装入上限，保留完整语义，最终由原binder报告失败；不截断、不修卡。'''


def make_request(sources, budget=1536):
    if type(budget) is not int or budget <= 0:
        raise ValueError('Budget must be a positive integer')
    request = table.make_request(sources)
    prefix, body = request['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n', 1)
    prefix = prefix.replace('不做共享scope，不因最终卡的字符预算遗漏规则或缩写条件。',
                            '不做共享scope；不得因预算遗漏规则或改变必要条件，采用自足短语表达。')
    value = json.loads(body)
    value.update(budget_characters=budget, fixed_header=table.base.grouped.HEADER,
                 fixed_guide=table.base.grouped.GUIDE)
    return {'schema': copy.deepcopy(SCHEMA), 'prompt': prefix + '\n' + GUIDANCE +
            '\nSOURCE_LEDGER_INPUT_JSON:\n' + table.base.canonical(value)}
