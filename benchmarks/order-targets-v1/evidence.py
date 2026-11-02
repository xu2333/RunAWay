"""Offline,post-hoc developer decomposition of both chronological policy-v2cards."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


upstream=load('order_target_upstream',ROOT/'scripts/replay_action_policy_comparison.py')
prototype=load('order_target_projection',HERE/'prototype.py')
p=upstream.engine.plan
DEFAULT=HERE/'derived.synthetic.json'
REFACTORED_V1=HERE/'refactored-v1.synthetic.json'
CORE='约定固定安静时段'


def derive(mode='explicit-v2'):
    if mode not in ('explicit-v2','refactored-v1'):raise ValueError('Unknown derivation mode')
    upstream.check()
    data=p.read(upstream.DEFAULT);sources=data['sources']['j16']
    offered=next(s for s in sources['sources'] if s['id']=='m13')
    if CORE not in offered['text'] or offered['role']!='user':raise ValueError('Source-offered label differs')
    parents=[]
    for generation in (0,1):
        record=next(r for r in data['records'] if r['kind']=='extract' and r['method']=='policy-v2' and r['generation']==generation)
        slot=next(s for s in p.slots() if s['key']==record['key'])
        answer=upstream.shared.parse_answer(record['raw'])
        original=p.bind(slot,answer)
        if original['prompt.md']!=record['card']['prompt']:raise ValueError('Original card changed')
        ledger=original['profile.private.json']['ledger']
        selected=[i for i,r in enumerate(ledger['rows']) if r['action']=='先'+CORE]
        if len(selected)!=1:raise ValueError('Expected one explicitly reviewed ordered action')
        binding={'row_index':selected[0],'core_action':CORE,
                 'core_evidence':[{'source_id':offered['id'],'quote':offered['text']}],
                 'execution_question':'执行先后'}
        binding_fn=prototype.bind if mode=='explicit-v2' else prototype.bind_refactored_v1
        separated=binding_fn(ledger,sources,[binding],1536)
        parents.append({'generation':generation,'source_sha256':p.digest(sources),
            'raw_parent_value_sha256':record['raw_value_sha256'],
            'parent_answer_sha256':record['card']['answer_sha256'],
            'original_ledger_sha256':p.digest(ledger),
            'separated_ledger_sha256':p.digest(separated['profile.private.json']['ledger']),
            'original_prompt':original['prompt.md'],'original_characters':len(original['prompt.md']),
            'split_prompt':separated['prompt.md'],'split_characters':len(separated['prompt.md']),
            'developer_binding':binding,'conservation':separated['decomposition.private.json']})
    result={'kind':'offline_order_target_decomposition_v1','all_sources_fictional':True,
        'upstream_snapshot_sha256':p.sha(upstream.DEFAULT),
        'upstream_input_manifest_sha256':data['source_input_manifest_sha256'],
        'upstream_observation_manifest_sha256':data['source_observation_manifest_sha256'],
        'parents':parents,'whole_public_character_cap':1536,'actual_new_model_calls':0,
        'post_hoc_case_informed_developer_annotation':True,'automatic_parser_or_new_generation':False,
        'literal_ordered_action_retained':True,'semantic_decomposition_independently_accepted':False,
        'old_semantic_equivalence_verified':False,'behavioral_fidelity_verified':False,
        'replaces_closed_cards_or_scores':False,'new_service_authority':False,'production_default_changed':False}
    if mode=='explicit-v2':
        result.update(kind='offline_order_target_decomposition_explicit_v2',original_public_scope_placement_preserved=True)
    return result


def replay(data,mode='explicit-v2'):
    if data!=derive(mode):raise ValueError('Source/decomposition/lineage or claim differs')
    return {'new_model_calls':0,'original_characters':[v['original_characters'] for v in data['parents']],
        'split_characters':[v['split_characters'] for v in data['parents']],
        'literal_ordered_action_retained':True,'post_hoc_case_informed_developer_annotation':True,
        'semantic_decomposition_independently_accepted':False,'behavioral_fidelity_verified':False,
        'fresh_generation_stability_test':False,'production_default_changed':False}


def check(path=None,mode='explicit-v2'):
    path=Path(path or (DEFAULT if mode=='explicit-v2' else REFACTORED_V1))
    if p.sha(path)!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Derived checksum differs')
    return replay(p.read(path),mode)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.write:
        with DEFAULT.open('x',encoding='utf-8') as f:json.dump(derive(),f,ensure_ascii=False,indent=2);f.write('\n')
        with DEFAULT.with_suffix('.sha256').open('x') as f:f.write(p.sha(DEFAULT)+'\n')
    print(json.dumps(check(),ensure_ascii=False,indent=2))
