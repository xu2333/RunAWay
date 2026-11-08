"""Experimental initial extraction with deterministic whole-source quotation anchors.

No inference transport, default promotion or semantic-coverage certification.
"""
import copy
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('initial_id_alias_base',HERE.parent/'scope-alias-encoding-v1/candidate.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
b=base.b
VERSION='scope_alias_source_id_graph_v1'
GUIDANCE='''本协议覆盖下文所有quote输出约定：所有证据锚点只输出{"source_id":"本次来源ID"}，不要输出quote或改写引文。程序按ID取该条完整原文，并原样交给旧校验器；原文过长、来源角色不符、名字或动作不在对应来源、关系不成立的结构等仍会失败，不能借ID规避旧约束。
source_id只能从本次sources中选。用户直接选择、指代背书、改口、上下文、条件、别名证据和双向source_accounting关联继续遵循原规则。ID存在并不证明语义正确：候选定义不是已选动作，否认同一关系不是改名；每个关系仍须有同一用户消息同时包含两名字。不把助手、工具或外部例句当作用户确认。
完整来源只用于私有证据重建，不附给读卡器，不变成额外公开记忆；公开预算、完整条件、优先级、未知边界、编译器与读卡器保持不变。仍从本人的来源独立提炼，不读取题目、参考、旧卡、旧响应或其他生成。'''


def _anchor(schema):
    return isinstance(schema,dict) and schema.get('type')=='object' and set(schema.get('properties',{}))=={'source_id','quote'}


def _reference_schema(schema, ids):
    if _anchor(schema):
        return b.obj({'source_id':{'type':'string','enum':list(ids)}})
    if isinstance(schema,dict):
        return {k:_reference_schema(v,ids) if isinstance(v,(dict,list)) else v for k,v in schema.items()}
    if isinstance(schema,list):return [_reference_schema(v,ids) if isinstance(v,(dict,list)) else v for v in schema]
    return schema


def schema(sources):
    original=base.schema(sources)
    result=_reference_schema(original,[s['id']for s in sources['sources']])
    result['properties']['version']['enum']=[VERSION]
    return result


def make_request(sources,budget=1536):
    request=base.make_request(sources,budget)
    request['schema']=schema(sources)
    request['prompt']=GUIDANCE+'\n'+request['prompt']
    return request


def _expand(value,original,index,ids):
    # Follow the typed schema, not arbitrary dict shape: a source legitimately
    # named 'source_id' in source_accounting is not an evidence anchor.
    if _anchor(original):
        return dict(source_id=value['source_id'],quote=index[value['source_id']]['text'])
    if 'anyOf'in original:
        for branch in original['anyOf']:
            try:b.check(value,_reference_schema(branch,ids))
            except ValueError:continue
            return _expand(value,branch,index,ids)
        raise ValueError('No allowed reference schema alternative')
    if original.get('type')=='object':
        return {k:_expand(v,original['properties'][k],index,ids)for k,v in value.items()}
    if original.get('type')=='array':
        return [_expand(v,original['items'],index,ids)for v in value]
    return copy.deepcopy(value)


def resolve(answer,sources):
    b.validate_sources(sources)
    b.check(answer,schema(sources))
    index={s['id']:s for s in sources['sources']}
    legacy=_expand(answer,base.schema(sources),index,list(index))
    legacy['version']=base.VERSION
    # Retain all original string limits and strict structure after expansion;
    # no truncation, inferred source, repaired name or relaxed guard.
    b.check(legacy,base.schema(sources))
    return legacy


def bind(answer,sources,budget=1536):
    legacy=resolve(answer,sources)
    files=base.bind(legacy,sources,budget)
    files['source-id-initial.private.json']=dict(
        version=VERSION,answer=copy.deepcopy(answer),resolved_graph=legacy,
        exact_whole_source_reconstruction_checked=True,
        source_reference_semantics_verified=False,source_completeness_verified=False,
        behavioral_fidelity_verified=False,production_default_changed=False)
    return files
