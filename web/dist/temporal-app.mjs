import {sourcesFrom,parseJSON,validateSources,canonical,hash} from './core.mjs';
import {createTemporal} from './temporal-core.mjs';
const $=id=>document.getElementById(id),state={revision:0,prepared:null,artifact:null,delivery:null,demo:null};
let engine,demo;
function notice(message,error=false){$('notice').hidden=false;$('notice').classList.toggle('error',error);$('notice').textContent=message;}
function clearDelivery(){state.artifact=null;state.delivery=null;$('delivery-panel').hidden=true;$('domains').replaceChildren();delete $('domains').dataset.artifactId;for(const id of ['copy-prompt','download-prompt','download-portable','download-private'])$(id).disabled=true;}
function sourceChanged(){state.revision++;state.prepared=null;state.demo=null;clearDelivery();$('exchange-panel').hidden=true;$('request').value='';$('answer').value='';$('demo-note').hidden=true;}
function answerChanged(){state.revision++;state.demo=null;clearDelivery();$('demo-note').hidden=true;}
function inputSources(){const raw=$('source').value;return raw.trim().startsWith('{')?validateSources(parseJSON(raw)):sourcesFrom(raw,$('kind').value);}
async function prepare(){
 const revision=++state.revision;clearDelivery();state.prepared=null;$('exchange-panel').hidden=true;
 try{const sources=inputSources(),request=await engine.makeRequest(sources);if(revision!==state.revision)return false;state.prepared={sources,request};$('request').value=request;$('exchange-panel').hidden=false;notice('请求已准备好。检查来源后，复制到你选择的 LLM。');return true;}
 catch(error){if(revision===state.revision)notice(error.message,true);return false;}
}
function node(tag,text,className){const el=document.createElement(tag);el.textContent=text;if(className)el.className=className;return el;}
function evidence(artifact){
 const spans=new Map(artifact.source_spans.map(s=>[s.id,s]));$('evidence').replaceChildren();$('unmodeled').replaceChildren();
 const names={regular:'曾经的选择',replace:'明确改变',exception:'情境例外',constraint:'硬约束',clear:'清除偏好',retract:'撤销事件'};
 for(const event of artifact.extraction.events){
  const box=node('div','','event');box.append(node('strong',`${names[event.kind]} · ${event.domain||event.id}`));
  if(event.action)box.append(node('p',event.action));if(event.target)box.append(node('p','撤销 '+event.target));
  if(event.when_all.length)box.append(node('p','同时满足：'+event.when_all.map(l=>l.predicate+(l.equals?'成立':'不成立')).join('，')));
  for(const id of event.span_ids)box.append(node('blockquote',spans.get(id).text));$('evidence').append(box);
 }
 for(const row of artifact.extraction.unmodeled){const box=node('div','','event');box.append(node('p',row.reason),node('blockquote',spans.get(row.span_id).text));$('unmodeled').append(box);}
 if(!artifact.extraction.unmodeled.length)$('unmodeled').append(node('p','所有片段都有事件记录；这仍不证明模型解释正确。'));
}
async function updateDelivery(initial=false){
 if(!state.artifact)return;const revision=++state.revision,artifact=state.artifact;
 state.delivery=null;for(const id of ['copy-prompt','download-prompt','download-portable'])$(id).disabled=true;$('prompt').value='';
 $('delivery-status').textContent='正在检查完整长度…';
 try{
  const build=initial||$('domains').dataset.artifactId!==artifact.id;
  const selected=build?null:[...$('domains').querySelectorAll('input:checked')].map(el=>el.value);
  const renderer=$('format').value==='concise'?engine.renderConcise:engine.render;
  const result=await renderer(artifact,Number($('budget').value),selected);if(revision!==state.revision)return;
  state.delivery=result;$('delivery-panel').hidden=false;$('download-private').disabled=false;
  if(build){$('domains').replaceChildren();$('domains').dataset.artifactId=artifact.id;for(const domain of result.included_domains){const label=node('label',''),box=document.createElement('input');box.type='checkbox';box.value=domain;box.checked=true;box.addEventListener('change',()=>updateDelivery());label.append(box,document.createTextNode(domain));$('domains').append(label);}}
  $('omissions').textContent=result.omitted_domains.length?'你明确略过：'+result.omitted_domains.join('、')+'。未列方面保持未知。':'当前包含所有已建模方面，没有自动删选。';
  const blocked=result.status==='budget_blocked';$('delivery-status').classList.toggle('blocked',blocked);
  $('delivery-status').textContent=blocked?`完整记忆需要 ${result.required_characters} 字符，超过 ${result.budget_characters} 上限。未导出残缺版本；可调整上限，或明确选择完整方面。`:`完整 ${result.required_characters} / ${result.budget_characters} 字符；来源词句和变化关系已检查，解释仍待你核对。Token数未测。`;
  $('prompt').value=result.text??'';for(const id of ['copy-prompt','download-prompt','download-portable'])$(id).disabled=blocked;
  $('result-title').textContent=state.demo?'合成示例的当前判断':'当前判断的初稿';
  return true;
 }catch(error){if(revision===state.revision){notice(error.message,true);$('delivery-status').textContent=error.message;$('delivery-status').classList.add('blocked');}return false;}
}
async function importAnswer(){
 if(!state.prepared)return notice('材料变化后，请先重新生成提取请求。',true);
 const revision=++state.revision,prepared=state.prepared,answer=$('answer').value;clearDelivery();
 try{const artifact=await engine.bind(parseJSON(answer),prepared.sources);if(revision!==state.revision)return;state.artifact=artifact;$('delivery-panel').hidden=false;$('download-private').disabled=false;evidence(artifact);if(!await updateDelivery(true))return;notice('已按事件关系生成当前记忆。请核对原文与条件后再使用。');$('delivery-panel').scrollIntoView({block:'start'});}
 catch(error){if(revision===state.revision)notice(error.message,true);}
}
async function loadDemo(index){
 const c=demo.cases[index];sourceChanged();$('kind').value='experience';$('source').value=JSON.stringify(c.sources,null,2);
 if(!await prepare())return;state.demo=c.id;$('answer').value=JSON.stringify(c.answer,null,2);$('demo-note').textContent='当前为已公开的合成开发示例；载入既有模型结果，不发起新调用，也不是你的档案。';$('demo-note').hidden=false;await importAnswer();
}
async function copy(value){if(!value)return;try{await navigator.clipboard.writeText(value);notice('已复制。只有你在所选服务中发送后，内容才会离开本页。');}catch{notice('无法自动复制，请从文本框中手动复制完整内容。',true);}}
function download(name,value,type='application/json'){
 const blob=new Blob([typeof value==='string'?value:JSON.stringify(value,null,2)+'\n'],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notice('已下载 '+name+'。');
}
async function exportPortable(){
 const delivery=state.delivery,artifact=state.artifact;if(!delivery?.text||!artifact)return;
 const method=delivery.delivery_format==='concise'?'program_rendered_temporal_concise_candidate_v1':'program_rendered_temporal_candidate_v1';
 const revision=state.revision,body={schema_version:1,artifact_type:'portable_expression',status:'candidate_unvalidated',text:delivery.text,profile_id:artifact.id,method};
 const expression={...body,id:await hash(canonical(body))};if(revision!==state.revision)return;download('runaway-temporal.portable.json',expression);
}
async function restore(file){
 if(!file)return;const revision=++state.revision;
 try{
  if(file.size>512000)throw Error('私有档案超过512KB，请用 CLI 处理。');
  const artifact=parseJSON(new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer()));await engine.validate(artifact);if(revision!==state.revision)return;
  sourceChanged();$('source').value=JSON.stringify(artifact.sources,null,2);$('kind').value='experience';if(!await prepare())return;$('answer').value=JSON.stringify(artifact.extraction,null,2);await importAnswer();
 }catch(error){if(revision===state.revision)notice(error.message,true);}
}
try{
 const responses=await Promise.all([fetch('./temporal-protocol.json'),fetch('./temporal-demo.json')]);if(responses.some(r=>!r.ok))throw Error('本地协议或示例未加载。');
 const [protocol,loadedDemo]=await Promise.all(responses.map(r=>r.json()));engine=createTemporal(protocol);demo=loadedDemo;
 $('prepare').disabled=false;$('demo-a').disabled=false;$('demo-b').disabled=false;
 $('source').addEventListener('input',sourceChanged);$('kind').addEventListener('change',sourceChanged);$('answer').addEventListener('input',answerChanged);
 $('prepare').addEventListener('click',prepare);$('import').addEventListener('click',importAnswer);$('budget').addEventListener('input',()=>updateDelivery());
 $('format').addEventListener('change',()=>updateDelivery());
 $('demo-a').addEventListener('click',()=>loadDemo(0));$('demo-b').addEventListener('click',()=>loadDemo(1));
 $('copy-request').addEventListener('click',()=>copy(state.prepared?.request));$('copy-prompt').addEventListener('click',()=>copy(state.delivery?.text));
 $('download-prompt').addEventListener('click',()=>{if(state.delivery?.text)download('runaway-temporal-prompt.txt',state.delivery.text,'text/plain;charset=utf-8');});
 $('download-portable').addEventListener('click',exportPortable);$('download-private').addEventListener('click',()=>{if(state.artifact)download('runaway-timeline.private.json',state.artifact);});
 $('restore').addEventListener('change',()=>restore($('restore').files[0]));
}catch(error){notice(error.message,true);}
