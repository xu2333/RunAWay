"""Freeze8unapproved reads of one original/neutral/named view parent;no extraction."""
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


fresh=load('named_view_upstream',ROOT/'scripts/replay_fresh_source_contrast.py')
old=fresh.engine.plan
prototype=load('named_view_prototype',HERE/'prototype.py')
read,sha,digest,choice_reader=old.read,old.sha,old.digest,old.choice_reader
PROFILES,METHODS,MODEL,AS_OF,CAP,BUDGET=('e0',),('original','neutral','named'),old.MODEL,old.AS_OF,8,1536


def inputs():
    d=old.inputs()
    return {'sources':{'e0':d['sources']['e0']},'queries':{'editing':d['queries']['editing']},
            **{k:[r for r in d[k] if r['person']=='e0'] for k in ('rows','legacy_rows','disputed_rows')}}


@lru_cache(maxsize=1)
def _views():
    import re
    fresh.check()
    d=read(fresh.DEFAULT)
    parent=next(r for r in d['records'] if r['kind']=='extract' and r['profile']=='e0' and r['generation']==0 and 'card' in r)
    anchors=[(s['id'],match.group(0),match.group(1)) for s in inputs()['sources']['e0']['sources'] if s['role']=='user'
             for match in re.finditer('我选全名为“([^”]+)”的那一套',s['text'])]
    if len(anchors)!=1:raise ValueError('Source does not uniquely declare the selected formal name')
    values=[]
    for method in METHODS:
        v=prototype.modify(parent['card']['prompt'],anchors[0][2],method,BUDGET)
        values.append({**v,'profile':'e0','method':method,'generation':0,'memory_ceiling':BUDGET,
            'source_sha256':old.digest(inputs()['sources']['e0']),'parent_answer_sha256':parent['card']['answer_sha256'],
            'parent_slot':parent['slot']})
    if values[1]['characters']!=values[2]['characters'] or values[0]['characters']+8!=values[1]['characters']:raise ValueError('Matched marker sizes differ')
    return values


def views():return copy.deepcopy(_views())
def parent(slot):return slot['profile'],slot['method'],slot['generation']
def view(slot):return next(v for v in views() if parent(v)==parent(slot))


def slots():
    jobs=[('none','shared_editing',None,None,None),('full','e0',None,None,None)]
    for repeat in (0,1):jobs += [('read','e0',m,0,repeat) for m in (METHODS if repeat==0 else reversed(METHODS))]
    return [{'slot':i+1,'kind':k,'profile':p,'method':m,'generation':g,'read_repeat':r,'budget':BUDGET if m else None,
             'key':':'.join(map(str,(k,p,m,g,r)))} for i,(k,p,m,g,r) in enumerate(jobs)]


def request(slot,parents=None):
    if slot not in slots() or parents is not None:raise ValueError('Only fixed eight-slot requests permitted')
    data=inputs()
    material='' if slot['kind']=='none' else old.old.canonical(data['sources']['e0']) if slot['kind']=='full' else view(slot)['prompt']
    req=choice_reader.make_request(material,data['queries']['editing'],as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':old.old.grouped_support.SYSTEM,**req,'prompt':old.old.COMMON+req['prompt']}


def implementation():
    result=old.implementation()
    paths=list(HERE.glob('*.py'))+[fresh.DEFAULT,fresh.DEFAULT.with_suffix('.sha256'),ROOT/'scripts/replay_fresh_source_contrast.py',ROOT/'scripts/replay_compression_stability.py',HERE.parent/'owned-dense-v1/codec.py']
    result.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    return dict(sorted(result.items()))


def values():
    data=inputs()
    proposal={'kind':'unapproved_named_target_readonly8','requested_model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':8,
        'source_messages':12,'public_question_forms':24,'primary_cases_per_view':12,'known':8,'unknown':4,'personal_known':5,
        'stages':{'controls':2,'extractions':0,'fixed_view_reads':6},'methods':list(METHODS),'whole_character_budget':BUDGET,
        'inherited_parents':1,'selection':'First chronological valid e0 generation0 from closed46;posthoc hard-failure family,not random or best-of.',
        'intervention':'Change only selected formal-name rule question by appending8character named marker;matched neutral8character marker is separate control.All actions/guards/scopes/other rows unchanged.',
        'control':'New full immediately12casesbothorders,no missing,personal-known>none;failure closes before read3.',
        'primary':'Per view12fixed cases,2newreads*2ordersallcorrect.One inherited parent,not fresh generation stability.',
        'comparison':'Report original/named/neutral separately.If both markers recover,extra wording/attention remains plausible;no unique semantic cause claim.',
        'all_requests_static':True,'new_extractions':0,'old_reader_responses_scores_or_references_sent':False,
        'post_hoc_case_informed_developer_annotation':True,'fresh_generation_stability_test':False,
        'semantic_equivalence_independently_accepted':False,'independent_holdout':False,'new_original_inventory_coverage':0,
        'real_person_fidelity_verified':False,'aggregate_token_cap':None,'money_cap':None,'timeout_per_local_child_seconds':180,
        'max_nominal_timeout_sum_seconds':1440,'not_a_spend_or_total_duration_cap':True,
        'retry':False,'repair':False,'resume':False,'replenishment':False,'no_invalid_product_skips_all_views_prevalidated':True,
        'fatal':'Control/transport/wire/decode/unknownusage/model/runtime/input/viewhash/guard closes remainder;intentcounts,unusedexpire.',
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
