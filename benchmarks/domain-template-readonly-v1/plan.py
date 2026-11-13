"""Freeze eight unapproved reads of one domain-preserving graph's original/template public views."""
import argparse
import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


up=load('domain_readonly_upstream',ROOT/'scripts/replay_domain_revision.py')
old=up.p
codec=load('domain_readonly_codec',ROOT/'benchmarks/domain-template-v2/codec.py')
sha,digest,read,choice_reader=old.sha,old.digest,old.read,old.choice_reader
MODEL,AS_OF,CAP=old.MODEL,old.AS_OF,8
PROFILES,METHODS,VIEWS=('rivet',),('task',),('flat1061','domain767','domain_dropped')
FILES={'proposal.json','sources.json','queries.public.json','reference.private.json','views.public.json',
       'slots.json','static-requests.json','implementation-sha256.json'}


@lru_cache(maxsize=1)
def inherited():
    up.check();data=read(up.DEFAULT)
    record=next(r for r in data['records']if r['slot']==3)
    if record['artifact']is None:raise ValueError('Selected original card is not valid')
    original=record['artifact']['prompt'];source=data['prepared_files']['sources.json']['rivet']
    parsed=old.old.candidate.dense.parse(old.old.candidate.restore(original))
    compressed=codec.render(parsed,768)['prompt']
    if len(original)!=1061 or len(compressed)!=767 or codec.restore(compressed)!=parsed:raise ValueError('Selected graph or exact domain layout changed')
    # Constructed diagnostic only:remove the six exact public domain clauses.
    # Do not alter the source,raw graph,other scopes,actions,conditions or unknowns.
    damaged=copy.deepcopy(parsed)
    for group in damaged['groups']:
        u=codec.unit(group);head,sep,tail=group['scope'].partition('；');prefix='（余量按非负整数'+u+'计）'
        if not sep or not(tail==prefix or tail.startswith(prefix+'且')):raise ValueError('Unrecognized domain damage target')
        rest=tail[len(prefix):];group['scope']=head+('；'+rest[1:]if rest else'')
    damage_text=old.old.candidate.dense._render(damaged)
    if damaged==parsed or any(x['rules']!=y['rules']for x,y in zip(damaged['groups'],parsed['groups'])):raise ValueError('Damage changed unrelated rules')
    return dict(sources={'rivet':source},queries={'task':data['prepared_files']['queries.public.json']['rivet']},
        rows=data['prepared_files']['reference.private.json'],views={'flat1061':original,'domain767':compressed,'domain_dropped':damage_text},
        original_parent_slot=3,original_observation_sha256=data['source_observation_manifest_sha256'])


def inputs():return copy.deepcopy(inherited())
def parent(slot):return slot['profile'],slot['view'],slot['generation']
def view(slot):
    if slot['kind']!='read' or slot['view']not in VIEWS:raise ValueError('Foreign fixed view')
    text=inputs()['views'][slot['view']]
    return dict(profile='rivet',view=slot['view'],generation=0,prompt=text,characters=len(text),
        memory_ceiling=768 if slot['view']=='domain767' else 1536,original_parent_slot=3,
        posthoc_development_layout=slot['view']=='domain767',constructed_damage=slot['view']=='domain_dropped',model_reader_fidelity_verified=False)


def slots():
    jobs=[('none',None,None),('full',None,None),('read','flat1061',0),('read','domain767',0),
          ('read','domain_dropped',0),('read','domain_dropped',1),('read','domain767',1),('read','flat1061',1)]
    return [dict(slot=i+1,kind=k,profile='rivet',method='task',view=v,generation=0 if k=='read'else None,
        read_repeat=r,budget=(768 if v=='domain767'else 1536)if k=='read'else None,
        key=':'.join(map(str,(k,v,r))))for i,(k,v,r)in enumerate(jobs)]


def questions(slot):return inputs()['queries']['task']


def request(slot):
    if type(slot.get('slot'))is not int or slot not in slots():raise ValueError('Outside fixed eight slots')
    if slot['kind']in('none','full'):
        original=next(s for s in old.slots()if s['kind']==slot['kind'])
        return old.request(original)
    common=old.old.seed.seed.seed.base.base.old.old
    req=choice_reader.make_request(view(slot)['prompt'],questions(slot),as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':common.grouped_support.SYSTEM,**req,'prompt':common.COMMON+req['prompt']}


def implementation():
    files=old.implementation()
    paths=[up.DEFAULT,up.DEFAULT.with_suffix('.sha256'),ROOT/'scripts/replay_domain_revision.py',ROOT/'benchmarks/domain-template-v2/codec.py',
           HERE.parent/'question-contract-diagnostic-v1/engine.py',*HERE.glob('*.py')]
    files.update({str(p.relative_to(ROOT)):sha(p)for p in paths});return dict(sorted(files.items()))


def values():
    data=inputs()
    proposal=dict(kind='unapproved_domain_template_readonly8',approved=False,new_service_authority=False,
        new_model_calls=0,model_requested=MODEL,max_new_local_cli_attempts=8,aggregate_token_cap=None,money_cap=None,
        local_child_timeout_seconds=180,source_messages=48,unique_public_forms=188,
        person_cases_per_view=94,known=36,unknown=58,stages=dict(controls=2,extractions=0,fixed_view_reads=6),
        intervention='Same original slot3 graph and1061charactercard versus767characterdomain-template. Exact scopes including per-unit nonnegative-integer predicates restore. Standard reader and prefix unchanged. Main views have no graph,source,question,reference,action,priority,alias or unknown edit. The third view separately removes only six domain clauses from the original public projection;it is a constructed test-power diagnostic,not automatic compression performance.',
        endpoint='One fixed generation;two reads*twoorders,allfour correct;94cases/view(36known58unknown). Full source94bothorders,no missing,known gain over none before reads. Missing remains missing.',
        disclosure='One existing fictional48message source;188public forms;two complete public views and a separate constructed domain-erasure diagnostic. No original graph,evidence anchors,reference,old reader responses/scores,author parameters,decoder program or human data in requests.',
        limits='Posthoc selected development card;one fictional person,same-author reference,no independent semantic gold,no generation stability,no source-only new-generation or cross-provider proof.',
        fatal='Control,transport,wire/decode,unknown usage,model,input/view/runtime/guard failure closes remainder. No retry,repair,resume,replenishment or old-scope reuse.',
        execution_condition='Fresh exact eight-attempt user grant,final manifest,exact published source and all three CI jobs and required steps successful. Closed14scope has no reusable slots.',
        condition_revision_candidate_tested=False,production_defaults_changed=False,damage_is_constructed_not_model_compression=True,main_views=['flat1061','domain767'],diagnostic_view='domain_dropped')
    return {'proposal.json':proposal,'sources.json':data['sources'],'queries.public.json':data['queries'],
        'reference.private.json':data['rows'],'views.public.json':{v:view(next(s for s in slots()if s['view']==v))for v in VIEWS},
        'slots.json':slots(),'static-requests.json':{str(s['slot']):request(s)for s in slots()},
        'implementation-sha256.json':implementation()}


def prepare(out):
    out=Path(out);content=values();out.mkdir(parents=True,exist_ok=False)
    for name,value in content.items():(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(dict(files={n:sha(out/n)for n in sorted(content)},new_model_calls=0),indent=2)+'\n')
    return content['proposal.json']


def verify(root,*,reconstruct=True):
    root=Path(root)
    if root.is_symlink()or(root/'manifest.json').is_symlink():raise ValueError('Symlink packet refused')
    m=read(root/'manifest.json')
    if set(m)!={'files','new_model_calls'}or type(m['new_model_calls'])is not int or m['new_model_calls']!=0:
        raise ValueError('Preparation manifest differs')
    if set(m['files'])!=FILES or {p.name for p in root.iterdir()}!=FILES|{'manifest.json'}:raise ValueError('Packet set differs')
    for name,h in m['files'].items():
        f=root/name
        if f.is_symlink()or not f.is_file()or sha(f)!=h:raise ValueError('Frozen packet drift')
    if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Implementation drift')
    if reconstruct and any(digest(read(root/n))!=digest(v)for n,v in values().items()):raise ValueError('Reconstruction differs')
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    print(json.dumps(prepare(parser.parse_args().out),ensure_ascii=False,indent=2))
