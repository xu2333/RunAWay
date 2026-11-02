"""Prepare22unapproved source-only generation/ordering-grounding attempts."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


old=load('source_order_probe_parent',HERE.parent/'action-policy-comparison-v1/plan.py')
baseline=load('source_order_probe_baseline',HERE.parent/'action-policy-v2/candidate.py')
candidate=load('source_order_probe_candidate',HERE.parent/'source-order-v3/candidate.py')
read,sha,digest=old.read,old.sha,old.digest
choice_reader=old.choice_reader
PROFILES,METHODS,MODEL,AS_OF,CAP,BUDGET=('j16',),('policy-v2','source-order-v3'),old.MODEL,old.AS_OF,22,1536
ORDERED='先约定固定安静时段'


def inputs():
    data=copy.deepcopy(old.inputs())
    # These facts stay in a separate auxiliary call and never prime primary
    # question packets or the source-only encoder. Controls already see source.
    scenario='只核对给定记忆材料中明确写出的执行先后，不根据常识或协调方法补推：作息相近的长期室友，大家认可两种方法可行，已确认进入连续夜班周。记录中明确表达哪种先后安排？没有唯一明确记录则回答U。'
    aux=[{'id':'order_probe_a','scenario':scenario,'options':{'A':ORDERED,'B':'留到以后再约定固定安静时段'}},
         {'id':'order_probe_b','scenario':scenario,'options':{'A':'留到以后再约定固定安静时段','B':ORDERED}}]
    source=next(s for s in data['sources']['j16']['sources'] if s['id']=='m16')
    if ORDERED not in source['text']:raise ValueError('Auxiliary source phrase differs')
    row={'person':'j16','case':'source_order_aux','gold':ORDERED,'query_ids':[q['id'] for q in aux],
         'personal_known':False,'stratum':'execution','support':[{'source_id':'m16','quote':source['text']}],
         'developer_authored_after_consumed_failure':True,'independent_semantic_acceptance':False}
    data['queries']['order']=aux
    data['queries']['control']=copy.deepcopy(data['queries']['j'])+copy.deepcopy(aux)
    if len({q['id'] for q in data['queries']['control']})!=50:raise ValueError('Auxiliary ID collision')
    data['auxiliary_rows']=[row]
    erased=copy.deepcopy(row);erased.update(gold='U',counterfactual_card_information_expectation_not_source_preference=True)
    data['erased_auxiliary_expectation_rows']=[erased]
    return data


def cells():return [('j16','policy-v2',0),('j16','source-order-v3',0),('j16','source-order-v3',1),('j16','policy-v2',1)]
def parent(slot):return slot['profile'],slot['method'],slot['generation']


def slots():
    jobs=[('none','shared_j',None,None,'control','intact',None),('full','j16',None,None,'control','intact',None)]
    jobs += [('extract',p,m,g,'extract','intact',None) for p,m,g in cells()]
    for repeat in (0,1):
        jobs += [('read',p,m,g,'primary','intact',repeat) for p,m,g in (cells() if repeat==0 else reversed(cells()))]
    order=[(0,'intact'),(0,'erased'),(1,'erased'),(1,'intact')]
    for repeat in (0,1):
        jobs += [('read','j16','source-order-v3',g,'order',v,repeat) for g,v in (order if repeat==0 else reversed(order))]
    return [{'slot':i+1,'kind':k,'profile':p,'method':m,'generation':g,'task':t,'variant':v,'read_repeat':r,
             'budget':BUDGET if m else None,'key':':'.join(map(str,(k,p,m,g,t,v,r)))} for i,(k,p,m,g,t,v,r) in enumerate(jobs)]


def question_bank(slot):return 'control' if slot['kind'] in ('none','full') else 'j' if slot['task']=='primary' else 'order'


def bind(slot,answer):
    if slot not in slots() or slot['kind']!='extract':raise ValueError('Only own extraction binds')
    encoder=baseline if slot['method']=='policy-v2' else candidate
    return encoder.bind(answer,inputs()['sources']['j16'],slot['budget'])


def bound_view(slot,parents):
    key=parent(slot)
    if key not in parents:return None
    extraction=next(s for s in slots() if s['kind']=='extract' and parent(s)==key)
    files=bind(extraction,parents[key])
    if slot['variant']=='intact':return {'eligible':True,'prompt':files['prompt.md'],'characters':len(files['prompt.md'])}
    return candidate.erase_order_targets(files,BUDGET)


def request(slot,parents=None):
    if slot not in slots():raise ValueError('Outside frozen22slot schedule')
    data=inputs()
    if slot['kind']=='extract':
        encoder=baseline if slot['method']=='policy-v2' else candidate
        return {'model':MODEL,'system':old.prior.grouped_support.SYSTEM,**encoder.make_request(data['sources']['j16'],BUDGET)}
    if slot['kind']=='none':material=''
    elif slot['kind']=='full':material=old.prior.canonical(data['sources']['j16'])
    else:
        view=bound_view(slot,parents or {})
        if view is None or not view['eligible']:return None
        material=view['prompt']
    req=choice_reader.make_request(material,data['queries'][question_bank(slot)],as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':old.prior.grouped_support.SYSTEM,**req,'prompt':old.prior.COMMON+req['prompt']}


def implementation():
    result=old.implementation()
    paths=list(HERE.glob('*.py'))+[HERE.parent/'source-order-v3/candidate.py',HERE.parent/'order-targets-v1/prototype.py']
    result.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    return dict(sorted(result.items()))


def values():
    data=inputs()
    proposal={'kind':'unapproved_source_order22_generation_probe','requested_model':MODEL,'as_of':AS_OF,
        'max_new_local_cli_attempts':22,'source_messages':34,'distinct_public_forms':50,
        'primary_cases_per_method':23,'unscored_old_w14':1,'auxiliary_source_order_cases':1,
        'stages':{'controls':2,'source_only_extractions':4,'primary_reads':8,'candidate_aux_intact_reads':4,'eligible_candidate_aux_erased_reads':4},
        'methods':list(METHODS),'whole_character_budget':1536,'generations_per_method':2,'reads_per_card_task_variant':2,
        'all_extractions_before_any_read':True,
        'control':'Full immediately23primary+1auxiliary,bothorders,no missing,personal-known>none;oldw14excluded. Failure closes before extract3.',
        'primary':'Unchanged23fixed author cases,2new cards*2reads*2orders strict. Primary read packets contain only original48forms;auxiliary facts/questions cannot prime them.',
        'auxiliary':'Separate candidate-only two-form calls. Intact expected source-quoted ordering;erased expectedU is a counterfactual card-information label,not new source-preference gold. Require both generated parents/read repeats/orders;ineligible stays missing.',
        'erasure':'Remove only compiler-designated model-generated execution targets;preserve all core choices/guards. Eligible only if split exists and exact ordered literals no longer occur. This is not semantic erasure proof;paraphrase redundancy remains possible. No repair.',
        'invalid_product':'Skip all own-parent reads:baseline2;candidate6(primary2+auxintact2+auxerased2). No replacement. Ineligible damage alone skips own2erased slots. Unused expire.',
        'source_only':'Only own source,budget,header/guide,instructions and schema;no old cards/responses/scores,reference/questions or manual row bindings. Generic design is development-informed.',
        'fatal':'Control,transport,wire/decode,unknownusage,model,runtime,input hash or ownedguard failure closes remainder. Intent counts even if receipt unknown.',
        'aggregate_token_cap':None,'money_cap':None,'timeout_per_local_child_seconds':180,'max_nominal_timeout_sum_seconds':3960,
        'not_a_spend_or_total_duration_cap':True,'retry':False,'repair':False,'resume':False,'replenishment':False,
        'post_hoc_consumed_development_design':True,'independent_holdout':False,'semantic_annotation_independently_accepted':False,
        'new_original_inventory_coverage':0,'validates_h93_or_development':False,'real_person_fidelity_verified':False,
        'approved':False,'new_service_authority':False,'production_default_changed':False}
    return {'proposal.json':proposal,'slots.json':slots(),'sources.json':data['sources'],'queries.public.json':data['queries'],
        'reference.consumed-development.private.json':{k:data[k] for k in ('rows','legacy_rows','disputed_rows','auxiliary_rows','erased_auxiliary_expectation_rows')},
        'static-requests.json':{s['key']:request(s) for s in slots() if s['kind']!='read'},
        'dynamic-rules.json':{'slots':[s for s in slots() if s['kind']=='read'],'builder':'benchmarks/source-order-probe-v1/plan.py:request',
            'parent':'Exact source+method+generation;task/variant independent response keys;only designated execution-field erasure,conditional fixed skip if ineligible.'},
        'implementation-sha256.json':implementation()}


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
