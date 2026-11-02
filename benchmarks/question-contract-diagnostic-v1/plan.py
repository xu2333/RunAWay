"""Freeze8unapproved original/explicit task-contract reads of one unchanged parent."""
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


upstream=load('question_contract_upstream',ROOT/'scripts/replay_named_target_diagnostic.py')
old=upstream.engine.plan
read,sha,digest,choice_reader=old.read,old.sha,old.digest,old.choice_reader
PROFILES,METHODS,MODEL,AS_OF,CAP,BUDGET=('e0',),('original','explicit'),old.MODEL,old.AS_OF,8,1536
OLD_TARGET='问题只问活动命名方式'
NEW_TARGET='问题只问本人会选哪套活动流程（返回方案完整名称）'


def inputs():
    d=old.inputs();original=copy.deepcopy(d['queries']['editing']);explicit=copy.deepcopy(original)
    changed=[]
    for q in explicit:
        if OLD_TARGET in q['scenario']:
            q['scenario']=q['scenario'].replace(OLD_TARGET,NEW_TARGET);changed.append(q['id'])
    if len(changed)!=2:raise ValueError('Expected exactly two fixed target forms')
    return {**d,'queries':{'original':original,'explicit':explicit},'changed_query_ids':changed}


@lru_cache(maxsize=1)
def _views():
    upstream.check()
    original=old.view({'profile':'e0','method':'original','generation':0})
    return [{'profile':'e0','method':m,'generation':0,'prompt':original['prompt'],'characters':original['characters'],
             'memory_ceiling':BUDGET,'parent_slot':original['parent_slot'],'parent_answer_sha256':original['parent_answer_sha256'],
             'source_sha256':original['source_sha256'],'question_packet_sha256':digest(inputs()['queries'][m]),
             'same_memory_across_conditions':True,'posthoc_task_clarification_not_semantic_equivalence':m=='explicit'} for m in METHODS]


def views():return copy.deepcopy(_views())
def parent(slot):return slot['profile'],slot['method'],slot['generation']
def view(slot):return next(v for v in views() if parent(v)==parent(slot))


def slots():
    jobs=[]
    for m in METHODS:jobs += [('none','e0',m,None,None),('full','e0',m,None,None)]
    for r in (0,1):jobs += [('read','e0',m,0,r) for m in (METHODS if r==0 else reversed(METHODS))]
    return [{'slot':i+1,'kind':k,'profile':p,'method':m,'generation':g,'read_repeat':r,'budget':BUDGET if k=='read' else None,
             'key':':'.join(map(str,(k,p,m,g,r)))} for i,(k,p,m,g,r) in enumerate(jobs)]


def questions(slot):return inputs()['queries'][slot['method']]


def request(slot,parents=None):
    if slot not in slots() or parents is not None:raise ValueError('Only fixed8requests permitted')
    d=inputs();text='' if slot['kind']=='none' else old.old.old.canonical(d['sources']['e0']) if slot['kind']=='full' else view(slot)['prompt']
    req=choice_reader.make_request(text,questions(slot),as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':old.old.old.grouped_support.SYSTEM,**req,'prompt':old.old.old.COMMON+req['prompt']}


def implementation():
    result=old.implementation()
    paths=list(HERE.glob('*.py'))+[upstream.DEFAULT,upstream.DEFAULT.with_suffix('.sha256'),ROOT/'scripts/replay_named_target_diagnostic.py',ROOT/'scripts/replay_compression_stability.py']
    result.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    return dict(sorted(result.items()))


def values():
    data=inputs()
    proposal={'kind':'unapproved_question_contract_readonly8','requested_model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':8,
        'source_messages':12,'unique_public_forms':26,'forms_per_packet':24,'changed_forms':2,'primary_cases_per_packet':12,
        'known':8,'unknown':4,'personal_known':5,'stages':{'controls':4,'extractions':0,'fixed_card_reads':4},
        'methods':list(METHODS),'whole_character_budget':BUDGET,'same_memory_characters':495,'inherited_parents':1,
        'intervention':'Only the c05two-form task descriptor changes;all facts/options/IDs/other22forms/source/reference/card/reader remain.One unchanged original card,no name/neutral markers.',
        'contract':'Posthoc explicit statement of author-intended future choice task,not independently accepted semantic paraphrase and not replacement of the old question/gold.',
        'controls':'Each question packet gets new none/full.Full immediately12bothorders,no missing,personal-known>ownnone.Both qualify before read5;any failure closes.',
        'primary':'Per packet12fixed cases,2newreads*2ordersallcorrect.Report old and explicit separately.No old-score replacement,best-of or generation-stability claim.',
        'question_packets_separate_calls':True,'all_requests_static':True,'new_extractions':0,'old_responses_scores_reference_or_private_bindings_sent':False,
        'fresh_generation_stability_test':False,'independent_semantic_acceptance':False,'independent_holdout':False,
        'new_original_inventory_coverage':0,'real_person_fidelity_verified':False,'aggregate_token_cap':None,'money_cap':None,
        'timeout_per_local_child_seconds':180,'max_nominal_timeout_sum_seconds':1440,'not_a_spend_or_total_duration_cap':True,
        'retry':False,'repair':False,'resume':False,'replenishment':False,'unused_slots_expire':True,
        'fatal':'Control/transport/wire/decode/unknownusage/model/runtime/input/view/questionhash/guard closes remainder;intentcounts.',
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
