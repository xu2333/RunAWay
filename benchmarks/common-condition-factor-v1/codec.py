"""Factor a shared ordered predicate prefix, without deleting any public condition.

Exact projection restoration is a syntactic guarantee. How a model reads the new
public instruction remains unmeasured. No service, repair or authority is added.
"""
import copy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('common_predicate_dense_codec',HERE.parent/'owned-dense-v1/codec.py')
dense=importlib.util.module_from_spec(spec);spec.loader.exec_module(dense)
LABEL='每条规则另须本题所问项目满足='


def canonical(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))


def restore(text):
    """Restore full ordered predicates using only the counted public card."""
    metadata=dense.metadata(text);head=dense.prefix(metadata);body=text[len(head):]
    if not body.startswith(LABEL):return dense.decode(text)
    first,body=body.split('\n',1)
    conditions=json.loads(first[len(LABEL):])
    if (type(conditions)is not list or not conditions or
            any(type(c)is not str or not c.strip()for c in conditions)or
            first!=LABEL+canonical(conditions)):
        raise ValueError('Invalid public common-condition clause')
    value=dense.parse(head+body)
    for group in value['groups']:
        for row in group['rules']:row['requires']=conditions+row['requires']
    return dense._render(value)


def factor(text,budget=768):
    if type(budget)is not int or budget<=0:raise ValueError('Positive whole-card budget required')
    value=dense.parse(text);original=copy.deepcopy(value)
    rules=[row for group in value['groups']for row in group['rules']]
    common=list(rules[0]['requires'])if rules else[]
    for row in rules[1:]:
        length=0
        for a,b in zip(common,row['requires']):
            if a!=b:break
            length+=1
        common=common[:length]
    result=text
    used=[]
    if common:
        for row in rules:row['requires']=row['requires'][len(common):]
        head=dense.prefix(value);flat=dense._render(value)
        candidate=head+LABEL+canonical(common)+'\n'+flat[len(head):]
        if len(candidate)<len(text):result=candidate;used=common
    expanded=restore(result)
    if expanded!=dense.decode(text)or dense.parse(expanded)!=original:
        raise AssertionError('Common-condition factor changed the public projection')
    if len(result)>budget:
        raise ValueError('Complete factored card exceeds budget; no truncation')
    return dict(prompt=result,original_characters=len(text),characters=len(result),
                saved_characters=len(text)-len(result),common_conditions=used,
                rule_count=len(rules),ordered_projection_roundtrip_exact=True,
                all_scopes_questions_conditions_actions_priorities_unknowns_preserved=True,
                model_reader_fidelity_verified=False,new_model_calls=0,
                production_default_changed=False)
