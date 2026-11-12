"""Prepare14 unapproved source-only comparisons;never invokes a model."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

old=load('domain_probe_previous_plan',HERE.parent/'heterogeneous-guard-pressure-v1/plan.py')
revision=load('domain_probe_condition_candidate',HERE.parent/'condition-revision-graph-v1/candidate.py')
sha,digest,read,choice_reader=old.sha,old.digest,old.read,old.choice_reader
PROFILES,METHODS=('rivet',),('current','condition_revision')
METHOD_BUDGET={m:1536 for m in METHODS}
MODEL,AS_OF,CAP=old.MODEL,old.AS_OF,14
FILES={'proposal.json','sources.json','queries.public.json','reference.private.json','domain-evidence.private.json',
       'slots.json','static-requests.json','dynamic-rules.json','implementation-sha256.json'}


def inputs():
    original=old.inputs();source=copy.deepcopy(original['sources']['rivet'])
    queries=copy.deepcopy(original['queries']['rivet']);rows=[copy.deepcopy(r)for r in original['rows']if r['person']=='rivet']
    evidence=[]
    for i in range(6):
        declarations=[s for s in source['sources']if s['episode_id']=='project'+str(i)and s['role']=='user'and '余量按非负整数'in s['text']]
        if len(declarations)!=1:raise ValueError('Unique explicit source domain required')
        declared=declarations[0];unit=re.search(r'余量按非负整数([^，。]+)计',declared['text']).group(1)
        anchor=next(r for r in rows if r['case']==str(i)+'_below_boundary')
        for name,value in [('fractional_domain','0.5'),('negative_domain','-1')]:
            ids=[]
            for order,qid in zip(('ab','ba'),anchor['query_ids']):
                q=copy.deepcopy(next(q for q in queries if q['id']==qid));q['id']='domain_%02d_%s_%s'%(i,name,order)
                q['scenario'],n=re.subn(r'余量=\d+'+re.escape(unit),'余量='+value+unit,q['scenario'])
                if n!=1:raise ValueError('One numeric fact changed per new question')
                queries.append(q);ids.append(q['id'])
            rows.append(dict(person='rivet',case=str(i)+'_'+name,query_ids=ids,gold='U',personal_known=False,cohort=name,family='declared_numeric_domain'))
            evidence.append(dict(case=str(i)+'_'+name,source_id=declared['id'],complete_domain_declaration=declared['text'],quantity=value,unit=unit,
                reference_contract='Source declares nonnegative integer quantities;this observation is outside that declared domain. No licensed choice,U. This same-author interpretation must pass the full-source control before card comparison.',
                independently_adjudicated=False))
    return dict(sources={'rivet':source},queries={'rivet':queries},rows=rows,domain_evidence=evidence)


def bank(person):
    if person not in('rivet','shared_rivet'):raise ValueError('Foreign source bank')
    return 'rivet'


def parent(slot):return slot['profile'],slot['method'],slot['budget'],slot['generation']


def slots():
    jobs=[('none','shared_rivet',None,None,None,None,None),('full','rivet',None,None,None,None,None)]
    for g in(0,1):
        for m in METHODS if g==0 else tuple(reversed(METHODS)):
            jobs.append(('extract','rivet',m,1536,g,None,None))
            jobs.extend(('read','rivet',m,1536,g,r,'card')for r in(0,1))
    return [dict(slot=i+1,kind=k,profile=p,method=m,budget=b,generation=g,read_repeat=r,view=v,
        key=':'.join(map(str,(k,p,m,b,g,r,v))))for i,(k,p,m,b,g,r,v)in enumerate(jobs)]


def encoder(method):
    if method not in METHODS:raise ValueError('Foreign method')
    return old.candidate if method=='current'else revision


def bind(slot,answer):
    if slot not in slots()or slot['kind']!='extract':raise ValueError('Foreign extraction')
    return encoder(slot['method']).bind(answer,inputs()['sources']['rivet'],1536)


def request(slot,parents=None):
    if type(slot.get('slot'))is not int or slot not in slots():raise ValueError('Outside fixed14schedule')
    data=inputs();common=old.seed.seed.seed.base.base.old.old
    if slot['kind']=='extract':
        return dict(model=MODEL,system=common.grouped_support.SYSTEM,**encoder(slot['method']).make_request(data['sources']['rivet'],1536))
    if slot['kind']=='none':material=''
    elif slot['kind']=='full':material=old.seed.transcript(data['sources']['rivet'])
    else:
        if parent(slot)not in(parents or {}):return None
        own=next(s for s in slots()if s['kind']=='extract'and parent(s)==parent(slot))
        material=bind(own,parents[parent(slot)])['prompt.md']
    req=choice_reader.make_request(material,data['queries']['rivet'],as_of=AS_OF,answer_format='text',reader_mode='standard')
    return {'model':MODEL,'system':common.grouped_support.SYSTEM,**req,'prompt':common.COMMON+req['prompt']}


def implementation():
    files=old.implementation()
    for p in [*HERE.glob('*.py'),HERE.parent/'condition-revision-graph-v1/candidate.py']:
        files[str(p.relative_to(ROOT))]=sha(p)
    return dict(sorted(files.items()))


def values():
    data=inputs()
    proposal=dict(kind='unapproved_domain_revision14',approved=False,new_service_authority=False,new_model_calls=0,
        model_requested=MODEL,max_new_local_cli_attempts=14,aggregate_token_cap=None,money_cap=None,child_timeout_seconds=180,
        stages=dict(controls=2,independent_extractions=4,card_reads=8),fictional_people=1,existing_source_messages=48,
        unique_public_forms=188,fixed_cases_per_method=94,known=36,unknown=58,old_anchors=82,new_domain_cases=12,
        methods=list(METHODS),whole_character_budget=1536,generations=2,reads=2,orders=2,answers_per_case=8,
        intervention='Existing source-ID encoder versus published condition_revision schema and its existing guidance. Both source-only,1536wholecharacters,old compiler guards and ordinary renderer;not a single-guidance-only causal comparison and not a768generation test.',
        source='Existing consumed rivet development source,not a fresh person or holdout. No old graph/card/response/score is sent.',
        new_questions='For each six projects change only the below-boundary numeric fact to0.5or-1withitsunit. Source-only nonnegative-integer declaration is not repeated in questions. Options,task and other facts stay unchanged. New same-author U reference is separate from82unchanged anchors.',
        control='Full source must retain all94cases in bothorders with known gain over none before any extraction. If the source-domain contract fails full control,stop;do not call this compression loss or revise reference within run.',
        endpoint='Each method fixed94cases. All2generations*2reads*2orders must agree with reference;invalid parent skips onlyits2reads and remains missing. No bestof,silent reference edits or shrinkage.',
        exclusions='Extraction sees only own48messages,budget,generic guidance and schema;not questions,reference,domain audit,author table,oldcard/graph/responses/scores,manualbinding or othergeneration. Reader sees onlyownvalidcard+188questions. No human data or decoder supplement.',
        fatal='Control,transport,wire/decode,unknownusage,model,runtime,guard failures close remainder. Invalid binding/budget skips own2reads. No retry,repair,resume,replenishment or closedbudgetreuse.',
        limits='One consumed fictionalperson,same-author newdomaincontract,no independent semanticgold or populationstability. Changed schema and guidance jointly assessed. This proposal does not execute or grant service authority.',
        execution_condition='Fresh exact14grant bound to final manifest and publishedsource,allthree exactheadCIjobs and requiredsteps successful.',
        production_defaults_changed=False)
    return {'proposal.json':proposal,'sources.json':data['sources'],'queries.public.json':data['queries'],'reference.private.json':data['rows'],
        'domain-evidence.private.json':data['domain_evidence'],'slots.json':slots(),
        'static-requests.json':{str(s['slot']):request(s)for s in slots()if s['kind']!='read'},
        'dynamic-rules.json':dict(slots=[s for s in slots()if s['kind']=='read'],builder='benchmarks/domain-revision-probe-v1/plan.py:request',only_own_valid_parent=True),
        'implementation-sha256.json':implementation()}


def prepare(out):
    out=Path(out);data=values();out.mkdir(parents=True,exist_ok=False)
    for n,v in data.items():(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(dict(files={n:sha(out/n)for n in sorted(data)},new_model_calls=0),indent=2)+'\n')
    return data['proposal.json']


def verify(root,*,reconstruct=True):
    root=Path(root)
    if root.is_symlink()or(root/'manifest.json').is_symlink():raise ValueError('Symlink packet refused')
    m=read(root/'manifest.json')
    if set(m)!={'files','new_model_calls'}or type(m['new_model_calls'])is not int or m['new_model_calls']!=0:raise ValueError('Preparation manifest differs')
    if set(m['files'])!=FILES or{p.name for p in root.iterdir()}!=FILES|{'manifest.json'}:raise ValueError('Frozen packet set differs')
    for n,h in m['files'].items():
        f=root/n
        if f.is_symlink()or not f.is_file()or sha(f)!=h:raise ValueError('Frozen packet drift')
    if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Implementation drift')
    if reconstruct and any(digest(read(root/n))!=digest(v)for n,v in values().items()):raise ValueError('Reconstruction differs')
    return True


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True,type=Path)
    print(json.dumps(prepare(a.parse_args().out),ensure_ascii=False,indent=2))
