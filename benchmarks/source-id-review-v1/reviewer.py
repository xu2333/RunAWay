"""Offline source-ID evidence references; no inference, repair or semantic proof."""
import copy,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
spec=importlib.util.spec_from_file_location('source_id_quoted_review',ROOT/'benchmarks/source-review-diagnostic-v1/reviewer.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
VERSION='source_id_review_graph_v1'

def reference_schema(value):
 if isinstance(value,list):return [reference_schema(v)for v in value]
 if not isinstance(value,dict):return copy.deepcopy(value)
 if value.get('type')=='object'and set(value.get('properties',{}))=={'source_id','quote'}:
  return {'type':'object','additionalProperties':False,'required':['source_id'],
   'properties':{'source_id':copy.deepcopy(value['properties']['source_id'])}}
 return {k:reference_schema(v)for k,v in value.items()}
SCHEMA=reference_schema(legacy.SCHEMA)
SCHEMA['properties']['version']['enum']=[VERSION]
CONTRACT='本版证据格式：所有evidence、decisions、contexts、relation_evidence、core_evidence中的锚点只输出{source_id}，不输出quote，不计算字符位置。程序按指定ID提取整条原消息作为逐字证据；源消息角色、时间顺序、引用存在性和原编译器约束继续校验。旧指导里的逐字锚点指该程序提取结果，不要求你抄引文。ID引用不是语义证明，不能据此伪造选择、条件、关系或已执行事实；错误ID拒绝，不猜测或修复。候选图仅是中间数据，按本轮schema重建完整图。'

def normalize(answer,sources):
 legacy.base.base.b.check(answer,SCHEMA)
 legacy.base.base.b.validate_sources(sources)
 index={s['id']:s['text']for s in sources['sources']}
 def expand(value):
  if isinstance(value,list):return [expand(v)for v in value]
  if not isinstance(value,dict):return copy.deepcopy(value)
  if set(value)=={'source_id'}:
   sid=value['source_id']
   if sid not in index:raise ValueError('Undefined source reference')
   text=index[sid]
   if not 0<len(text)<=2000:raise ValueError('Referenced whole message exceeds existing anchor limit')
   return {'source_id':sid,'quote':text}
  return {k:expand(v)for k,v in value.items()}
 result=expand(answer);result['version']=legacy.VERSION
 return result

def bind(answer,sources,budget=1536):
 normalized=normalize(answer,sources)
 files=legacy.bind(normalized,sources,budget)
 files['source-reference.private.json']={'version':VERSION,'answer':copy.deepcopy(answer),
  'normalized_graph':normalized,'whole_message_evidence':True,'semantic_support_verified':False,
  'automatic_quote_correction':False,'source_coverage_verified':False}
 return files

def make_request(sources,draft,budget=1536):
 req=legacy.make_request(sources,draft,budget)
 req['schema']=copy.deepcopy(SCHEMA)
 old='所有引用须逐字来自指定source_id。choice/status的decisions及revision的关系证据须由用户给出，contexts和每个条件也需逐字锚点；引用短而完整。'
 if req['prompt'].count(old)!=1:raise ValueError('Original evidence contract changed')
 req['prompt']=CONTRACT+'\n'+req['prompt'].replace(old,
  '所有证据只给指定source_id，由程序提取整条原文。choice/status的decisions及revision的关系证据须由用户给出；contexts和每个条件同样须引用存在的来源ID。')
 return req
