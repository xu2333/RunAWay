"""Identifiability reader contract with2–8 options; prepares no service calls."""
from datetime import date
from .card import canonical
from .choice_contract import IDENTIFIABLE


def make_request(material,queries,*,as_of=None):
    if type(material) is not str or type(queries) is not list or not queries:raise ValueError('Provide text material and queries')
    if as_of is not None:
        if type(as_of) is not str or date.fromisoformat(as_of).isoformat()!=as_of:raise ValueError('as_of must be YYYY-MM-DD')
    seen=set();properties={}
    for query in queries:
        if type(query) is not dict or set(query)!={'id','scenario','options'}:raise ValueError('Queries require id,scenario,options')
        qid=query['id'];options=query['options']
        if type(qid) is not str or not qid or qid in seen:raise ValueError('Query IDs must be unique')
        if type(query['scenario']) is not str or not query['scenario'].strip() or type(options) is not dict or not 2<=len(options)<=8:raise ValueError('Provide a scenario and2–8 options')
        labels=list('ABCDEFGH'[:len(options)])
        if list(options)!=labels or any(type(text) is not str or not text.strip() for text in options.values()):raise ValueError('Options must use consecutive labels A,B,..., with text')
        seen.add(qid);properties[qid]={'type':'string','enum':labels+['U']}
    schema={'type':'object','additionalProperties':False,'required':list(properties),'properties':properties}
    prefix=IDENTIFIABLE.replace('截至2026-04-01','' if as_of is None else '截至'+as_of,1).replace('A/B是本题两个选项','A、B等字母对应本题给定选项').replace('选择，所有题均可用U','选择，所有题均可用U').replace('到A/B/U的完整JSON','到本题选项字母或U的完整JSON')
    return {'schema':schema,'prompt':prefix+'\nANSWER_SCHEMA_JSON:\n'+canonical(schema)+'\nREADER_INPUT_JSON:\n'+canonical({'material':material,'queries':queries})}
