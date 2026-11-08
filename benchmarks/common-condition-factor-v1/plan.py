"""Unapproved20 fixed-view reads of a reversible common-condition factor."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


old=load('orthogonal_consumed_plan',HERE.parent/'source-id-initial-encoding-v1/plan.py')
factor_codec=load('common_factor_candidate',HERE/'codec.py')
query_plan=load('common_factor_question_seed',HERE.parent/'orthogonal-condition-diagnostic-v1/plan.py')
read,sha,digest,choice_reader=old.read,old.sha,old.digest,old.choice_reader
PROFILES,METHODS=old.PROFILES,('flat','factored')
MODEL,AS_OF,CAP,BUDGET=old.MODEL,old.AS_OF,20,1536
MEASURED=HERE.parent/'source-id-initial-encoding-v1/measured.synthetic.json'
SOURCE='8f5aa0a9440628284b4ba0e9bd9f1f434fa2a1c9'
INPUT='15b4569774d3fece2f64870d57dfc5f5c0cf76d27700758676f00b19b0fb05d8'
DIAGNOSTICS=()
FILES={'proposal.json','sources.json','queries.public.json','reference.private.json','views.public.json',
       'slots.json','static-requests.json','implementation-sha256.json'}


def inputs():return query_plan.inputs()


def views():
    data=read(MEASURED)
    if sha(MEASURED)!=MEASURED.with_suffix('.sha256').read_text().strip():raise ValueError('Fixed evidence checksum differs')
    if data['scientific_source_ref']!=SOURCE or data['input_manifest_sha256']!=INPUT or data['all_sources_fictional']is not True or data['status']['status']!='complete':raise ValueError('Foreign or incomplete inherited data')
    result=[]
    for rec in data['records']:
        if rec['kind']!='extract'or rec['method']!=old.METHODS[1]:continue
        slot=next(s for s in old.slots()if s['slot']==rec['slot'])
        bound=old.bind(slot,json.loads(rec['raw']))
        if rec['artifact']is None or bound['prompt.md']!=rec['artifact']['prompt']:raise ValueError('Inherited card differs')
        flat=bound['prompt.md'];factored=factor_codec.factor(flat,768)
        for method,prompt,ceiling in(('flat',flat,1536),('factored',factored['prompt'],768)):
            result.append(dict(profile=rec['profile'],method=method,generation=rec['generation'],prompt=prompt,
                characters=len(prompt),whole_character_ceiling=ceiling,parent_slot=rec['slot'],parent_method=rec['method'],
                parent_raw_sha256=digest(rec['raw']),ordered_projection_roundtrip_exact=True,
                model_reader_fidelity_verified=False))
    if {(v['profile'],v['method'],v['generation'])for v in result}!={(p,m,g)for p in PROFILES for m in METHODS for g in(0,1)}:raise ValueError('Exact four-parent/two-view set differs')
    return result


def parent(slot):return slot['profile'],slot['method'],slot['generation']
def view(slot):return next(v for v in views()if parent(v)==parent(slot))
def questions(slot):return inputs()['queries'][old.bank(slot['profile'])]


def slots():
    jobs=[dict(kind='none',profile=p,method=None,generation=None,read_repeat=None)for p in('shared_chain','shared_qualified')]
    jobs += [dict(kind='full',profile=p,method=None,generation=None,read_repeat=None)for p in PROFILES]
    for repeat in(0,1):
        for generation in(0,1):
            for pi,p in enumerate(PROFILES):
                order=METHODS if(repeat+generation+pi)%2==0 else tuple(reversed(METHODS))
                jobs += [dict(kind='read',profile=p,method=m,generation=generation,read_repeat=repeat)for m in order]
        jobs += [dict(kind='read',profile='otter',method=m,generation=0,read_repeat=repeat)
                 for m in(DIAGNOSTICS if repeat==0 else tuple(reversed(DIAGNOSTICS)))]
    return [dict(s,slot=i+1,budget=(768 if s['method']=='factored' else 1536)if s['kind']=='read'else None,
                 key=':'.join(map(str,(s['kind'],s['profile'],s['method'],s['generation'],s['read_repeat']))))
            for i,s in enumerate(jobs)]


def request(slot):
    if slot not in slots():raise ValueError('Outside fixed20schedule')
    data=inputs()
    text=''if slot['kind']=='none'else old.transcript(data['sources'][slot['profile']])if slot['kind']=='full'else view(slot)['prompt']
    req=choice_reader.make_request(text,questions(slot),as_of=AS_OF,answer_format='text',reader_mode='standard')
    base=old.seed.base.base.old.old
    return {'model':MODEL,'system':base.grouped_support.SYSTEM,**req,'prompt':base.COMMON+req['prompt']}


def implementation():
    files=query_plan.implementation()
    for path in [*HERE.glob('*.py'),HERE/'derived.synthetic.json',HERE/'derived.synthetic.sha256']:
        files[str(path.relative_to(ROOT))]=sha(path)
    return dict(sorted(files.items()))


def values():
    d=inputs()
    proposal=dict(kind='unapproved_common_condition_factor_readonly20',requested_model=MODEL,as_of=AS_OF,
        max_new_local_cli_attempts=CAP,stages=dict(controls=4,extractions=0,fixed_view_reads=16),
        profiles=list(PROFILES),methods=list(METHODS),source_messages=96,unique_public_forms=240,
        person_cases_per_layout=120,known=56,unknown=64,old_case_anchors=88,crossed_unknown_cases=32,
        inherited_source_id_parents=4,answers_per_primary_case=8,
        whole_character_ceilings=dict(flat=1536,factored=768),local_child_timeout_seconds=180,
        intervention='Only public rendering changes:hoist an exact shared ordered predicate prefix into a counted instruction applying separately to the project in this question. All names,scopes,questions,actions,priorities,remaining predicates and unknowns restore byte-exactly to the prior dense projection. No condition erased,paraphrased,guessed or repaired.',
        primary='Same four consumed source-ID parents,two inherited generations/person. Each layout120fixed cases,2parents*2newreads*2ordersallcorrect. Old88anchors and new32crossed unknowns separate. Missing stays in denominator. This is not new extraction or independent generation stability.',
        reader='Unchanged standard reader/prefix. Own flat or factored public prompt plus own120public forms only. The factor guide and predicate text are counted inside the factored prompt. No program decoder,original flat supplement,raw graph,reference,author table,old response/score or real-person data.',
        controls='Two new none banks,two new own full histories. Each full60/60bothorders,no missing and known gain above own none. Both qualify before any fixed-view read;failure closes remainder.',
        selection='Four already-consumed development parents from a completed28call study. Formatting was designed after a24call condition-erasure diagnostic. No independent holdout,semantic acceptance,human-fidelity or cross-provider claim.',
        fatal='Control,transport,wire/decode,unknown usage,model,runtime,guard or input/view drift closes remainder. No retry,repair,resume,replenishment or reuse of closed scopes.',
        aggregate_token_cap=None,money_cap=None,approved=False,new_service_authority=False,new_model_calls=0,
        program_projection_roundtrip_verified=True,model_reader_fidelity_verified=False,
        independent_holdout=False,production_default_changed=False,old_sources_cards_scores_modified=False,
        execution_condition='Fresh direct finite20grant and exact published implementation all three CI jobs and required steps completed successfully.')
    return {'proposal.json':proposal,'sources.json':d['sources'],'queries.public.json':d['queries'],
            'reference.private.json':d['rows'],'views.public.json':views(),'slots.json':slots(),
            'static-requests.json':{str(s['slot']):request(s)for s in slots()},
            'implementation-sha256.json':implementation()}


def prepare(destination):
    destination=Path(destination);contents=values();destination.mkdir(parents=True,exist_ok=False)
    for name,value in contents.items():(destination/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    (destination/'manifest.json').write_text(json.dumps(dict(files={n:sha(destination/n)for n in sorted(contents)},new_model_calls=0),indent=2)+'\n')
    return contents['proposal.json']


def verify(root,*,reconstruct=True):
    root=Path(root)
    if root.is_symlink()or(root/'manifest.json').is_symlink():raise ValueError('Symlink packet refused')
    manifest=read(root/'manifest.json')
    if set(manifest)!={'files','new_model_calls'}or type(manifest['new_model_calls'])is not int or manifest['new_model_calls']!=0:raise ValueError('Manifest contract differs')
    if set(manifest['files'])!=FILES or{p.name for p in root.iterdir()}!=FILES|{'manifest.json'}:raise ValueError('Packet file set differs')
    for name,fingerprint in manifest['files'].items():
        path=root/name
        if path.is_symlink()or not path.is_file()or sha(path)!=fingerprint:raise ValueError('Frozen packet drift')
    if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Implementation drift')
    if reconstruct and any(read(root/n)!=v for n,v in values().items()):raise ValueError('Reconstruction differs')
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    print(json.dumps(prepare(parser.parse_args().out),ensure_ascii=False,indent=2))
