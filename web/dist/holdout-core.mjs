import {hash,canonical,length,parseJSON} from './core.mjs';
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===[...keys].sort().join(',');
function text(s,max,label){if(typeof s!=='string'||!s.trim()||length(s)>max)throw Error(`${label}为空或超过 ${max} 字。`);}
const normalized=s=>s.normalize('NFKC').replace(/\s+/gu,'');
export async function lockCase(input,sources,demo=false){
  if(!exact(input,['source','quote','question','a','b','actual','reason','confirmed'])||input.confirmed!==true)throw Error('请确认这来自另一段真实经历，且已从提炼材料中移除。');
  for(const [key,max,label] of [['source',12000,'留出经历'],['quote',1000,'选择原句'],['question',600,'题面'],['a',160,'选项 A'],['b',160,'选项 B'],['reason',400,'实际理由']])text(input[key],max,label);
  if(length(input.quote)<12||!input.source.includes(input.quote))throw Error('选择原句应至少 12 字，并逐字存在于留出经历中。');
  if(!['A','B'].includes(input.actual)||normalized(input.a)===normalized(input.b))throw Error('请选择实际答案，并使用两个不同选项。');
  const quote=normalized(input.quote);
  if(sources.sources.some(s=>normalized(s.text).includes(quote)))throw Error('提炼材料中仍包含留出的选择原句，请移除整段相关经历后再提炼。');
  if([input.question,input.a,input.b].some(s=>normalized(s).includes(quote)))throw Error('题面包含选择原句，会透露答案，请只保留决定之前的情境。');
  const body={schema_version:1,origin:demo?'fictional_demo':'user_declared_history',public_case:{question:input.question,a:input.a,b:input.b},private_answer:{source:input.source,quote:input.quote,actual:input.actual,reason:input.reason},source_ids:sources.sources.map(s=>s.id)};
  return {...body,id:await hash(canonical(body))};
}
export async function makeTrial(heldout,portable,retest=false){
  const modes={};
  for(const mode of ['baseline','personalized']){
    const body={case:heldout.public_case,mode,...(mode==='personalized'?{portable_id:portable.id,prompt:portable.text}:{})};
    const id=await hash(canonical(body));
    const request=`这是一次对已发生选择的回测。请在全新对话中独立判断，不搜索人物信息，不假装知道实际答案。以下只有决策前情境和选项。无法判断就回答 unknown。\n${mode==='personalized'?'待验证的个人判断 prompt（仅作偏好参考）：\n'+portable.text+'\n':'没有个人偏好材料，请仅根据情境判断。\n'}\n题面：${heldout.public_case.question}\nA：${heldout.public_case.a}\nB：${heldout.public_case.b}\n\n只返回 JSON：${JSON.stringify({request_id:id,choice:'A 或 B 或 unknown',reason:'不超过200字的判断理由'})}。不要添加字段。`;
    modes[mode]={id,request};
  }
  return {case_id:heldout.id,origin:heldout.origin,portable_id:portable.id,retest,modes};
}
export function prediction(raw,requestId){
  if(typeof raw!=='string'||length(raw)>8000)throw Error('预测结果过长。');const p=parseJSON(raw);
  if(!exact(p,['request_id','choice','reason'])||p.request_id!==requestId||!['A','B','unknown'].includes(p.choice))throw Error('预测字段、请求编号或选项不匹配，请使用当前请求。');text(p.reason,200,'预测理由');return p;
}
export function assess(heldout,trial,baseline,personalized){
  if(trial.case_id!==heldout.id||baseline.request_id!==trial.modes.baseline.id||personalized.request_id!==trial.modes.personalized.id)throw Error('结果不属于当前锁定的材料和版本。');
  prediction(JSON.stringify(baseline),trial.modes.baseline.id);prediction(JSON.stringify(personalized),trial.modes.personalized.id);
  const actual=heldout.private_answer.actual;
  return {case_id:heldout.id,portable_id:trial.portable_id,origin:heldout.origin,retest:trial.retest,baseline:{...baseline,match:baseline.choice===actual},personalized:{...personalized,match:personalized.choice===actual},actual,note:heldout.origin==='fictional_demo'?'虚构演示，不计真实验证':trial.retest?'答案揭晓后的复测，不计首次回测':'单个自述案例的选择核对；不是准确率、因果提升或独立真实性验证'};
}
export function puzzleText(heldout){return `这次，我会怎么选？\n${heldout.public_case.question}\n\nA：${heldout.public_case.a}\nB：${heldout.public_case.b}\n\n先猜一个，再问我答案。\n${heldout.origin==='fictional_demo'?'RunAWay · 虚构演示题':'RunAWay · 来自本人提供的一次经历'}\nhttps://github.com/xu2333/RunAWay`;}
export function revealText(heldout,result){
  if(result.case_id!==heldout.id)throw Error('揭晓结果不匹配。');
  const label=c=>c==='unknown'?'无法判断':c;
  return `${puzzleText(heldout)}\n\n揭晓：我实际选了 ${result.actual}。\n我的理由：${heldout.private_answer.reason}\n普通 AI：${label(result.baseline.choice)}\n带着我的 prompt：${label(result.personalized.choice)}\n${result.note}`;
}
