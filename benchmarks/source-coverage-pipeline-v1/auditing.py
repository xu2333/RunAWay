"""Source-only omission audit and gated compression, with no inference backend."""
import copy
import producers as p
from coverage_contract import inventory,digest,exact,string

TEXT={'type':'string'}
ANCHOR={'type':'object','additionalProperties':False,'required':['source_id','quote'],
 'properties':{'source_id':TEXT,'quote':TEXT}}
SCHEMA={'type':'object','additionalProperties':False,'required':['coverage','findings'],
 'properties':{'coverage':{'type':'array','items':{'type':'object','additionalProperties':False,
  'required':['source_id','status','unit_ids','quote','reason'],
  'properties':{'source_id':TEXT,'status':{'type':'string','enum':['covered','not_a_choice','context_only','uncertain']},
   'unit_ids':{'type':'array','items':TEXT},'quote':TEXT,'reason':TEXT}}},
 'findings':{'type':'array','items':{'type':'object','additionalProperties':False,
  'required':['kind','anchors','unit_ids','detail'],
  'properties':{'kind':{'type':'string','enum':['missing','unsupported','overgeneralized','bad_update','collapsed_conflict','uncertain']},
   'anchors':{'type':'array','items':ANCHOR},'unit_ids':{'type':'array','items':TEXT},'detail':TEXT}}}}}

def check_ledger(ledger):
 if inventory(ledger['sources'],ledger['units'])!=ledger:raise ValueError('Inventory/source binding differs')
 p.source_check(ledger['sources'])

def make_audit_request(ledger):
 check_ledger(ledger)
 prompt=(
  '独立审计来源选择清单。逐句重读全部原始来源，不以现有清单的主题为边界；不要压缩，也不参考评测题或参考答案。'
  '检查遗漏的明确选择、范围、具体例外、数值边界、单次限制、未定冲突和错误改口；助手/工具建议不是用户背书。'
  '每条原始消息恰好一条coverage，source_id原样。用户消息：有清单unit则covered，确无明确选择可not_a_choice，不确定用uncertain。'
  'covered的unit_ids必须列出所有以该消息作decisions锚点的清单id，包括后来退役的旧unit；not_a_choice只可用于没有这种锚点的消息。'
  '助手和工具一律context_only、unit_ids为空。每条coverage需该消息逐字quote及简短reason。'
  '发现遗漏/不支持/过度概括/错误局部替代/冲突被抹平/不确定，分别写findings，引用逐字anchors、相关unit_ids（新遗漏可为空）和detail。'
  'coverage逐项填完不代表清单完整，不能把未收录的用户选择当作不存在。发现问题只报告，不补写、不改清单，不替用户选赢家。'
  '没有发现问题才令findings为空；不知道就明说，不为通过检查开绿灯。返回coverage/findings对象。'
  '\nAUDIT_INPUT_JSON:\n'+p.canonical({'sources':ledger['sources'],
   'unit_inventory':{k:ledger[k] for k in ('units','active','retired','inventory_sha256')}}))
 if len(prompt.encode())>64000:raise ValueError('Full source-only audit request exceeds64KB')
 return {'system':p.SYSTEM,'prompt':prompt,'schema':copy.deepcopy(SCHEMA)}

def accept_audit(raw,ledger):
 check_ledger(ledger);answer=p.parse(raw);exact(answer,('coverage','findings'))
 if type(answer['coverage']) is not list or type(answer['findings']) is not list:raise ValueError('Audit arrays required')
 sources={s['id']:s for s in ledger['sources']};units={u['id']:u for u in ledger['units']}
 expected={sid:{u['id'] for u in ledger['units'] if any(a['source_id']==sid for a in u['decisions'])} for sid in sources}
 seen=set();uncertain=False
 def unit_ids(values):
  if type(values) is not list or any(type(v) is not str or v not in units for v in values) or len(values)!=len(set(values)):
   raise ValueError('Unknown/duplicate audit unit IDs')
 for row in answer['coverage']:
  exact(row,('source_id','status','unit_ids','quote','reason'));sid=row['source_id']
  if type(sid) is not str or sid not in sources or sid in seen:raise ValueError('Unknown/duplicate audit source')
  seen.add(sid);string(row['quote']);string(row['reason']);unit_ids(row['unit_ids'])
  if row['quote'] not in sources[sid]['text']:raise ValueError('Audit coverage quote not exact')
  if sources[sid]['role']!='user':
   if row['status']!='context_only' or row['unit_ids']:raise ValueError('Assistant/tool text is context only')
  else:
   if row['status'] not in ('covered','not_a_choice','uncertain'):raise ValueError('User audit status differs')
   if set(row['unit_ids'])!=expected[sid]:raise ValueError('All decision units at this source must be addressed')
   if row['status']=='covered' and not row['unit_ids']:raise ValueError('Covered user needs units')
   if row['status']=='not_a_choice' and expected[sid]:raise ValueError('Inventory choice cannot be labelled absent')
   uncertain=uncertain or row['status']=='uncertain'
 if seen!=set(sources):raise ValueError('Audit must cover every selected source exactly once')
 for finding in answer['findings']:
  exact(finding,('kind','anchors','unit_ids','detail'));unit_ids(finding['unit_ids']);string(finding['detail'])
  if finding['kind'] not in ('missing','unsupported','overgeneralized','bad_update','collapsed_conflict','uncertain'):raise ValueError('Unknown audit finding kind')
  if type(finding['anchors']) is not list or not finding['anchors']:raise ValueError('Audit finding needs exact source anchors')
  for a in finding['anchors']:
   exact(a,('source_id','quote'));string(a['quote'])
   if type(a['source_id']) is not str or a['source_id'] not in sources or a['quote'] not in sources[a['source_id']]['text']:
    raise ValueError('Audit finding quote not exact')
 clear=not answer['findings'] and not uncertain
 record={'artifact_type':'source_inventory_audit_v1','source_sha256':ledger['source_sha256'],
  'inventory_sha256':ledger['inventory_sha256'],'answer':copy.deepcopy(answer),'clear_for_compression':clear,
  'status':'audit_clear_unvalidated' if clear else 'audit_flagged','source_coverage_accounted':True,
  'inventory_complete_verified':False,'semantic_support_verified':False,'fresh_inference_verified':False}
 record['id']=digest(record);return record

def require_clear_audit(ledger,audit):
 if type(audit) is not dict or 'answer' not in audit or accept_audit(p.canonical(audit['answer']),ledger)!=audit:
  raise ValueError('Audit/source/inventory binding differs')
 if not audit['clear_for_compression']:raise ValueError('Inventory audit flagged findings or uncertainty; no compression admitted')

def make_card_request(ledger,audit,budget):
 require_clear_audit(ledger,audit)
 return p.make_card_request(ledger,budget)

def accept_card(raw,ledger,audit,budget):
 require_clear_audit(ledger,audit);result=p.accept_card(raw,ledger,budget)
 result['audit_id']=audit['id'];result['independent_audit_semantics_verified']=False
 return result
