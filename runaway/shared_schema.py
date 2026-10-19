"""Offline immutable $defs variant of the frozen16reader requests. No backend."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import zipfile
from fractions import Fraction

from .card import canonical, digest
from . import temporal_determinacy as dual

SOURCE_SHA='48330c90142f297bcd9d12dde3d6d4f25fe1e582ad9e34610a795e5d36881cc7'
PREFIX='structural-dual/frozen-source/examples/structural-dual/'
STAGES=('development_jobs','wrong_person_jobs','holdout_jobs')
FIELDS=('strict_answer','reported_status','completion_answer','possible_outcomes')


def load_source(path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('Sealed source archive changed')
    with zipfile.ZipFile(path) as archive:
        manifest=json.loads(archive.read('structural-dual/manifest.json'))
        for name,sha in manifest.items():
            if hashlib.sha256(archive.read('structural-dual/'+name)).hexdigest()!=sha:raise ValueError('Source manifest mismatch')
        read=lambda n:json.loads(archive.read(PREFIX+n))
        return dict(design=read('service-design.synthetic.json'),
            worlds={s:read(s+'-world.synthetic.json') for s in ('development','holdout')},
            expected={s:read(s+'-expected.synthetic.json') for s in ('development','holdout')},
            records={s:read(s+'-program-records.synthetic.json') for s in ('development','holdout')},
            reports={s:read(s+'-report.synthetic.json') for s in ('development','holdout')})


def expanded(schema):
    root=copy.deepcopy(schema);definitions=root.pop('$defs',{})
    if definitions and set(definitions)!={'answer'}:raise ValueError('Unexpected definitions')
    def walk(value,depth=0):
        if depth>32:raise ValueError('Reference cycle or excessive depth')
        if isinstance(value,list):return [walk(v,depth+1) for v in value]
        if not isinstance(value,dict):return value
        if '$defs' in value:raise ValueError('Nested definitions unsupported')
        if '$ref' in value:
            if set(value)!={'$ref'} or value['$ref']!='#/$defs/answer' or 'answer' not in definitions:raise ValueError('Unsupported reference or siblings')
            return walk(definitions['answer'],depth+1)
        return {k:walk(v,depth+1) for k,v in value.items()}
    return walk(root)


def hoist(request):
    schema=request['schema']
    if '$defs' in schema or '$ref' in canonical(schema):raise ValueError('Original schema already has references')
    answers=schema['properties']['answers'];properties=answers['properties']
    if not properties or set(answers['required'])!=set(properties):raise ValueError('ID coverage changed')
    item=next(iter(properties.values()))
    if any(value!=item for value in properties.values()):raise ValueError('Per-ID schemas differ; cannot hoist')
    variant=copy.deepcopy(request);variant['schema']['$defs']={'answer':copy.deepcopy(item)}
    variant['schema']['properties']['answers']['properties']={k:{'$ref':'#/$defs/answer'} for k in properties}
    prove(request,variant)
    return variant


def prove(original,variant):
    if set(original)!=set(variant) or any(original[k]!=variant[k] for k in original if k!='schema'):raise ValueError('Non-schema request changed')
    if canonical(expanded(variant['schema']))!=canonical(original['schema']):raise ValueError('Expanded schema changed')
    return dict(exact_expansion=True,non_schema_request_unchanged=True,ids_and_required_and_additionalProperties_unchanged=True)


def accepts(instance,schema):
    """Local checker ONLY for the frozen keyword subset, not general JSON Schema.

    Interpret references directly; the separate expansion equality is the
    universal contract proof. Backend acceptance is deliberately untested.
    """
    definitions=schema.get('$defs',{})
    allowed={'type','properties','required','additionalProperties','enum','items','minItems','maxItems','$defs','$ref'}
    def check(value,node,depth=0):
        if depth>40 or set(node)-allowed:raise ValueError('Unsupported schema')
        if '$ref' in node:
            if set(node)!={'$ref'} or node['$ref']!='#/$defs/answer' or 'answer' not in definitions:raise ValueError('Unsupported reference')
            return check(value,definitions['answer'],depth+1)
        types=node.get('type');types=types if isinstance(types,list) else [types]
        matches={'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'null':value is None}
        if any(t not in matches for t in types):raise ValueError('Unsupported schema type')
        if not any(matches[t] for t in types):return False
        if 'enum' in node and value not in node['enum']:return False
        if isinstance(value,dict):
            props=node.get('properties',{})
            if not set(node.get('required',[]))<=set(value):return False
            if node.get('additionalProperties') is False and set(value)-set(props):return False
            if any(not check(v,props[k],depth+1) for k,v in value.items() if k in props):return False
        if isinstance(value,list):
            if not node.get('minItems',0)<=len(value)<=node.get('maxItems',len(value)):return False
            if any(not check(v,node['items'],depth+1) for v in value):return False
        return True
    return check(instance,schema)


def parse_wire(raw):
    if isinstance(raw,bytes):raw=raw.decode('utf-8',errors='strict')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    def constant(value):raise ValueError('Non-JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def wire_result(raw,schema):
    try:
        value=parse_wire(raw)
        return dict(accepted=accepts(value,schema),parsed=value,error=None)
    except (ValueError,UnicodeError,TypeError) as error:return dict(accepted=False,parsed=None,error=type(error).__name__)


def corruptions(response):
    """Predetermined mutations, always first lexical ID, never gold-selected."""
    key=min(response['answers']);row=response['answers'][key];result=[('valid',canonical(response))]
    def add(name,change):
        value=copy.deepcopy(response);change(value);result.append((name,canonical(value)))
    add('missing_query',lambda x:x['answers'].pop(key))
    add('extra_query',lambda x:x['answers'].update({'unexpected-id':copy.deepcopy(row)}))
    def rename(x):x['answers']['renamed-id']=x['answers'].pop(key)
    add('renamed_query',rename)
    for field in FIELDS:add('missing_'+field,lambda x,f=field:x['answers'][key].pop(f))
    add('extra_field',lambda x:x['answers'][key].update(extra='not allowed'))
    add('extra_envelope',lambda x:x.update(extra='not allowed'))
    for field in ('strict_answer','completion_answer'):
        add('illegal_'+field,lambda x,f=field:x['answers'][key].update({f:'X'}))
        add('null_'+field,lambda x,f=field:x['answers'][key].update({f:None}))
    add('illegal_status',lambda x:x['answers'][key].update(reported_status='invented'))
    add('wrong_type',lambda x:x['answers'][key].update(strict_answer=1))
    for name,outcomes in [('empty_outcomes',[]),('too_many_outcomes',[dict(status='chosen',action='x')]*5),
        ('null_chosen_action',[dict(status='chosen',action=None)]),('nonnull_conflict',[dict(status='conflict',action='x')]),
        ('duplicate_outcome',[dict(status='chosen',action='x')]*2),('unsorted_outcomes',[dict(status='unobserved',action=None),dict(status='chosen',action='x')])]:
        add(name,lambda x,v=outcomes:x['answers'][key].update(possible_outcomes=v))
    raw=canonical(response);fragment=canonical(key)+':'+canonical(row)
    result.append(('duplicate_query',raw.replace(fragment,fragment+','+fragment,1)))
    field=canonical('strict_answer')+':'+canonical(row['strict_answer'])
    result.append(('duplicate_field',raw.replace(field,field+','+field,1)))
    result.append(('NaN',raw.replace(field,canonical('strict_answer')+':NaN',1)))
    result.append(('invalid_utf8',raw.encode()+b'\xff'))
    result.append(('whitespace',' \n'+raw+'\t'))
    result.append(('wrapped_array',canonical([response])))
    return result


def score_fingerprint(score):
    """Fingerprint exact counts and rational macro, not runtime sum rounding."""
    def portable(value):
        if isinstance(value,list):return [portable(v) for v in value]
        if not isinstance(value,dict):return value
        result={k:portable(v) for k,v in value.items() if k!='macro_cluster_accuracy'}
        if 'macro_cluster_accuracy' in value:
            rows=value['paired_clusters'];mean=sum((Fraction(r['correct'],r['planned']) for r in rows),Fraction())/len(rows)
            result['macro_cluster_accuracy_exact']=[mean.numerator,mean.denominator]
        return result
    return digest(canonical(portable(score)))


def scored(source,split,pid,value):
    try:
        if not isinstance(value,dict) or set(value)!={'answers'}:raise ValueError('Wrong output envelope')
        rows=copy.deepcopy(source['records'][split]['intact_dual_program']);rows[pid]=value['answers']
        score=dual.score_records(source['worlds'][split],rows,source['expected'][split],tasks=('current_choice','joint'))
        return dict(status='scored',sha256=score_fingerprint(score),
            strict_missing=score['strict_choice']['joint']['missing'],strict_invalid=score['strict_choice']['joint']['invalid_answers'],
            completion_missing=score['completion_choice']['joint']['missing'],completion_invalid=score['completion_choice']['joint']['invalid_answers'],
            status_missing=score['reported_rule_status']['joint']['missing'],outcome_missing=score['possible_outcomes']['joint']['missing'])
    except (ValueError,TypeError,KeyError) as error:return dict(status='rejected',error=type(error).__name__+':'+str(error))


def audit(source,variants):
    cases=[];job_index={(j['person_id'],stage):j for stage in STAGES for j in source['design'][stage]}
    def trial(job,stage,name,wire):
        original=job_index[(job['person_id'],stage)]['request'];old=wire_result(wire,original['schema']);new=wire_result(wire,job['request']['schema'])
        if old!=new:raise ValueError('Schema acceptance or parse changed')
        split='holdout' if stage=='holdout_jobs' else 'development'
        a=scored(source,split,job['person_id'],old['parsed']);b=scored(source,split,job['person_id'],new['parsed'])
        if a!=b:raise ValueError('Scoring changed')
        cases.append(dict(request_id=job['request_id'],case=name,wire_sha256=hashlib.sha256(wire.encode() if isinstance(wire,str) else wire).hexdigest(),
            old_accepted=old['accepted'],new_accepted=new['accepted'],parse_error=old['error'],score=a))
    for stage in STAGES:
        for job in variants[stage]:
            pid=job['person_id'];split='holdout' if stage=='holdout_jobs' else 'development'
            controls=source['records'][split]
            if stage=='wrong_person_jobs':controls={'wrong_person':controls['wrong_person']}
            for name,rows in controls.items():trial(job,stage,'program:'+name,canonical(dict(answers=rows[pid])))
            baseline=source['records'][split]['wrong_person' if stage=='wrong_person_jobs' else 'intact_dual_program'][pid]
            for name,wire in corruptions(dict(answers=baseline)):trial(job,stage,'mutation:'+name,wire)
    return dict(cases=cases,case_count=len(cases),all_acceptance_equal=True,all_decoded_values_equal=True,all_score_signatures_equal=True,
        semantic_layers='Strict wire contract rejects missing/illegal outputs; offline scorer still preserves their denominators and invalid values. No repair or conversion toU.',external_model_calls=0)


def measure(request,count):
    text=canonical(request)
    return dict(characters=len(text),utf8_bytes=len(text.encode()),actual_local_vocabulary_tokens=count(text) if count else None)


def make_variant(source,count=None):
    result={};lengths=[];proofs=[];ids=set()
    for stage in STAGES:
        result[stage]=[]
        for old in source['design'][stage]:
            request=hoist(old['request']);key=digest(canonical(request))
            if key in ids or key==old['request_id']:raise ValueError('Request identity reused')
            ids.add(key);result[stage].append(dict(person_id=old['person_id'],source_request_id=old['request_id'],request_id=key,request=request))
            proofs.append(dict(source_request_id=old['request_id'],request_id=key,**prove(old['request'],request)))
            before=measure(old['request'],count);after=measure(request,count)
            if count and before!=old['canonical_request_lengths']:raise ValueError('Original whole-request recount changed')
            if before['utf8_bytes']<=after['utf8_bytes']:raise ValueError('No byte savings')
            lengths.append(dict(stage=stage,person_id=old['person_id'],source_request_id=old['request_id'],request_id=key,before=before,after=after))
    if len(ids)!=16:raise ValueError('Frozen16matrix changed')
    totals={side:{unit:sum(row[side][unit] for row in lengths) if count or unit!='actual_local_vocabulary_tokens' else None for unit in ('characters','utf8_bytes','actual_local_vocabulary_tokens')} for side in ('before','after')}
    if count and (totals['before']['actual_local_vocabulary_tokens']!=142763 or totals['after']['actual_local_vocabulary_tokens']>=142763):raise ValueError('Frozen token recount or savings gate failed')
    report=dict(proofs=proofs,whole_request_lengths=lengths,totals=totals,
        savings={unit:dict(absolute=totals['before'][unit]-totals['after'][unit],fraction=(totals['before'][unit]-totals['after'][unit])/totals['before'][unit]) if totals['before'][unit] is not None else None for unit in totals['before']},
        audit=audit(source,result),source_archive_sha256=SOURCE_SHA,request_count=16,backend_compatibility='unmeasured',model_output_equivalence='unmeasured; same formal output language does not imply same sampled model behavior',
        new_external_model_calls=0,experimental_service_tokens=0,token_scope='Whole canonical system/prompt/schema object; not billing tokens. Future unfrozen CLI/API metadata not included. Memory and output contract unchanged.',native_development_usage='Separate host accounting,not0.')
    return result,report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);parser.add_argument('--out',required=True);parser.add_argument('--tokenizer',required=True);args=parser.parse_args()
    root=Path(args.out);root.mkdir(parents=True,exist_ok=False)
    expected='7f4030143c1c477224c5434f8272c662a8b042079a0a584f0a27a1684fe2e1fa'
    if hashlib.sha256(Path(args.tokenizer).read_bytes()).hexdigest()!=expected:raise ValueError('Tokenizer changed')
    import llama_cpp
    model=llama_cpp.Llama(model_path=args.tokenizer,vocab_only=True,n_gpu_layers=0,verbose=False)
    try:
        count=lambda text:len(model.tokenize(text.encode(),add_bos=False,special=False))
        variants,report=make_variant(load_source(args.source),count)
        for name,value in [('requests.synthetic.json',variants),('report.synthetic.json',report)]:
            with (root/name).open('x') as handle:json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')
        print(json.dumps(dict(requests=16,before=report['totals']['before'],after=report['totals']['after'],cases=report['audit']['case_count'],new_model_calls=0)))
    finally:model.close()
