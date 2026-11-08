"""Unapproved24 fixed-card reads; independently cross two previously coupled facts."""
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
damage=load('orthogonal_damage_fixture',HERE.parent/'material-condition-blindspot-v1/check.py')
read,sha,digest,choice_reader=old.read,old.sha,old.digest,old.choice_reader
PROFILES,METHODS=old.PROFILES,old.METHODS
MODEL,AS_OF,CAP,BUDGET=old.MODEL,old.AS_OF,24,1536
MEASURED=HERE.parent/'source-id-initial-encoding-v1/measured.synthetic.json'
SOURCE='8f5aa0a9440628284b4ba0e9bd9f1f434fa2a1c9'
INPUT='15b4569774d3fece2f64870d57dfc5f5c0cf76d27700758676f00b19b0fb05d8'
DIAGNOSTICS=('historical_original','constructed_material_damage')
FILES={'proposal.json','sources.json','queries.public.json','reference.private.json','views.public.json',
       'slots.json','static-requests.json','implementation-sha256.json'}


def inputs():
    data=copy.deepcopy(old.inputs())
    for family in ('chain','qualified'):
        bank=data['queries'][family]
        current=old.corpus.names(family)[1]
        for index,label in enumerate(current):
            for ti,(time,material) in enumerate((('充裕','尚未齐全'),('很紧','齐备'))):
                for fi,feedback in enumerate(('明确不愿','愿意')):
                    n=index*4+ti*2+fi
                    qid='x%02d'%((n*7+3)%16+1)
                    scenario=(f'只根据该人的记录，问完整标识“{label}”这项当前会选的策略。'
                              f'已经明确允许可撤销模拟；准备时间{time}，材料{material}，负责人{feedback}先给反馈。'
                              '记录能否确定唯一完整策略？不凭常识补出未记录的选择。')
                    bank.extend(dict(id=qid+suffix,scenario=scenario,options=dict(zip(('A','B'),options)))
                                for suffix,options in(('_ab',old.corpus.ACTIONS),('_ba',tuple(reversed(old.corpus.ACTIONS)))))
                    person=next(p for p in PROFILES if old.bank(p)==family)
                    data['rows'].append(dict(person=person,case='%d_cross_%d_%d'%(index,ti,fi),
                        query_ids=[qid+'_ab',qid+'_ba'],gold='U',personal_known=False,
                        stratum='preference',cohort='crossed_time_material',family=family))
        pairs=[bank[i:i+2]for i in range(0,len(bank),2)]
        data['queries'][family]=[q for i in range(60)for q in pairs[(i*17+11)%60]]
    data['design'].update(person_cases_per_method=120,known=56,unknown=64,old_case_anchors=88,
                         crossed_unknown_cases=32,unique_public_forms=240,forms_per_own_reader=120)
    return data


def views():
    data=read(MEASURED)
    if sha(MEASURED)!=MEASURED.with_suffix('.sha256').read_text().strip():raise ValueError('Measured evidence checksum differs')
    if (data['scientific_source_ref']!=SOURCE or data['input_manifest_sha256']!=INPUT
            or data['all_sources_fictional']is not True or data['status']['scope_closed']is not True
            or data['status']['status']!='complete' or len(data['records'])!=28):
        raise ValueError('Only the exact closed fictional28comparison is permitted')
    result=[]
    for rec in data['records']:
        if rec['kind']!='extract':continue
        slot=next(s for s in old.slots()if s['slot']==rec['slot'])
        if rec['state']!='completed' or rec['artifact'] is None:raise ValueError('Missing fixed parent')
        bound=old.bind(slot,json.loads(rec['raw']))
        if bound['prompt.md']!=rec['artifact']['prompt']:raise ValueError('Parent public card differs')
        result.append(dict(profile=rec['profile'],method=rec['method'],generation=rec['generation'],
            prompt=bound['prompt.md'],characters=len(bound['prompt.md']),parent_slot=rec['slot'],
            parent_raw_sha256=digest(rec['raw']),constructed_damage=False))
    keys={(v['profile'],v['method'],v['generation'])for v in result}
    if keys!={(p,m,g)for p in PROFILES for m in METHODS for g in(0,1)}:raise ValueError('Fixed parent set differs')
    fixture=damage.read_evidence();diagnostic=damage.diagnose(fixture)
    original=next(r for r in fixture['records']if r['slot']==10)
    for method,prompt in zip(DIAGNOSTICS,(original['artifact']['prompt'],diagnostic['damaged_prompt'])):
        result.append(dict(profile='otter',method=method,generation=0,prompt=prompt,characters=len(prompt),
            parent_slot=10,parent_raw_sha256=digest(original['raw']),constructed_damage=method==DIAGNOSTICS[1]))
    if any(v['characters']>BUDGET for v in result):raise ValueError('Fixed view exceeds original ceiling')
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
    return [dict(s,slot=i+1,budget=BUDGET if s['kind']=='read'else None,
                 key=':'.join(map(str,(s['kind'],s['profile'],s['method'],s['generation'],s['read_repeat']))))
            for i,s in enumerate(jobs)]


def request(slot):
    if slot not in slots():raise ValueError('Outside fixed24schedule')
    data=inputs()
    text=''if slot['kind']=='none'else old.transcript(data['sources'][slot['profile']])if slot['kind']=='full'else view(slot)['prompt']
    req=choice_reader.make_request(text,questions(slot),as_of=AS_OF,answer_format='text',reader_mode='standard')
    base=old.seed.base.base.old.old
    return {'model':MODEL,'system':base.grouped_support.SYSTEM,**req,'prompt':base.COMMON+req['prompt']}


def implementation():
    files=old.implementation()
    for path in [*HERE.glob('*.py'),MEASURED,MEASURED.with_suffix('.sha256'),damage.DEFAULT,
                 damage.DEFAULT.with_suffix('.sha256'),damage.HERE/'check.py']:
        files[str(path.relative_to(ROOT))]=sha(path)
    return dict(sorted(files.items()))


def values():
    d=inputs()
    proposal=dict(kind='unapproved_orthogonal_condition_readonly24',requested_model=MODEL,as_of=AS_OF,
        max_new_local_cli_attempts=CAP,stages=dict(controls=4,extractions=0,fixed_card_reads=16,constructed_diagnostic_reads=4),
        profiles=list(PROFILES),methods=list(METHODS),source_messages=96,unique_public_forms=240,
        person_cases_per_method=120,known=56,unknown=64,old_case_anchors=88,crossed_unknown_cases=32,
        answers_per_primary_case=8,diagnostic_cases_per_view=60,diagnostic_answers_per_case=4,
        whole_character_ceiling=BUDGET,local_child_timeout_seconds=180,
        primary='Same eight unchanged cards from the closed28comparison;two generations,two new reads,two orders. Fixed120cases per method;32crossed unknown and88old anchors reported separately. No new extraction or generation-stability claim.',
        diagnostic='Historical831-character alias card and its755-character developer-constructed material-guard damage,each two reads. This is a separate posthoc mechanism test,not a new encoder score. Retained unknown notes may rescue the LLM boundary;symbolic errors do not predict reader errors.',
        controls='Two none banks and two own full sources;each full60/60bothorders,known choices strictly above own none. Any failure stops before card reads. Diagnostic failure to discriminate is a finding,not an excuse to repair or rerun.',
        reference='New32unknowns reflect absence of any applicable recorded conjunction;no independent semantic adjudication. Existing88cases and old gold remain intact. All-U loses56known primary cases.',
        disclosure='Only own public card and public questions in card reads;controls use none or own48fictional messages. No raw graph,reference,author tables,private bindings,old responses or scores. Two extra diagnostic public prompts are deliberately constructed from already-public fictional evidence.',
        fatal='Control,transport,wire/decode,unknown usage,requested model,owned guard,input/view hash failure closes remainder. No retry,repair,resume,replenishment or closed-scope reuse.',
        aggregate_token_cap=None,money_cap=None,approved=False,new_service_authority=False,new_model_calls=0,
        independent_holdout=False,independent_semantic_gold=False,real_person_fidelity_verified=False,
        production_default_changed=False,old_observations_modified=False,
        execution_condition='Fresh direct finite24approval and exact published implementation all three CI jobs and required steps completed successfully.')
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
