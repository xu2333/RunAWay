"""Fixed-parent read-only23-case endpoint,not model-generation stability."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


plan=load('order_read_score_plan',HERE/'plan.py')
prior=load('order_read_count_functions',HERE.parent/'compression-stability-v1/score.py')
counts,disagreement=prior.counts,prior.disagreement


def summarize(rows,responses):
    methods,outcomes,disputes={},{},[]
    for method in plan.METHODS:
        reads=[[responses.get(('j16',method,g,r),{}) for r in (0,1)] for g in (0,1)]
        generations={}
        for g in (0,1):
            v=plan.view({'profile':'j16','method':method,'generation':g})
            generations[str(g)]={'fixed_material_available':True,'characters':v['characters'],'memory_ceiling':1536,
                'first':counts(rows,[reads[g][0]]),'second':counts(rows,[reads[g][1]]),
                'strict_both_reads':counts(rows,reads[g]),'within_parent_read_disagreement':disagreement(rows,[reads[g][0]],[reads[g][1]])}
        methods[method]={'generations':generations,'strict_all_parents_and_reads':counts(rows,reads[0]+reads[1])}
        outcomes[method]=reads[0]+reads[1]
        for row in plan.inputs()['disputed_rows']:
            disputes.append({'profile':'j16','method':method,'case':row['case'],
                'legacy_author_annotation_unaccepted':row['gold'],'reference_accepted':False,'included_in_primary_or_gate':False,
                'generations_reads_orders':[[[a.get(q) for q in row['query_ids']] for a in generation] for generation in reads]})
    pair={k:0 for k in ('planned','both_correct','only_split_correct','only_original_correct','neither_correct','split_missing','original_missing')}
    for row in rows:
        s,o=counts([row],outcomes['split'])['joint'],counts([row],outcomes['original'])['joint']
        pair['planned']+=1
        label='both_correct' if s['correct'] and o['correct'] else 'only_split_correct' if s['correct'] else 'only_original_correct' if o['correct'] else 'neither_correct'
        pair[label]+=1;pair['split_missing']+=s['missing'];pair['original_missing']+=o['missing']
    return {'methods':methods,'paired_strict':pair,'disputed_observations_not_scored':disputes,
        'primary_cases_per_method':23,'inherited_producer_parents':2,'new_extractions':0,
        'fresh_generation_stability_test':False,'post_hoc_case_informed_developer_annotation':True,
        'semantic_decomposition_independently_accepted':False,'validates_h93_or_development':False,
        'new_original_inventory_coverage':0,'production_default_changed':False}
