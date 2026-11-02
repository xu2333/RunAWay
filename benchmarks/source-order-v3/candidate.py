"""Unmeasured model-generated order annotations;no manually selected source rows."""
import copy
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


policy=load('source_order_policy',HERE.parent/'action-policy-v2/candidate.py')
projection=load('source_order_projection',HERE.parent/'order-targets-v1/prototype.py')
graph=policy.base
b=graph.b
VERSION='source_order_annotation_graph_v3'
SPLIT=b.obj({k:copy.deepcopy(v) for k,v in projection.BINDING['properties'].items() if k!='row_index'})
SCHEMA=copy.deepcopy(policy.SCHEMA)
SCHEMA['properties']['version']['enum']=[VERSION]
for node in SCHEMA['properties']['nodes']['items']['anyOf']:
    node['properties']['order_split']={'anyOf':[{'type':'null'},copy.deepcopy(SPLIT)]}
    node['required'].append('order_split')
GUIDANCE='''额外输出order_split字段，每个节点都必须有；通常为null，status节点必须为null。本版在这个窄类型上按本段字段分工：完整表述留在action，核心名称填order_split，不在action中预先规范化；其它旧指导照用。
action仍完整保留来源中有意义的原动作及顺序词，不在action里悄悄删词。只有来源明确提供了独立的方法候选名称，而后续完整动作恰为“先”加该完整方法名时，才可标注order_split：core_action填该来源候选的完整名称，core_evidence给逐字候选定义锚点，execution_question用独立且不与原决策/事实冲突的执行先后目标名。编译器会在原选择目标使用核心方法，并在另一个目标逐字保留完整原动作和全部原条件。
如果“先”本身属于来源给出的候选方法名，不把它剥掉另造名称；无独立候选证据、没有可分离的先后含义、不满足这个窄语法或无法可靠判断时order_split为null。不能依据任何外部题目或想象的选项造标签。不能伪造独立候选、去掉否定/许可条件或把执行安排说成已经实施。
仅对当前仍有效的choice节点进行拆分，最多4个；被替代动作的表示注释不继承到新动作。原action_revision的条件继承和其它事实保留规则不变。注释由你从本次来源生成，程序只核对字面引用/前缀/结构，不证明语义归类正确。'''


def make_request(sources,budget=1536):
    req=policy.make_request(sources,budget);req['schema']=copy.deepcopy(SCHEMA)
    req['prompt']=GUIDANCE+'\n'+req['prompt']
    return req


def bind(answer,sources,budget=1536):
    b.check(answer,SCHEMA)
    b.validate_sources(sources)
    source_index={s['id']:(i,s) for i,s in enumerate(sources['sources'])}
    normalized=copy.deepcopy(answer);normalized['version']=graph.VERSION
    annotations={}
    for node in normalized['nodes']:
        annotation=node.pop('order_split')
        if node['id'] in annotations:raise ValueError('Duplicate annotation node')
        if node.get('target_kind')=='status' and annotation is not None:raise ValueError('Past status cannot be decomposed')
        if annotation is not None:
            b.grouped._anchors(annotation['core_evidence'],source_index)
            core=b.grouped.string(annotation['core_action'],'source-offered core',80)
            if node['action']!='先'+core or not any(core in a['quote'] for a in annotation['core_evidence']):
                raise ValueError('Annotation must retain a source-bound complete ordered action')
        annotations[node['id']]=annotation
    ledger,trace=graph.compile_graph(normalized,sources)
    bindings=[]
    for index,node_id in enumerate(trace['active_node_ids']):
        if annotations[node_id] is not None:bindings.append({'row_index':index,**annotations[node_id]})
    files=projection.bind(ledger,sources,bindings,budget) if bindings else graph.dense.bind(ledger,sources,budget)
    if bindings:
        files['decomposition.private.json'].update(developer_annotation_not_model_inference=False,model_generated_annotation=True)
    files['summary.private.json'].update(model_generated_annotation=True,
        developer_annotation_not_model_inference=False,active_order_splits=len(bindings),
        semantic_decomposition_independently_accepted=False)
    files['source-order.private.json']={'version':VERSION,'answer':copy.deepcopy(answer),'bindings':bindings,
        'trace':trace,'original_ledger':ledger,'semantic_action_assignment_verified':False,
        'full_ordered_actions':[ledger['rows'][x['row_index']]['action'] for x in bindings]}
    return files


def erase_order_targets(files,budget=1536):
    """Remove designated generated execution rows only;never edit choices/guards.

    Eligibility checks literal absence,not semantic erasure of paraphrases.
    A missing/contaminated split is ineligible,not repaired or replaced.
    """
    annotation=files['source-order.private.json'];bindings=annotation['bindings']
    if not bindings:return {'eligible':False,'reason':'no_active_generated_order_split'}
    value=graph.dense.parse(files['prompt.md']);before=copy.deepcopy(value)
    _,plans=b.project(annotation['original_ledger'],files['profile.private.json']['sources'])
    removed=[]
    for binding in bindings:
        gi=next(i for i,p in enumerate(plans) if any(m['index']==binding['row_index'] for m in p['members']))
        rules=value['groups'][gi]['rules'];matches=[i for i,r in enumerate(rules) if r['question']==binding['execution_question']]
        if len(matches)!=1:raise ValueError('Generated execution target not unique')
        removed.append(rules.pop(matches[0]))
    expanded=graph.dense._render(value)
    text,_=graph.dense.pack(expanded,budget,prefix=graph.dense.prefix(value))
    if any(action in graph.dense.decode(text) for action in annotation['full_ordered_actions']):
        return {'eligible':False,'reason':'ordered_literal_remains_outside_designated_targets'}
    # Independently restore removed rows to compare the whole public projection.
    # Removal itself uses target identity;choice rows/guards are untouched.
    for gi,group in enumerate(value['groups']):
        expected=[r for r in before['groups'][gi]['rules'] if r['question'] not in
                  {x['execution_question'] for x in bindings if any(m['index']==x['row_index'] for m in plans[gi]['members'])}]
        if group['scope']!=before['groups'][gi]['scope'] or group['rules']!=expected:raise ValueError('Damage changed a non-target field')
    return {'eligible':True,'prompt':text,'characters':len(text),'removed_execution_rows':removed,
        'ordered_literals_absent':True,'semantic_erasure_proven':False,'new_source_preference_gold':False}
