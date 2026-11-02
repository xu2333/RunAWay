"""Separate primary,ordering and erasure endpoints;no auxiliary priming/pooling."""
import copy
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


plan=load('source_order_score_plan',HERE/'plan.py')
prior=load('source_order_score_functions',HERE.parent/'owned-conditions-v1/score.py')
prior.plan=plan
counts,disagreement=prior.counts,prior.disagreement


def summarize(rows,responses,cards,parents):
    primary={key[:3]+(key[-1],):answer for key,answer in responses.items() if key[3:5]==('primary','intact')}
    result=prior.summarize(rows,primary,cards)
    result.update(primary_cases_per_method=23,legacy_cases=24,disputed_cases=1)
    data=plan.inputs();method='source-order-v3';intact=[];erased=[];details={}
    for g in (0,1):
        key=('j16',method,g);valid=key in cards
        a=[responses.get(key+('order','intact',r),{}) if valid else {} for r in (0,1)]
        d=[responses.get(key+('order','erased',r),{}) if valid else {} for r in (0,1)]
        intact+=a;erased+=d
        mechanism={'valid_parent':valid,'generated_order_bindings':0,'source_probe_binding_generated':False,
                   'source_order_literal_present':False,'erasure_eligible':False,'erasure_reason':'invalid_parent'}
        if valid:
            slot=next(s for s in plan.slots() if s['kind']=='extract' and plan.parent(s)==key)
            files=plan.bind(slot,parents[key]);meta=files['source-order.private.json'];damage=plan.candidate.erase_order_targets(files,plan.BUDGET)
            mechanism.update(generated_order_bindings=len(meta['bindings']),
                source_probe_binding_generated=plan.ORDERED in meta['full_ordered_actions'],
                source_order_literal_present=plan.ORDERED in plan.candidate.graph.dense.decode(files['prompt.md']),
                erasure_eligible=damage['eligible'],erasure_reason=damage.get('reason'))
        details[str(g)]={'mechanism':mechanism,'intact':counts(data['auxiliary_rows'],a),
                        'erased_expected_unknown':counts(data['erased_auxiliary_expectation_rows'],d)}
    a=counts(data['auxiliary_rows'],intact);d=counts(data['erased_auxiliary_expectation_rows'],erased)
    mechanism_pass=all(v['mechanism']['source_probe_binding_generated'] and v['mechanism']['source_order_literal_present']
                       and v['mechanism']['erasure_eligible'] for v in details.values())
    result['auxiliary_order']={'source_cases':1,'primary_cases_unchanged':23,
        'post_hoc_source_authored_not_independent_holdout':True,'by_generation':details,
        'strict_intact_source_order':a,'strict_erased_expected_unknown':d,
        'erased_label_is_card_information_not_new_source_preference':True,
        'damage_is_designated_field_removal_not_semantic_erasure_proof':True}
    result['planned_development_acceptance']={
        'candidate_primary23':result['per_method_strict'][method]['joint']['correct']==23,
        'both_generated_probe_bindings_and_eligible_damage':mechanism_pass,
        'intact_order_all_answers':a['joint']['correct']==1,
        'erased_order_all_unknown':d['joint']['correct']==1,
        'all_required':result['per_method_strict'][method]['joint']['correct']==23 and mechanism_pass
                       and a['joint']['correct']==1 and d['joint']['correct']==1,
        'not_population_stability_or_independent_semantic_proof':True}
    result.update(semantic_annotation_independently_accepted=False,validates_h93_or_development=False)
    return result
