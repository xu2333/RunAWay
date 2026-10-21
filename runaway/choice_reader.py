"""Identifiability reader contract with2–8 options; prepares no service calls."""
from datetime import date
from .card import canonical
from .choice_contract import IDENTIFIABLE

COVERAGE_CHECK = (
    '本次先核对记录的适用范围，再选择动作。逐题按以下顺序核对，不把核对过程写进答案：'
    '先列清本题条件与材料中条件的对应关系；只用材料明示的规则和同义等价的条件，不自行补一条更宽的偏好。'
    '特别注意：记录在某一个数值下的决定，不自动变成整个数值区间的规则；'
    '条件变得更安全、更便宜、更确定或看起来更有利，也不能据单调性推断这个人会沿用原决定。'
    '然后检查题面是否明确穷尽了若干个已记录情境：若是，分别保留每个情境的当前有效选择，'
    '只有它们全选同一做法时才能选该做法；如果选择不同，答案是U，不能替用户取最保守、最合理或最常见的一项。'
    '如果不是这种穷尽情形，只在本题条件确实落入某条记录规则的适用范围时迁移；否则答案是U。'
    '最后检查同条件的最新改口和具体例外。题材换名、同义改写、选项换位本身不是条件越界；'
    '已经覆盖而且有唯一选择的题必须给出该选择，不能因谨慎而一律U。')


def make_request(material,queries,*,as_of=None,answer_format="label",reader_mode="standard"):
    if type(material) is not str or type(queries) is not list or not queries:raise ValueError('Provide text material and queries')
    if as_of is not None:
        if type(as_of) is not str or date.fromisoformat(as_of).isoformat()!=as_of:raise ValueError('as_of must be YYYY-MM-DD')
    if answer_format not in ('label','text'):raise ValueError('answer_format must be label or text')
    if reader_mode not in ('standard','coverage'):raise ValueError('reader_mode must be standard or coverage')
    seen=set();properties={}
    for query in queries:
        if type(query) is not dict or set(query)!={'id','scenario','options'}:raise ValueError('Queries require id,scenario,options')
        qid=query['id'];options=query['options']
        if type(qid) is not str or not qid or qid in seen:raise ValueError('Query IDs must be unique')
        if type(query['scenario']) is not str or not query['scenario'].strip() or type(options) is not dict or not 2<=len(options)<=8:raise ValueError('Provide a scenario and2–8 options')
        labels=list('ABCDEFGH'[:len(options)])
        if list(options)!=labels or any(type(text) is not str or not text.strip() for text in options.values()):raise ValueError('Options must use consecutive labels A,B,..., with text')
        values=list(options.values()) if answer_format=='text' else labels
        if answer_format=='text' and (len(set(values))!=len(values) or 'U' in values):
            raise ValueError('Text answers require distinct option texts; U is reserved for unknown')
        seen.add(qid);properties[qid]={'type':'string','enum':values+['U']}
    schema={'type':'object','additionalProperties':False,'required':list(properties),'properties':properties}
    prefix=IDENTIFIABLE.replace('截至2026-04-01','' if as_of is None else '截至'+as_of,1).replace('A/B是本题两个选项','A、B等字母对应本题给定选项').replace('选择，所有题均可用U','选择，所有题均可用U').replace('到A/B/U的完整JSON','到本题选项字母或U的完整JSON')
    if answer_format=='text':
        prefix=prefix.replace('A、B等字母对应本题给定选项','A、B等字母只标记选项位置；答案应为所选做法的完整原文或U').replace('到本题选项字母或U的完整JSON','到所选做法完整原文或U的完整JSON')
        prefix+='不要返回选项字母；同一做法换位置时，答案原文不变。'
    if reader_mode=='coverage':prefix=COVERAGE_CHECK+'\n'+prefix
    return {'schema':schema,'prompt':prefix+'\nANSWER_SCHEMA_JSON:\n'+canonical(schema)+'\nREADER_INPUT_JSON:\n'+canonical({'material':material,'queries':queries})}


def decode_response(queries,answer,*,answer_format='label',allow_missing=False):
    """Validate raw choices and map exact public option text to its display label.

    This does not consult memory, gold, conditions or a preference policy. Missing
    answers stay missing when explicitly allowed for an incomplete-result audit.
    """
    schema=make_request('',queries,answer_format=answer_format)['schema']
    expected=set(schema['required'])
    if type(answer) is not dict or set(answer)-expected or (not allow_missing and set(answer)!=expected):
        raise ValueError('Missing or unexpected query keys')
    byid={query['id']:query for query in queries};result={}
    for qid,value in answer.items():
        if type(value) is not str or value not in schema['properties'][qid]['enum']:
            raise ValueError('Answer is not an exact offered choice or U; no repair')
        if answer_format=='label' or value=='U':result[qid]=value
        else:result[qid]=next(label for label,text in byid[qid]['options'].items() if text==value)
    return result
