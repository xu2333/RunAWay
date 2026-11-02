"""Replay the actual new-source card/tail contrast; no service capability."""
import argparse
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


shared = load('fresh_contrast_archive_shared', ROOT / 'scripts/replay_compression_stability.py')
engine = load('fresh_contrast_archive_engine', ROOT / 'benchmarks/fresh-source-contrast-v1/engine.py')
INPUT_MANIFEST = 'b5a2af613a6902e33e91316584bf2ea94e3d9e2045308cf31b4759fe6bf00f53'
KIND = 'actual_fresh_source_contrast46'
DEFAULT = ROOT / 'benchmarks/fresh-source-contrast-v1/measured.synthetic.json'


def posthoc_card_audit(data):
    """Literal/annotation inspection, separate from the frozen choice endpoint."""
    rows=engine.plan.inputs()['rows'];out=[]
    for rec in data['records']:
        if rec['kind']!='extract' or 'card' not in rec:continue
        slot=engine.plan.slots()[rec['slot']-1]
        files=engine.plan.bind(slot,shared.parse_answer(rec['raw']))
        own={r['case']:r['gold'] for r in rows if r['person']==rec['profile']}
        text=engine.plan.candidate.graph.dense.decode(files['prompt.md'])
        bindings=files['source-order.private.json']['bindings']
        out.append({'profile':rec['profile'],'generation':rec['generation'],
            'characters':len(files['prompt.md']),
            'named_method_literal_present':own['c05'] in text,
            'past_status_literal_present':own['c06'] in text,
            'execution_literal_present':own['c07'] in text,
            'active_order_splits':len(bindings),
            'unexpected_binding_cores':[b['core_action'] for b in bindings if b['core_action']!=own['c01']]})
    return {'preregistered_endpoint':False,'independent_semantic_acceptance':False,
        'literal_presence_does_not_prove_scope_or_entailment':True,'valid_parent_observations':out,
        'case12_role_attribution_not_isolated':True,
        'case12_limit':'Options omit the remote proposal action and ordinary readiness is absent. U cannot independently demonstrate rejection of assistant-origin policy.'}


def replay(data):
    inputs=engine.plan.inputs()
    for key in ('independent_reference_acceptance','independent_generalization','encoder_changed_for_new_sources',
                'pair_rescoring_independent','token_matched_tail','optimal_tail_selection'):
        shared.require(data[key] is False,'Unsupported claim: '+key)
    for key in ('source_only_model_generated_annotation','development_informed','template_paired_families'):
        shared.require(data[key] is True,'Missing boundary: '+key)
    for key in ('design','legacy_rows','disputed_rows'):
        shared.require(data[key]==inputs[key],'Authored design/reference differs: '+key)
    shared.require(type(data['answers_per_primary_case']) is int and data['answers_per_primary_case']==8,'Eight-answer endpoint differs')
    shared.require(type(data['fresh_generations_planned']) is int and data['fresh_generations_planned']==8,'Producer count differs')
    result=shared.replay(data,controller=engine,kind=KIND,input_manifest=INPUT_MANIFEST,
                         axes=(),record_fields=('method','view'))
    decoded={engine.plan.parent(r)+(r['view'],r['read_repeat']):shared.parse_answer(r['raw'])
             for r in data['records'] if r['kind']=='read' and r['state']=='completed'}
    losses=[]
    for view in ('tail','card'):
        for row in inputs['rows']:
            values=[[[decoded.get((row['person'],'source-order-v3',g,view,r),{}).get(q)
                       for q in row['query_ids']] for r in (0,1)] for g in (0,1)]
            flat=[v for generation in values for reading in generation for v in reading]
            if any(v!=row['gold'] for v in flat):
                losses.append({'profile':row['person'],'view':view,'case':row['case'],'gold':row['gold'],
                               'missing':any(v is None for v in flat),'generations_reads_orders':values})
    result.update(failed_or_missing_cases=losses,answers_per_primary_case=8,fresh_generations_planned=8,
        original_inventory_measured=232,original_inventory_remaining=0,new_original_inventory_coverage=0,
        new_authored_person_cases=48,template_families=2,independent_generalization=False,
        independent_reference_acceptance=False,pair_rescoring_independent=False,encoder_changed_for_new_sources=False)
    result['posthoc_representation_audit']=posthoc_card_audit(data)

    return result


def check(path=DEFAULT):
    path = Path(path)
    shared.require(engine.plan.sha(path) == path.with_suffix('.sha256').read_text().strip(), 'Snapshot checksum differs')
    return replay(engine.plan.read(path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--input', type=Path, default=DEFAULT)
    args = parser.parse_args(); print(json.dumps(check(args.input), ensure_ascii=False, indent=2))
