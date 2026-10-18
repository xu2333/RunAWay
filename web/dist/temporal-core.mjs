import {canonical,hash,validateSources} from './core.mjs';
import {requireIntact} from './text-integrity.mjs';

const length=text=>[...text].length;
const nonempty=text=>!/^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u.test(text);
function exact(value,keys,label){
 if(!value||Array.isArray(value)||typeof value!=='object'||Object.keys(value).sort().join('|')!==[...keys].sort().join('|'))throw Error(`${label}字段不完整。`);
}
function text(value,label,max){
 if(typeof value!=='string'||!nonempty(value)||length(value)>max||/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value)||/<!-- runaway:/i.test(value)||value.includes('<|im_'))throw Error(`${label}为空、过长或包含控制标记。`);
 requireIntact(value,label);return value;
}
function lines(value){
 const chars=[...value],result=[];let start=0;
 for(let i=0;i<chars.length;i++)if(/[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/u.test(chars[i])){
  if(chars[i]==='\r'&&chars[i+1]==='\n')i++;
  result.push(chars.slice(start,i+1).join(''));start=i+1;
 }
 if(start<chars.length)result.push(chars.slice(start).join(''));return result;
}
const KINDS=['regular','replace','exception','constraint','clear','retract'];
const EVENT_KEYS=['id','kind','domain','action','strength','when_all','target','span_ids'];

export function createTemporal(protocol){
 if(protocol.version!==1||typeof protocol.instruction_prefix!=='string'||!protocol.schema)throw Error('时序协议版本无效。');
 async function spans(sources){
  validateSources(sources);const result=[];
  for(const source of sources.sources){
   if(source.role!=='user')continue;
   let offset=0;
   for(const line of lines(source.text)){
    const end=offset+length(line);
    if(nonempty(line))result.push({id:'s-'+(await hash(canonical([source.id,offset,end,line]))).slice(0,20),source_id:source.id,start:offset,end,text:line});
    offset=end;
   }
  }
  if(!result.length||result.length>1000)throw Error('请选择1–1000个非空来源行；不会自动截断。');return result;
 }
 async function makeRequest(sources){
  const units=await spans(sources);
  if(new TextEncoder().encode(canonical(units)).length>256000)throw Error('这次来源超过256KB，请明确选择片段。');
  return protocol.instruction_prefix+'INPUT_JSON:\n'+canonical({spans:units,schema:protocol.schema});
 }
 async function bind(answer,sources){
  exact(answer,['scope','events','unmodeled'],'事件提取');text(answer.scope,'适用范围',300);
  const units=await spans(sources),byId=new Map(units.map(s=>[s.id,s]));
  if(!Array.isArray(answer.events)||answer.events.length>300)throw Error('最多接收300个事件，不会静默删选。');
  const seen=new Set(),used=new Set();
  for(const e of answer.events){
   exact(e,EVENT_KEYS,'事件');
   if(typeof e.id!=='string'||!/^[A-Za-z0-9_.-]{1,64}$/.test(e.id)||seen.has(e.id))throw Error('事件ID须为唯一的短ASCII标识。');
   if(!KINDS.includes(e.kind)||typeof e.strength!=='number'||!Number.isInteger(e.strength)||e.strength<0||e.strength>10)throw Error('事件类型或强度无效。');
   for(const field of ['domain','action','target']){
    requireIntact(e[field],field);if(length(e[field])>200)throw Error('事件字段过长。');if(e[field])text(e[field],field,200);
   }
   if(!Array.isArray(e.when_all)||e.when_all.length>12)throw Error('条件须为最多12项的“同时满足”。');
   const predicates=new Set();
   for(const l of e.when_all){
    exact(l,['predicate','equals'],'条件');text(l.predicate,'条件',100);
    if(typeof l.equals!=='boolean'||predicates.has(l.predicate))throw Error('条件重复、矛盾或不是布尔值。');predicates.add(l.predicate);
   }
   if(e.kind==='retract'){
    if(e.domain||e.action||e.when_all.length||e.strength||!seen.has(e.target))throw Error('撤销必须指向一个更早的事件。');
   }else if(e.kind==='clear'){
    if(!e.domain||e.action||e.target||e.when_all.length||e.strength)throw Error('清除事件只指定领域。');
   }else{
    if(!e.domain||!e.action||e.target)throw Error('偏好事件须有领域和选择，不应带撤销目标。');
    const conditional=['exception','constraint'].includes(e.kind);
    if(conditional!==Boolean(e.when_all.length))throw Error('只有例外或硬约束使用条件。');
    if(conditional&&e.strength)throw Error('冲突的条件规则不会按强度擅自取舍。');
   }
   if(!Array.isArray(e.span_ids)||!e.span_ids.length||e.span_ids.some(s=>typeof s!=='string'||!byId.has(s))||new Set(e.span_ids).size!==e.span_ids.length)throw Error('来源片段未知、缺失或重复。');
   const phrases=[...(e.domain?[e.domain]:[]),...(e.action?[e.action]:[]),...e.when_all.map(l=>l.predicate)];
   if(phrases.some(phrase=>!e.span_ids.some(id=>byId.get(id).text.includes(phrase))))throw Error('领域、选择和条件用词必须原样出现在所引用的片段中。');
   seen.add(e.id);for(const id of e.span_ids)used.add(id);
  }
  if(!Array.isArray(answer.unmodeled))throw Error('未建模片段须明确列出。');const unmodeled=new Set();
  for(const row of answer.unmodeled){
   exact(row,['span_id','reason'],'未建模片段');
   if(typeof row.span_id!=='string'||!byId.has(row.span_id)||used.has(row.span_id)||unmodeled.has(row.span_id))throw Error('未建模片段未知、重复或已用于事件。');
   text(row.reason,'未建模原因',300);unmodeled.add(row.span_id);
  }
  if(new Set([...used,...unmodeled]).size!==byId.size)throw Error('每个来源片段都须有事件或明确的未建模原因。');
  const body={schema_version:1,artifact_type:'temporal_preference_candidate',sources,source_sha256:await hash(canonical(sources)),extraction:answer,source_spans:units,validation:protocol.validation};
  return {...body,id:await hash(canonical(body))};
 }
 async function validate(artifact){
  exact(artifact,['schema_version','artifact_type','sources','source_sha256','extraction','source_spans','validation','id'],'私有事件档案');
  const expected=await bind(artifact.extraction,artifact.sources);
  if(canonical(expected)!==canonical(artifact))throw Error('事件档案或来源校验发生变化。');return artifact;
 }
 async function effective(artifact,through=null){
  await validate(artifact);let events=artifact.extraction.events;
  if(through!==null){const i=events.findIndex(e=>e.id===through);if(i<0)throw Error('不存在该事件截止点。');events=events.slice(0,i+1);}
  const disabled=new Set();
  for(let i=events.length-1;i>=0;i--){const e=events[i];if(!disabled.has(e.id)&&e.kind==='retract')disabled.add(e.target);}
  const active=events.filter(e=>!disabled.has(e.id)&&e.kind!=='retract'),domains=[...new Set(events.filter(e=>e.domain).map(e=>e.domain))],result=Object.create(null);
  for(const domain of domains){
   let items=active.filter(e=>e.domain===domain),clear=-1;items.forEach((e,i)=>{if(e.kind==='clear')clear=i;});items=items.slice(clear+1);
   let replacement=-1;items.forEach((e,i)=>{if(e.kind==='replace')replacement=i;});
   const regular=items.filter((e,i)=>['regular','replace'].includes(e.kind)&&i>=replacement),strongest=Math.max(-1,...regular.map(e=>e.strength));
   result[domain]={regular:regular.filter(e=>e.strength===strongest),exception:items.filter(e=>e.kind==='exception'),constraint:items.filter(e=>e.kind==='constraint')};
  }
  return result;
 }
 function matches(e,context){
  if(e.when_all.some(l=>Object.hasOwn(context,l.predicate)&&context[l.predicate]!==l.equals))return false;
  return e.when_all.every(l=>Object.hasOwn(context,l.predicate))?true:null;
 }
 async function resolve(artifact,domain,context,through=null){
  if(!context||Array.isArray(context)||typeof context!=='object'||Object.values(context).some(v=>typeof v!=='boolean'))throw Error('情境须明确给出条件的true或false。');
  const rules=(await effective(artifact,through))[domain]??{};
  for(const kind of ['constraint','exception','regular']){
   const candidates=rules[kind]??[],unknown=candidates.filter(e=>matches(e,context)===null),selected=candidates.filter(e=>matches(e,context)===true);
   if(unknown.length)return {status:'context_unknown',action:null,event_ids:unknown.map(e=>e.id)};
   if(selected.length){const actions=[...new Set(selected.map(e=>e.action))];return {status:actions.length===1?'chosen':'conflict',action:actions.length===1?actions[0]:null,event_ids:selected.map(e=>e.id)};}
  }
  return {status:'unobserved',action:null,event_ids:[]};
 }
 async function render(artifact,budgetChars,domains=null,count=null,budgetTokens=null){
  if(typeof budgetChars!=='number'||!Number.isInteger(budgetChars)||budgetChars<1)throw Error('需要正整数的完整字符预算。');
  if(budgetTokens!==null&&(typeof count!=='function'||!Number.isInteger(budgetTokens)||budgetTokens<1))throw Error('Token预算须提供实际分词器，不能按字符估计。');
  const rules=await effective(artifact),domainOrder=[...new Set(artifact.extraction.events.filter(e=>e.domain).map(e=>e.domain))],wanted=domains??domainOrder;
  if(!Array.isArray(wanted)||wanted.some(d=>typeof d!=='string'||!Object.hasOwn(rules,d))||new Set(wanted).size!==wanted.length)throw Error('请选择不重复的已有领域。');
  const quote=s=>'「'+s+'」',groups=[];
  for(const domain of wanted){
   const rule=rules[domain],actions=[...new Set(rule.regular.map(e=>e.action))],parts=['常规'+(actions.length===1?quote(actions[0]):actions.length?'未定（等强冲突）':'未知')];
   for(const [kind,label] of [['exception','例外'],['constraint','硬约束']])for(const e of rule[kind]){
    const condition=e.when_all.map(l=>quote(l.predicate)+(l.equals?'成立':'不成立')).join('且');parts.push(label+'若'+condition+'则'+quote(e.action));
   }
   groups.push('【'+domain+'】'+parts.join('；')+'。');
  }
  let output=protocol.header+artifact.extraction.scope+'\n硬约束优先于例外，例外优先于常规；同层冲突或条件不明则不判断。\n';
  if(artifact.extraction.unmodeled.length)output+='另有未建模来源，以下解释可能不完整。\n';output+=groups.join('\n')+'\n';
  const units=count?count(output):null;if(units!==null&&(!Number.isInteger(units)||units<0))throw Error('分词器返回了无效计数。');
  const accepted=length(output)<=budgetChars&&(budgetTokens===null||units<=budgetTokens);
  return {status:accepted?'candidate_unvalidated':'budget_blocked',text:accepted?output:null,required_characters:length(output),required_tokens:units,budget_characters:budgetChars,budget_tokens:budgetTokens,included_domains:wanted,omitted_domains:domainOrder.filter(d=>!wanted.includes(d)),source_unmodeled_spans:artifact.extraction.unmodeled.length,historical_reconstruction_supported:false,source_semantic_fidelity_verified:false,model_quality_measured:false,interpretation:protocol.interpretation};
 }
 return {spans,makeRequest,bind,validate,effective,resolve,render};
}
