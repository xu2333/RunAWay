"""Freeze six unapproved reads of one graph's original/template public views."""
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


up=load('template_readonly_upstream',ROOT/'scripts/replay_guard_pressure.py')
old=up.p
sha,digest,read,choice_reader=old.sha,old.digest,old.read,old.choice_reader
MODEL,AS_OF,CAP=old.MODEL,old.AS_OF,6
PROFILES,METHODS,VIEWS=('quince',),('task',),('flat997','template768')
FILES={'proposal.json','sources.json','queries.public.json','reference.private.json','views.public.json',
       'slots.json','static-requests.json','implementation-sha256.json'}


@lru_cache(maxsize=1)
def inherited():
    up.check();data=read(up.DEFAULT)
    record=next(r for r in data['records']if r['slot']==14)
    answer=up.e.parse_answer(record['raw']);source=data['prepared_files']['sources.json']['quince']
    original=old.candidate.base.bind(answer,source,16000)['prompt.md']
    parsed=old.candidate.dense.parse(old.candidate.restore(original))
    compressed=up.template_render(parsed,768)['prompt']
    if len(original)!=997 or len(compressed)!=768 or up.template_restore(compressed)!=parsed:
        raise ValueError('Original graph or fixed public layout changed')
    return dict(sources={'quince':source},queries={'task':data['prepared_files']['queries.public.json']['quince']},
        rows=[r for r in data['prepared_files']['reference.private.json']if r['person']=='quince'],
        views={'flat997':original,'template768':compressed},answer=answer,
        original_parent_slot=14,original_observation_sha256=data['source_observation_manifest_sha256'])


def inputs():return copy.deepcopy(inherited())
def parent(slot):return slot['profile'],slot['view'],slot['generation']
def view(slot):
    if slot['kind']!='read' or slot['view']not in VIEWS:raise ValueError('Foreign fixed view')
    text=inputs()['views'][slot['view']]
    return dict(profile='quince',view=slot['view'],generation=0,prompt=text,characters=len(text),
        memory_ceiling=1536 if slot['view']=='flat997' else 768,original_parent_slot=14,
        posthoc_development_layout=slot['view']=='template768',model_reader_fidelity_verified=False)


def slots():
    jobs=[('none',None,None),('full',None,None),('read','flat997',0),('read','template768',0),
          ('read','template768',1),('read','flat997',1)]
    return [dict(slot=i+1,kind=k,profile='quince',method='task',view=v,generation=0 if k=='read' else None,
        read_repeat=r,budget=(1536 if v=='flat997' else 768)if k=='read' else None,
        key=':'.join(map(str,(k,v,r))))for i,(k,v,r)in enumerate(jobs)]


def questions(slot):return inputs()['queries']['task']


def request(slot):
    if type(slot.get('slot'))is not int or slot not in slots():raise ValueError('Outside fixed six slots')
    data=inputs()
    if slot['kind']in('none','full'):
        original=next(s for s in old.slots()if s['kind']==slot['kind']and old.bank(s['profile'])=='quince')
        return old.request(original)
    # Derive the unchanged standard-reader prefix using the old public builder.
    original=next(s for s in old.slots()if s['kind']=='read'and s['profile']=='quince'and s['budget']==1536)
    baseline=old.request(original,{old.parent(original):data['answer']})
    unprefixed=choice_reader.make_request(data['views']['flat997'],questions(slot),as_of=AS_OF,
                                        answer_format='text',reader_mode='standard')
    if not baseline['prompt'].endswith(unprefixed['prompt']):raise ValueError('Original reader prefix changed')
    prefix=baseline['prompt'][:-len(unprefixed['prompt'])]
    req=choice_reader.make_request(view(slot)['prompt'],questions(slot),as_of=AS_OF,
                                 answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':baseline['system'],**req,'prompt':prefix+req['prompt']}


def implementation():
    files=old.implementation()
    paths=[up.DEFAULT,up.DEFAULT.with_suffix('.sha256'),ROOT/'scripts/replay_guard_pressure.py',
           HERE.parent/'question-contract-diagnostic-v1/engine.py',*HERE.glob('*.py')]
    files.update({str(p.relative_to(ROOT)):sha(p)for p in paths});return dict(sorted(files.items()))


def values():
    data=inputs()
    proposal=dict(kind='unapproved_guard_template_readonly6',approved=False,new_service_authority=False,
        new_model_calls=0,model_requested=MODEL,max_new_local_cli_attempts=6,aggregate_token_cap=None,money_cap=None,
        local_child_timeout_seconds=180,source_messages=48,unique_public_forms=164,
        person_cases_per_view=82,known=36,unknown=46,stages=dict(controls=2,extractions=0,fixed_view_reads=4),
        intervention='Same actual slot14 graph,original997view versus new768template. No source,question,reference,action,predicate,scope,alias,priority or unknown-field edit. Standard reader and prefix unchanged.',
        endpoint='One generation,each view two independent reads*two option orders,all four correct. Fixed82cases/view. Full source82bothorders,no missing,and known gain over none before reads. Missing remains missing.',
        disclosure='One existing fictional48message source;164public forms;two complete public views. No original graph,evidence anchors,reference,old reader responses/scores,author parameters,decoder program or human data in requests.',
        limits='Posthoc selected development failure;one fictional person,same-author reference,no independent semantic gold,no generation stability,no source-only new-generation or cross-provider proof.',
        fatal='Control,transport,wire/decode,unknown usage,model,input/view/runtime/guard failure closes remainder. No retry,repair,resume,replenishment or old-scope reuse.',
        execution_condition='Fresh exact six-attempt user grant,final manifest,exact published source and all three CI jobs and required steps successful. Closed16scope has no reusable slots.',
        condition_revision_candidate_tested=False,production_defaults_changed=False)
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
