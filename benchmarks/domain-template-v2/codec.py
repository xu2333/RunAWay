"""Lift an exact per-row nonnegative-integer domain into a counted guide.

Narrow syntax only:no source inference,graph edits,repair or model backend.
"""
import copy
import importlib.util
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('domain_template_previous_codec',HERE.parents[1]/'scripts/replay_guard_pressure.py')
v1=importlib.util.module_from_spec(s);s.loader.exec_module(v1)
d=v1.p.candidate.dense
GUIDE=(v1.TEMPLATE_GUIDE[2:].replace('常规另须空即无额外条件。','另须空即真。').rstrip('\n')+'余量取非负整数，单位同界。\n')


def unit(group):
    try:text=group['rules'][0]['requires'][-1]
    except(KeyError,IndexError,TypeError)as exc:raise ValueError('Missing ordered high threshold')from exc
    match=re.fullmatch(r'余量≥[0-9]+([一-鿿A-Za-z]{1,12})',text)
    if match is None:raise ValueError('Unsupported integer threshold and unit syntax')
    return match.group(1)


def swap_guide(text,before,after):
    header=d.base.grouped.HEADER
    if type(text)is not str or not text.startswith(header):raise ValueError('Missing complete public header')
    end=text.find('\n',len(header))
    if end<0:raise ValueError('Missing metadata line')
    start=end+1
    if not text[start:].startswith(before):raise ValueError('Counted domain guide differs')
    return text[:start]+after+text[start+len(before):]


def encode(value):
    """Lift only the first explicit mandatory scope predicate,unit by unit."""
    stripped=copy.deepcopy(value)
    for group in stripped['groups']:
        u=unit(group);head,sep,tail=group['scope'].partition('；')
        prefix='（余量按非负整数'+u+'计）'
        if not head or not sep or not(tail==prefix or tail.startswith(prefix+'且')):
            raise ValueError('Every group must explicitly start its scope conditions with the matching domain')
        remaining=tail[len(prefix):]
        if remaining:
            if remaining=='且':raise ValueError('Empty remaining scope condition')
            group['scope']=head+'；'+remaining[1:]
        else:group['scope']=head
    original=v1.template_render(stripped,16000)['prompt']
    return swap_guide(original,v1.TEMPLATE_GUIDE,GUIDE)


def restore(text):
    stripped=v1.template_restore(swap_guide(text,GUIDE,v1.TEMPLATE_GUIDE))
    value=copy.deepcopy(stripped)
    for group in value['groups']:
        u=unit(group);head,sep,tail=group['scope'].partition('；')
        if not head or(sep and not tail):raise ValueError('Empty scope part')
        group['scope']=head+'；（余量按非负整数'+u+'计）'+('且'+tail if sep else'')
    value=d.parse(d._render(value))
    if encode(value)!=text:raise ValueError('Noncanonical domain-template encoding')
    return value


def render(value,budget=768):
    v1.p.candidate.base.b.grouped.budget_check(budget)
    if d.parse(d._render(value))!=value:raise ValueError('Noncanonical original projection')
    text=encode(value)
    if restore(text)!=value:raise ValueError('Domain template changed ordered public fields')
    if len(text)>budget:raise ValueError('Complete domain template exceeds budget;no truncation')
    return dict(prompt=text,characters=len(text),budget=budget,ordered_fields_roundtrip_exact=True,
        mandatory_numeric_domain_preserved=True,model_reader_fidelity_verified=False,
        source_only_generation_tested=False,used_by_authorized14=False,new_model_calls=0)
