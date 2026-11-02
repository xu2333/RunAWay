"""Post-hoc explicit-name marker with equal-length neutral control;no inference."""
import copy
import importlib.util
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'owned-dense-v1/codec.py'
s=importlib.util.spec_from_file_location('named_target_dense',p);dense=importlib.util.module_from_spec(s);s.loader.exec_module(dense)
MARKERS={'named':'〔正式方法全名〕','neutral':'〔沿用原有条件〕'}
assert len(MARKERS['named'])==len(MARKERS['neutral'])==8


def modify(text,formal_name,mode,budget=1536):
 if mode not in ('original','named','neutral'):raise ValueError('Unknown marker mode')
 value=dense.parse(text)
 if dense._render(value)!=text:raise ValueError('Only canonical expanded public views supported;no reflow')
 matches=[(g,r) for g,group in enumerate(value['groups']) for r,rule in enumerate(group['rules']) if rule['choose']==formal_name]
 if len(matches)!=1:raise ValueError('Formal-name row must be unique')
 out=copy.deepcopy(value);g,r=matches[0]
 if mode!='original':out['groups'][g]['rules'][r]['question']+=MARKERS[mode]
 prompt=dense._render(out)
 if not 0<len(prompt)<=budget:raise ValueError('Fixed view exceeds cap')
 restored=copy.deepcopy(out);restored['groups'][g]['rules'][r]['question']=value['groups'][g]['rules'][r]['question']
 if restored!=value:raise ValueError('Non-target field changed')
 return {'prompt':prompt,'characters':len(prompt),'selected_group':g,'selected_rule':r,'question_before':value['groups'][g]['rules'][r]['question'],
   'question_after':out['groups'][g]['rules'][r]['question'],'all_actions_guards_scopes_other_rows_preserved':True,
   'posthoc_developer_annotation':mode!='original','semantic_equivalence_independently_accepted':False}
