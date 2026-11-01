"""Unmeasured private object-table wire candidate; public names expand fully."""
import copy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('owned_table_base', HERE.parent / 'owned-conditions-v1/candidate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
VERSION = 'owned-object-table-v1'
fields = {'object_index': {'type': 'integer', 'minimum': 0, 'maximum': 11}}
fields.update({k: copy.deepcopy(v) for k, v in base.ROW['properties'].items() if k != 'object'})
SCHEMA = base.obj({'version': {'type': 'string', 'enum': [VERSION]}, 'name': base.txt(20), 'tagline': base.txt(60),
    'objects': base.arr(base.txt(40), 0, 12), 'rows': base.arr(base.obj(fields), 0, 30),
    'unknowns': base.arr(base.txt(160), 1, 4)})
WIRE = '''本次返回object-table wire：version=owned-object-table-v1。objects为最多12个独立对象/类目的自然语言名称，名称不夹带条件，不重复；rows总计最多30行，每行用从0开始的object_index引用表中已存在的对象，不再输出object字段。同一对象的不同决策问题用question区别；条件仍属于每一行，不能挂到objects上或因共用对象而继承给例外。独立恢复所有有效承诺，不为缩小类目数删除行、合并动作或伪造优先关系。没有用户决策时objects及rows可空。私有索引仅作结构引用，公开卡会完整展开自然语言名称，不用索引、外部字典或测试题代替含义。最终整卡预算由程序处理，输入没有题目、旧卡或反馈。'''


def make_request(sources):
    request = base.make_request(sources)
    prefix, body = request['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n', 1)
    return {'schema': copy.deepcopy(SCHEMA),
            'prompt': prefix + '\n' + WIRE + '\nSOURCE_LEDGER_INPUT_JSON:\n' + body}


def expand(answer):
    base.check(answer, SCHEMA)
    objects = answer['objects']
    for name in objects:
        base.grouped.string(name, 'object', 40)
    if len(set(objects)) != len(objects):
        raise ValueError('Duplicate object name')
    rows = []
    for row in answer['rows']:
        index = row['object_index']
        if index >= len(objects):
            raise ValueError('Undefined object index')
        rows.append({'object': objects[index], **{k: copy.deepcopy(v) for k, v in row.items() if k != 'object_index'}})
    return {'version': base.VERSION, 'name': answer['name'], 'tagline': answer['tagline'],
            'rows': rows, 'unknowns': copy.deepcopy(answer['unknowns'])}


def bind(answer, sources, budget=1536):
    ledger = expand(answer)
    files = base.bind(ledger, sources, budget)
    files['object-table.private.json'] = {'version': VERSION, 'wire_answer': copy.deepcopy(answer),
        'all_public_object_names_expanded': True, 'annotation_semantics_verified': False}
    return files
