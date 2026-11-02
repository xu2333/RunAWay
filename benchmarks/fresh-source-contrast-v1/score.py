"""Nested card/tail fidelity; paired-person rescoring adds no independent samples."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent


def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


plan=load('fresh_contrast_score_plan',HERE/'plan.py')
prior=load('fresh_contrast_score_prior',HERE.parent/'owned-conditions-v1/score.py')
prior.plan=SimpleNamespace(PROFILES=plan.PROFILES,METHODS=('tail','card'),inputs=plan.inputs)
counts,disagreement=prior.counts,prior.disagreement


def summarize(rows,responses,cards):
 products={};answers={}
 for (pid,method,g),card in cards.items():
  for view in ('tail','card'):
   products[pid,view,g]={'characters':len(plan.material(pid,card['prompt'],view))}
   for r in (0,1):
    if (pid,method,g,view,r) in responses:answers[pid,view,g,r]=responses[pid,method,g,view,r]
 result=prior.summarize(rows,answers,products)
 paired=[]
 for pid in plan.PROFILES:
  opposite=plan.corpus.PAIRS[pid]
  divergent=[r for r in rows if r['person']==opposite and r['personal_known']]
  own=[answers.get((pid,'card',g,r),{}) for g in (0,1) for r in (0,1)]
  paired.append({'donor_profile':pid,'counterfactual_recipient':opposite,'opposite_personal_reference':counts(divergent,own),
                 'new_reader_calls':0,'independent_behavioral_evidence':False})
 result.update(primary_cases_per_method=48,legacy_cases=48,disputed_cases=0,answers_per_case_per_view=8,
   template_paired_families=2,not_four_independent_authors=True,pair_rescoring=paired,
   paired_diagnostic_is_algebraically_dependent=True,semantic_annotation_independently_accepted=False)
 return result
