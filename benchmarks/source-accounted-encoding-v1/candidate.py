"""Source-accounted encoding candidate; semantic classification remains unverified."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('accounted_original_encoder', ROOT / 'benchmarks/object-coverage-guidance-v1/candidate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
b = base.base.b
VERSION = 'source_accounted_graph_v1'
GUIDANCE = '''先逐条恢复观察，再总结可推导规则：
source_accounting必须逐一包含本次所有user消息的ID。每条填kind、node_ids和仅依据该消息及上下文的reason，不把助手/工具当作用户确认。
kind=direct_choice：该用户消息直接写出了本人选择、政策或已发生事实，逐项保留为自己的节点；动作完整原文须出现在该消息的decision引文中。kind=contextual_choice：该消息确实背书了前文但动作只靠上下文才能解析，节点仍用本消息作decision证据，完整前提和动作定义另引上下文。只有省略/指代确认才用此类，不能为了绕开直接引文核对把显式选择改标为contextual_choice。
kind=no_choice：本消息只定义候选/条件、撤回完整性保证、尚未决定或提供背景，没有新的直接选择；node_ids为空，reason说清为何。撤回“候选集合完整”不撤回此前已确认的个别选择，未知只保留到真正未定的组合。
每个观察节点的每条decision来源都必须在source_accounting里明确关联该节点；直接选择分别核对自己的动作引文。不同消息的相反动作不能合并成一个观察节点的共同背书。同一完整条件和同一动作的再次确认可关联同一节点，避免复制重复规则；不同条件下的选择必须分别保留，不因对象表已有名称就省掉其选择。先按原时间顺序恢复这些观察和同条件改口，再压缩共享范围。
跨消息推导出的规则另外建节点并在derived_node_ids列出，证据仍来自原用户来源。推导节点不能代替逐项保留的直接观察，也不能用候选定义冒充已选定候选。每个nodes成员要么被观察条目关联，要么在derived_node_ids里，不能两者兼有；不允许未交代的节点。程序验证关联、字面动作见证与原图约束，不证明你对消息的语义分类或推导正确。
unknowns只写用户来源中实际未决/不适用的边界。“尚未编码、未完整覆盖、生成器没处理”是提炼失败，不是用户未知；已确认的选择不能移进unknowns来省节点。若预算困难，先精炼命名和重复条件，不能假装用户没决定。公开编译、条件继承、事实/许可/选择区分、顺序注释与完整字符上限均保持原规则。输出完整候选，不输出补丁，不看任何题目、参考或旧卡。'''


def schema(sources):
    b.validate_sources(sources)
    item = b.obj({'kind': {'type': 'string', 'enum': ['direct_choice', 'contextual_choice', 'no_choice']},
                  'node_ids': b.arr(b.txt(96), 0, 60), 'reason': b.txt(160)})
    result = copy.deepcopy(base.SCHEMA)
    result['properties']['version']['enum'] = [VERSION]
    result['properties']['source_accounting'] = b.obj({s['id']: copy.deepcopy(item)
                                                     for s in sources['sources'] if s['role'] == 'user'})
    result['properties']['derived_node_ids'] = b.arr(b.txt(96), 0, 60)
    result['required'] += ['source_accounting', 'derived_node_ids']
    return result


def make_request(sources, budget=1536):
    request = base.make_request(sources, budget)
    request['schema'] = schema(sources)
    request['prompt'] = GUIDANCE + '\n' + request['prompt']
    return request


def normalize(answer, sources):
    b.check(answer, schema(sources))
    nodes = {node['id']: node for node in answer['nodes']}
    if len(nodes) != len(answer['nodes']):
        raise ValueError('Duplicate node ID')
    owners = {}
    for sid, entry in answer['source_accounting'].items():
        ids = entry['node_ids']
        if len(set(ids)) != len(ids) or ((entry['kind'] == 'no_choice') != (not ids)):
            raise ValueError('Source disposition and observed nodes disagree')
        for node_id in ids:
            if node_id not in nodes:
                raise ValueError('Observed node missing')
            node = nodes[node_id]
            witnesses = [anchor for anchor in node['decisions'] if anchor['source_id'] == sid]
            if not witnesses:
                raise ValueError('Observed source has no corresponding decision witness')
            if entry['kind'] == 'direct_choice' and not any(node['action'] in anchor['quote'] for anchor in witnesses):
                raise ValueError('Direct action has no literal witness in its owner decision quote')
            owners.setdefault(node_id, []).append(sid)
    for node_id, supporters in owners.items():
        if {a['source_id'] for a in nodes[node_id]['decisions']} != set(supporters):
            raise ValueError('Observation has unaccounted decision sources')
    derived = answer['derived_node_ids']
    if len(set(derived)) != len(derived) or set(derived) & set(owners) or set(derived) | set(owners) != set(nodes):
        raise ValueError('Observed and derived nodes must partition the entire graph')
    normalized = copy.deepcopy(answer)
    normalized.pop('source_accounting')
    normalized.pop('derived_node_ids')
    normalized['version'] = base.VERSION
    return normalized, owners


def bind(answer, sources, budget=1536):
    normalized, owners = normalize(answer, sources)
    # Use the original binder unchanged: roles, literal quotations, conditions,
    # revisions, status/order constraints and whole-public budget still apply.
    files = base.bind(normalized, sources, budget)
    files['source-accounting.private.json'] = {
        'version': VERSION, 'answer': copy.deepcopy(answer), 'observed_node_supporters': owners,
        'every_user_message_classified': True, 'node_partition_verified': True,
        'direct_action_literal_witness_checked': True,
        'source_semantic_classification_verified': False, 'source_completeness_verified': False,
        'behavioral_fidelity_verified': False, 'normalized_graph': normalized}
    return files
