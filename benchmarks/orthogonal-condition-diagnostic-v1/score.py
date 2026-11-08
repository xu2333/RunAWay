"""Keep actual-card primary endpoints separate from the constructed damage diagnostic."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


plan=load('orthogonal_score_plan',HERE/'plan.py')
prior=load('orthogonal_count_functions',HERE.parent/'compression-stability-v1/score.py')
counts=prior.counts


def summarize(rows,responses):
    methods={}
    for method in plan.METHODS:
        pieces={'strict_eight_answers':[],'old_anchors':[],'crossed_unknown':[]}
        for person in plan.PROFILES:
            own=[row for row in rows if row['person']==person]
            answers=[responses.get((person,method,g,r),{})for g in(0,1)for r in(0,1)]
            pieces['strict_eight_answers'].append(counts(own,answers))
            pieces['old_anchors'].append(counts([r for r in own if r['cohort']!='crossed_time_material'],answers))
            pieces['crossed_unknown'].append(counts([r for r in own if r['cohort']=='crossed_time_material'],answers))
        methods[method]={name:{group:{field:sum(piece[group][field]for piece in values)
                            for field in values[0][group]}for group in values[0]}
                         for name,values in pieces.items()}
    diagnostic={}
    own=[row for row in rows if row['person']=='otter']
    for method in plan.DIAGNOSTICS:
        answers=[responses.get(('otter',method,0,r),{})for r in(0,1)]
        diagnostic[method]={'strict_four_answers':counts(own,answers),
            'old_anchors':counts([r for r in own if r['cohort']!='crossed_time_material'],answers),
            'crossed_unknown':counts([r for r in own if r['cohort']=='crossed_time_material'],answers)}
    return dict(methods=methods,constructed_diagnostic=diagnostic,primary_cases_per_method=120,
                primary_known=56,primary_unknown=64,new_extractions=0,
                generation_stability_retested=False,unknown_notes_may_rescue_damaged_reader=True,
                old_question_gold_replaced=False,production_default_changed=False)
