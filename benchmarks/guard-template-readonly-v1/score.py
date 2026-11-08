"""Fixed82case endpoints per view;missing is not U or semantic recovery."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


p=load('template_readonly_score_plan',HERE/'plan.py')
old=load('template_readonly_counts',HERE.parent/'compression-stability-v1/score.py')
counts=old.counts


def summarize(rows,responses):
    views={}
    for view in p.VIEWS:
        answers=[responses.get(('quince',view,0,r),{})for r in(0,1)]
        views[view]=dict(strict=counts(rows,answers),per_read={str(r):counts(rows,[answers[r]])for r in(0,1)},
            answers_per_case=4,generation_stability_verified=False)
    cells=[]
    for row in rows:
        cell={k:row[k]for k in('person','case','cohort','gold')}
        for view in p.VIEWS:
            values=[responses.get(('quince',view,0,r),{}).get(q)for r in(0,1)for q in row['query_ids']]
            cell[view]=dict(answers=values,correct=all(v==row['gold']for v in values),missing=any(v is None for v in values))
        cells.append(cell)
    return dict(views=views,all_cases=cells,fixed_cases_per_view=82,known=36,unknown=46,
        independent_people=1,generation_stability_verified=False,independent_semantic_gold=False,
        source_only_new_generation_tested=False,condition_revision_candidate_tested=False)
