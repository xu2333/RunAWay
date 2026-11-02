"""One fixed parent;12cases per view with two reads and two option orders."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

plan=load('named_target_score_plan',HERE/'plan.py')
prior=load('named_target_score_functions',HERE.parent/'compression-stability-v1/score.py')
counts,disagreement=prior.counts,prior.disagreement

def summarize(rows,responses):
 methods={}
 for method in plan.METHODS:
  a=[responses.get(('e0',method,0,r),{}) for r in (0,1)]
  methods[method]={'characters':plan.view({'profile':'e0','method':method,'generation':0})['characters'],
   'strict_both_reads':counts(rows,a),'first':counts(rows,[a[0]]),'second':counts(rows,[a[1]]),
   'read_disagreement':disagreement(rows,[a[0]],[a[1]])}
 return {'methods':methods,'primary_cases_per_view':12,'answers_per_case_per_view':4,'inherited_parents':1,'new_extractions':0,
  'fresh_generation_stability_test':False,'post_hoc_case_informed_developer_annotation':True,'independent_semantic_acceptance':False,
  'neutral_same_character_control':True,'production_default_changed':False}
