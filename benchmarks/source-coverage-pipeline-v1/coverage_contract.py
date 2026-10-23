"""Offline bookkeeping prototype. No inference, extraction, export or semantics proof."""
import copy,hashlib,json

def digest(value):
 return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def exact(value,keys):
 if type(value) is not dict or set(value)!=set(keys):raise ValueError('Unexpected fields')

def string(value):
 if type(value) is not str or not value.strip():raise ValueError('Nonempty literal string required')

def inventory(sources,units):
 """Validate manually supplied source-only units; never discover missing units."""
 if type(sources) is not list or not sources:raise ValueError('Selected role-labelled sources required')
 index={}
 for i,s in enumerate(sources):
  if type(s) is not dict:raise ValueError('Source object required')
  source_fields={'id','role','text'}
  if 'episode_id' in s:source_fields.add('episode_id');string(s['episode_id'])
  exact(s,source_fields);string(s['id']);string(s['text'])
  if s['id'] in index or s['role'] not in ('user','assistant','tool'):raise ValueError('Source ID/role differs')
  index[s['id']]=(i,s)
 def anchors(values,decisions=False):
  if type(values) is not list or not values:raise ValueError('Exact anchors required')
  positions=[]
  for a in values:
   exact(a,('source_id','quote'));string(a['quote'])
   source=index.get(a['source_id'])
   if source is None or a['quote'] not in source[1]['text']:raise ValueError('Not an exact source quote')
   if decisions and source[1]['role']!='user':raise ValueError('Only user choices')
   positions.append(source[0])
  return positions
 if type(units) is not list or not units:raise ValueError('Explicit source-only inventory required')
 known={};positions={};retired=set()
 for u in units:
  exact(u,('id','kind','scope','condition','content','decisions','contexts','supersedes'))
  for k in ('id','scope','condition','content'):string(u[k])
  if u['id'] in known or u['kind'] not in ('choice','boundary'):raise ValueError('Unit identity/kind differs')
  positions[u['id']]=anchors(u['decisions'],True);anchors(u['contexts'])
  refs=u['supersedes']
  if type(refs) is not list or any(type(r) is not str for r in refs) or len(refs)!=len(set(refs)):raise ValueError('Invalid update references')
  for old in refs:
   if old not in known or max(positions[old])>=min(positions[u['id']]):raise ValueError('Local old unit must precede every new anchor')
   retired.add(old)
  known[u['id']]=u
 return {'kind':'source_unit_inventory_prototype','sources':copy.deepcopy(sources),'units':copy.deepcopy(units),
  'source_sha256':digest(sources),'inventory_sha256':digest(units),'retired':sorted(retired),
  'active':sorted(set(known)-retired),'inventory_complete_verified':False,'semantic_support_verified':False}

def account(ledger,complete_public_prompt,dispositions,budget):
 """Every supplied unit has a disposition. This is not a semantic retention test."""
 rebuilt=inventory(ledger['sources'],ledger['units'])
 if ledger!=rebuilt:raise ValueError('Inventory/source binding changed')
 if type(complete_public_prompt) is not str or not complete_public_prompt.strip():raise ValueError('Complete public prompt required')
 if type(budget) is not int or not 1<=budget<=16000:raise ValueError('Explicit whole-character budget required')
 if type(dispositions) is not list:raise ValueError('Explicit dispositions required')
 known={u['id']:u for u in ledger['units']};seen=set();represented=[];omitted=[]
 for d in dispositions:
  exact(d,('unit_id','status','public_span','reason'))
  uid=d['unit_id']
  if uid not in known or uid in seen:raise ValueError('Unknown/duplicate unit disposition')
  seen.add(uid)
  if uid in ledger['retired']:
   if d['status']!='superseded' or d['public_span'] is not None or d['reason'] is not None:raise ValueError('Retired unit needs local supersession disposition')
  elif d['status']=='represented':
   string(d['public_span'])
   if d['public_span'] not in complete_public_prompt or d['reason'] is not None:raise ValueError('Missing exact public span')
   represented.append(uid)
  elif d['status']=='omitted':
   if d['public_span'] is not None:raise ValueError('Omission is not a public claim')
   string(d['reason']);omitted.append({'unit_id':uid,'kind':known[uid]['kind'],'reason':d['reason']})
  else:raise ValueError('Active units must be represented or explicitly omitted')
 if seen!=set(known):raise ValueError('Unaccounted source units')
 status='budget_unmet' if len(complete_public_prompt)>budget else 'declared_partial_candidate' if omitted else 'accounted_candidate_unvalidated'
 return {'status':status,'whole_public_characters':len(complete_public_prompt),'budget_characters':budget,
  'inventory_sha256':ledger['inventory_sha256'],'prompt_sha256':digest(complete_public_prompt),
  'active_units':len(ledger['active']),'represented_units':len(represented),'omissions':omitted,
  'source_unit_accounting_complete':True,'no_declared_omissions':not omitted,
  'inventory_complete_verified':False,'semantic_retention_verified':False,'behavioral_fidelity_verified':False,
  'no_model_call_or_repair':True}
