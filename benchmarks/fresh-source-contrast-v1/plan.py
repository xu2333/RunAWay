"""Freeze a new-source card/equal-character-tail probe; no service backend."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


old=load('fresh_contrast_helpers',HERE.parent/'owned-conditions-v1/plan.py')
corpus=load('fresh_contrast_corpus',HERE/'corpus.py')
candidate=load('fresh_contrast_encoder',HERE.parent/'source-order-v3/candidate.py')
read,sha,digest,choice_reader=old.read,old.sha,old.digest,old.choice_reader
PROFILES,METHODS=corpus.PROFILES,('source-order-v3',)
MODEL,AS_OF,CAP,BUDGET='gpt-6.1-sol','2026-11-01',46,1536


def inputs():return corpus.build()
def bank(pid):return corpus.FAMILY[pid] if pid in PROFILES else pid.removeprefix('shared_') if pid in ('shared_tools','shared_editing') else invalid_bank()
def invalid_bank():raise ValueError('Foreign bank')
def parent(slot):return slot['profile'],slot['method'],slot['generation']
def cells():return [(p,'source-order-v3',g) for g in (0,1) for p in (PROFILES if g==0 else reversed(PROFILES))]


def slots():
 jobs=[]
 for family,pair in (('tools',('t0','t1')),('editing',('e0','e1'))):
  jobs+=[('none','shared_'+family,None,None,None,None)]+[('full',p,None,None,None,None) for p in pair]
 jobs+=[('extract',p,m,g,None,None) for p,m,g in cells()]
 order=[(p,m,g,v) for index,(p,m,g) in enumerate(cells()) for v in (('card','tail') if index%2==0 else ('tail','card'))]
 for r in (0,1):jobs+=[('read',p,m,g,r,v) for p,m,g,v in (order if r==0 else reversed(order))]
 return [{'slot':i+1,'kind':k,'profile':p,'method':m,'budget':BUDGET if m else None,'generation':g,'read_repeat':r,'view':v,
          'key':':'.join(map(str,(k,p,m,g,r,v)))} for i,(k,p,m,g,r,v) in enumerate(jobs)]


def bind(slot,answer):
 if slot not in slots() or slot['kind']!='extract':raise ValueError('Only own frozen extraction binds')
 return candidate.bind(answer,inputs()['sources'][slot['profile']],slot['budget'])


def material(pid,prompt,view):
 if view=='card':return prompt
 if view!='tail':raise ValueError('Foreign view')
 raw=old.canonical(inputs()['sources'][pid])
 if len(raw)<len(prompt):raise ValueError('Source shorter than matched material budget')
 return raw[-len(prompt):]


def request(slot,parents=None):
 if slot not in slots():raise ValueError('Outside frozen46schedule')
 d=inputs();pid=slot['profile']
 if slot['kind']=='extract':return {'model':MODEL,'system':old.grouped_support.SYSTEM,**candidate.make_request(d['sources'][pid],BUDGET)}
 if slot['kind']=='none':text=''
 elif slot['kind']=='full':text=old.canonical(d['sources'][pid])
 else:
  if parent(slot) not in (parents or {}):return None
  own=next(s for s in slots() if s['kind']=='extract' and parent(s)==parent(slot))
  text=material(pid,bind(own,parents[parent(slot)])['prompt.md'],slot['view'])
 req=choice_reader.make_request(text,d['queries'][bank(pid)],as_of=AS_OF,answer_format='text',reader_mode='standard')
 return {'model':MODEL,'system':old.grouped_support.SYSTEM,**req,'prompt':old.COMMON+req['prompt']}


def implementation():
 locked=read(HERE/'encoder-lock.json')['files']
 if any(sha(ROOT/p)!=h for p,h in locked.items()):raise ValueError('Frozen merged encoder/dependency drift')
 files=list(HERE.glob('*.py'))+[HERE/'encoder-lock.json']
 return dict(sorted({**locked,**{str(p.relative_to(ROOT)):sha(p) for p in files}}.items()))


def values():
 d=inputs()
 return {'proposal.json':{'kind':'unapproved_fresh_source_contrast46','model':MODEL,'as_of':AS_OF,'max_new_local_cli_attempts':CAP,
  'stages':{'controls':6,'source_only_extractions':8,'card_reads':16,'matched_raw_tail_reads':16},
  'source_messages':48,'distinct_public_forms':48,'profile_cases':48,'known':32,'unknown':16,'personal_known':20,
  'two_template_paired_families_not_four_independent_authors':True,'encoder_unchanged_from_pr38':True,
  'whole_public_character_cap':BUDGET,'generations_per_profile':2,'reads_per_view':2,
  'control':'Both fulls per family12/12bothorders,no missing,personal-known>shared-banknone.All4fulls before extraction7;any failure closes.',
  'endpoint':'Each view48cases,2fresh cards*2reads*2orders all correct;missing parents stay missing.No old pooling or best-of.',
  'tail':'Suffix of complete canonical role-labelled source JSON,exactly own whole-card character count;may start mid-message/JSON,no repair. Equal characters,not tokens. One distinct tail per own producer length.',
  'pair_rescoring':'Use same completed card reads against opposite-person gold only on20predeclared divergent personal cases. No new wrong-card requests or independent evidence;algebraically dependent diagnostic.',
  'invalid_product':'Own parent invalid skips its4card/tailreads;no repair/replacement/missing denominator removal.',
  'fatal':'Control/transport/wire/decode/unknownusage/model/runtime/inputhash/guard failure closes scope.Intent counts if receipt unknown.',
  'source_only':'Own source,budget,header/guide,guidance/schema only;no questions,reference,old outputs/scores,manual binding or case feedback.',
  'all_extractions_before_any_read':True,'aggregate_token_cap':None,'money_cap':None,'timeout_per_local_child_seconds':180,
  'max_nominal_timeout_sum_seconds':8280,'not_spend_or_total_duration_cap_or_cancellation_guarantee':True,
  'retry':False,'repair':False,'resume':False,'replenishment':False,'unused_slots_expire':True,
  'independent_holdout':False,'independent_semantic_acceptance':False,'real_person_fidelity_verified':False,
  'development_informed_scene_taxonomy':True,'new_original_inventory_coverage':0,'approved':False,'new_service_authority':False,'production_default_changed':False},
  'sources.json':d['sources'],'queries.public.json':d['queries'],'reference.consumed-development.private.json':{k:d[k] for k in ('rows','legacy_rows','disputed_rows')},
  'design.json':d['design'],'slots.json':slots(),'static-requests.json':{s['key']:request(s) for s in slots() if s['kind']!='read'},
  'dynamic-rules.json':{'slots':[s for s in slots() if s['kind']=='read'],'builder':'benchmarks/fresh-source-contrast-v1/plan.py:request','own_parent_only':True},
  'implementation-sha256.json':implementation()}


def prepare(out):
 data=values();out.mkdir(parents=True,exist_ok=False)
 for n,v in data.items():(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 (out/'manifest.json').write_text(json.dumps({'files':{n:sha(out/n) for n in sorted(data)},'new_model_calls':0},indent=2)+'\n')
 return data['proposal.json']


def verify(root,*,reconstruct=True):
 for p,h in read(root/'manifest.json')['files'].items():
  if Path(p).is_absolute() or '..' in Path(p).parts or (root/p).is_symlink() or sha(root/p)!=h:raise ValueError('Frozen input drift')
 if read(root/'implementation-sha256.json')!=implementation():raise ValueError('Implementation drift')
 if reconstruct and any(read(root/n)!=v for n,v in values().items()):raise ValueError('Reconstructed input drift')
 return True


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.out),indent=2))
