"""Freeze10unapproved reads of two original/split policy-v2parents;no extraction."""
import argparse
import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


derived=load('order_read_derivation',HERE.parent/'order-targets-v1/evidence.py')
old=derived.p
read,sha,digest=old.read,old.sha,old.digest
choice_reader=old.choice_reader
PROFILES,METHODS,MODEL,AS_OF,CAP,BUDGET=('j16',),('original','split'),old.MODEL,old.AS_OF,10,1536
inputs=old.inputs


@lru_cache(maxsize=1)
def _views():
    derived.check();data=read(derived.DEFAULT);values=[]
    for parent in data['parents']:
        for method in METHODS:
            text=parent[method+'_prompt']
            if not 0<len(text)<=BUDGET:raise ValueError('Fixed public view exceeds cap')
            values.append({'profile':'j16','method':method,'generation':parent['generation'],
                'prompt':text,'characters':len(text),'memory_ceiling':BUDGET,
                'view_class':'unchanged_policy_v2' if method=='original' else 'post_hoc_developer_order_target_split',
                'source_sha256':parent['source_sha256'],'parent_answer_sha256':parent['parent_answer_sha256'],
                'developer_annotation_not_model_inference':method=='split'})
    return values


def views():return copy.deepcopy(_views())
def parent(slot):return slot['profile'],slot['method'],slot['generation']
def view(slot):return next(v for v in views() if parent(v)==parent(slot))


def slots():
    cells=[('original',0),('split',0),('split',1),('original',1)]
    jobs=[('none','shared_j',None,None,None),('full','j16',None,None,None)]
    for repeat in (0,1):
        jobs += [('read','j16',m,g,repeat) for m,g in (cells if repeat==0 else reversed(cells))]
    return [{'slot':i+1,'kind':k,'profile':p,'method':m,'generation':g,'read_repeat':r,
             'budget':BUDGET if m else None,'key':':'.join(map(str,(k,p,m,g,r)))} for i,(k,p,m,g,r) in enumerate(jobs)]


def request(slot,parents=None):
    if slot not in slots() or parents is not None:raise ValueError('Only fixed ten-slot requests permitted')
    data=inputs()
    material='' if slot['kind']=='none' else old.prior.canonical(data['sources']['j16']) if slot['kind']=='full' else view(slot)['prompt']
    req=choice_reader.make_request(material,data['queries']['j'],as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':old.prior.grouped_support.SYSTEM,**req,'prompt':old.prior.COMMON+req['prompt']}


def implementation():
    result=old.implementation()
    paths=list(HERE.glob('*.py'))+[HERE.parent/'order-targets-v1/prototype.py',HERE.parent/'order-targets-v1/evidence.py',
        derived.DEFAULT,derived.DEFAULT.with_suffix('.sha256'),derived.upstream.DEFAULT,
        derived.REFACTORED_V1,derived.REFACTORED_V1.with_suffix('.sha256'),
        derived.upstream.DEFAULT.with_suffix('.sha256'),ROOT/'scripts/replay_action_policy_comparison.py',
        ROOT/'scripts/replay_compression_stability.py']
    result.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    return dict(sorted(result.items()))


def values():
    data=inputs()
    proposal={'kind':'unapproved_order_target_readonly10','requested_model':MODEL,'as_of':AS_OF,
        'max_new_local_cli_attempts':CAP,'source_messages':34,'public_question_forms':48,
        'primary_cases_per_method':23,'legacy_cases':24,'unscored_disputed_cases':1,
        'stages':{'controls':2,'source_only_extractions':0,'fixed_view_reads':8},
        'methods':list(METHODS),'whole_character_budget':BUDGET,'inherited_parents':2,'reads_per_view':2,
        'control':'New full immediately23cases/bothorders,no missing,personal-known>none;w14excluded. Failure closes before read3.',
        'primary':'Per method23cases,all2inherited parents*2new reads*2orders correct;unread stays missing. No best-of or old-response pooling.',
        'intervention':'Post-hoc developer mapping of one ordered action per parent:source-offered core on original target,complete original action retained on a distinct execution target. All original guard/other-row fields conserved. Not independent semantic proof or a model-generated fix.',
        'semantic_decomposition_independently_accepted':False,'post_hoc_case_informed_developer_annotation':True,
        'fresh_generation_stability_test':False,'validates_h93_or_development':False,
        'aggregate_token_cap':None,'money_cap':None,'timeout_per_local_child_seconds':180,
        'max_nominal_timeout_sum_seconds':1800,'not_a_spend_or_total_duration_cap':True,
        'retry':False,'repair':False,'resume':False,'replenishment':False,
        'fatal':'Control,transport,wire,decode,unknownusage,model,runtime,input/view hash or ownedguard closes remainder;intent counts,unused expire.',
        'no_invalid_product_skips_all_views_prevalidated':True,
        'independent_holdout':False,'new_original_inventory_coverage':0,'real_person_fidelity_verified':False,
        'approved':False,'new_service_authority':False,'production_default_changed':False}
    return {'proposal.json':proposal,'slots.json':slots(),'sources.json':data['sources'],'queries.public.json':data['queries'],
        'reference.consumed-development.private.json':{k:data[k] for k in ('rows','legacy_rows','disputed_rows')},
        'views.public.json':views(),'static-requests.json':{s['key']:request(s) for s in slots()},
        'dynamic-rules.json':{'slots':[],'all_requests_static':True},'implementation-sha256.json':implementation()}


def prepare(out):
    data=values();out.mkdir(parents=True,exist_ok=False)
    for n,v in data.items():(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps({'files':{n:sha(out/n) for n in sorted(data)},'new_model_calls':0},indent=2)+'\n')
    return data['proposal.json']


def verify(root,*,reconstruct=True):
    for rel,expected in read(root/'manifest.json')['files'].items():
        p=Path(rel)
        if p.is_absolute() or '..' in p.parts or (root/p).is_symlink() or sha(root/p)!=expected:raise ValueError('Frozen input drift')
    if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Frozen implementation drift')
    if reconstruct and any(read(root/n)!=v for n,v in values().items()):raise ValueError('Reconstructed input drift')
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(prepare(args.out),ensure_ascii=False,indent=2))
