"""Unmeasured source review variant: model reviews meaning, code enumerates links."""
from pathlib import Path
import copy,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source-coverage-pipeline-v1'))
import producers as p
import auditing as v1
from coverage_contract import digest,exact,string

TEXT={'type':'string'}
SCHEMA=copy.deepcopy(v1.SCHEMA)
ROW=SCHEMA['properties']['coverage']['items']
ROW['required'].remove('unit_ids')
del ROW['properties']['unit_ids']
ROW['properties']['status']['enum']=['reviewed','context_only','uncertain']

def make_inventory_request(sources):
 request=p.make_inventory_request(sources)
 marker='\nINVENTORY_INPUT_JSON:\n'
 prefix,body=request['prompt'].split(marker)
 request['prompt']=(prefix+'内部unit编号仅放id和supersedes字段；scope/condition/content只写偏好含义，不嵌入内部单元编号。'
                    '旧单元保留当时原选择，后续改口只由新单元supersedes回指，不在旧单元正文补写可能过时的后继编号。'
                    +marker+body)
 if len(request['prompt'].encode())>64000:raise ValueError('Full source-only inventory request exceeds64KB')
 return request

def links(ledger):
 v1.check_ledger(ledger)
 return [{'source_id':s['id'],'role':s['role'],
          'decision_unit_ids':[u['id'] for u in ledger['units'] if any(a['source_id']==s['id'] for a in u['decisions'])],
          'context_unit_ids':[u['id'] for u in ledger['units'] if any(a['source_id']==s['id'] for a in u['contexts'])]}
         for s in ledger['sources']]

def make_audit_request(ledger):
 index=links(ledger)
 prompt=(
  '独立重读全部原始来源，审计选择清单是否遗漏或歪曲明确偏好、条件、数值边界、例外、单次限制、局部改口及未定冲突。'
  '不压缩、不补写、不看评测问题或参考答案。source_unit_links由程序按清单中的逐字引用生成，分别列决策与上下文回指；'
  '它只是索引，不证明语义覆盖。特别检查仅放进contexts而未表达在scope/condition/content中的选择或限制。'
  '每条原始消息恰好一条coverage，逐字source_id和本条消息quote，并写具体reason。'
  '用户消息已完成语义检查用reviewed，无法判断用uncertain；助手和工具只用context_only。'
  'reviewed表示读过并做了判断，不表示没有问题；发现问题仍须写findings。不要重新抄写unit关联表。'
  'findings逐项报告missing/unsupported/overgeneralized/bad_update/collapsed_conflict/uncertain，'
  '用逐字anchors、现有unit_ids（新遗漏可为空）和detail。检查supersedes与正文提到的更新编号是否一致。'
  '不得把两个场景合并成全局人格；助手/工具建议不算用户背书。任何finding或用户uncertain均阻止压缩。'
  '未发现才返回空findings；没有发现不是完整性证明。只返回coverage/findings。'
  '\nSOURCE_REVIEW_INPUT_JSON:\n'+p.canonical({'sources':ledger['sources'],
   'unit_inventory':{k:ledger[k] for k in ('units','active','retired','inventory_sha256')},
   'source_unit_links':index}))
 if len(prompt.encode())>64000:raise ValueError('Full source-only review request exceeds64KB')
 return {'system':p.SYSTEM,'prompt':prompt,'schema':copy.deepcopy(SCHEMA)}

def accept_audit(raw,ledger):
 index=links(ledger);answer=p.parse(raw);exact(answer,('coverage','findings'))
 if type(answer['coverage']) is not list or type(answer['findings']) is not list:raise ValueError('Review arrays required')
 sources={s['id']:s for s in ledger['sources']};known={u['id'] for u in ledger['units']}
 seen=set();uncertain=False
 for row in answer['coverage']:
  exact(row,('source_id','status','quote','reason'));sid=row['source_id']
  if type(sid) is not str or sid not in sources or sid in seen:raise ValueError('Review source inventory differs')
  seen.add(sid);string(row['quote']);string(row['reason'])
  if row['quote'] not in sources[sid]['text']:raise ValueError('Review quote not exact')
  if sources[sid]['role']=='user':
   if row['status'] not in ('reviewed','uncertain'):raise ValueError('User review status differs')
   uncertain=uncertain or row['status']=='uncertain'
  elif row['status']!='context_only':raise ValueError('Non-user is context only')
 if seen!=set(sources):raise ValueError('Review must address every selected source exactly once')
 for finding in answer['findings']:
  exact(finding,('kind','anchors','unit_ids','detail'));string(finding['detail'])
  if finding['kind'] not in v1.SCHEMA['properties']['findings']['items']['properties']['kind']['enum']:raise ValueError('Unknown review finding kind')
  ids=finding['unit_ids']
  if type(ids) is not list or any(type(i) is not str or i not in known for i in ids) or len(set(ids))!=len(ids):raise ValueError('Finding units differ')
  if type(finding['anchors']) is not list or not finding['anchors']:raise ValueError('Finding needs source anchors')
  for anchor in finding['anchors']:
   exact(anchor,('source_id','quote'));string(anchor['quote'])
   if type(anchor['source_id']) is not str or anchor['source_id'] not in sources or anchor['quote'] not in sources[anchor['source_id']]['text']:raise ValueError('Finding quote not exact')
 clear=not answer['findings'] and not uncertain
 record={'artifact_type':'source_inventory_review_v2','source_sha256':ledger['source_sha256'],
         'inventory_sha256':ledger['inventory_sha256'],'source_unit_links':index,
         'answer':copy.deepcopy(answer),'clear_for_compression':clear,
         'status':'review_clear_unvalidated' if clear else 'review_flagged',
         'source_review_accounted':True,'inventory_complete_verified':False,
         'semantic_support_verified':False,'fresh_inference_verified':False,'model_calls':0}
 record['id']=digest(record);return record

def require_clear_audit(ledger,audit):
 if type(audit) is not dict or 'answer' not in audit or accept_audit(p.canonical(audit['answer']),ledger)!=audit:raise ValueError('Review/source/inventory binding differs')
 if not audit['clear_for_compression']:raise ValueError('Review flagged findings or uncertainty; no compression admitted')

def make_card_request(ledger,audit,budget):
 require_clear_audit(ledger,audit);return p.make_card_request(ledger,budget)

def accept_card(raw,ledger,audit,budget):
 require_clear_audit(ledger,audit);result=p.accept_card(raw,ledger,budget)
 result['review_id']=audit['id'];result['independent_review_semantics_verified']=False
 return result
