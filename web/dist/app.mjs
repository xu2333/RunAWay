import {VERSION,HEADER,length,sourcesFrom,parseJSON,makeRequest,validateAnswer,makeBundle,feedbackReport} from './core.mjs';
import {validateCard,renderCard,cardText,makeOutputSample} from './presentation.mjs';
const $=id=>document.getElementById(id);
let prepared=null, answer=null, lastExport=null, sampleDraft=null;
let session=freshSession();
function freshSession(){return {id:crypto.randomUUID(),demo:false,events:[{type:'opened',at:new Date().toISOString()}],feedback:[],exports:[],output_samples:[]};}
function record(type){session.events.push({type,at:new Date().toISOString()});}
function notify(message,error=false){$('notice').textContent=message;$('notice').classList.toggle('error',error);$('notice').hidden=false;if(error)$('notice').scrollIntoView({behavior:'smooth',block:'center'});}
function show(step){
  if(step==='model'&&!prepared) return notify('先放入材料，点击「整理好，去提炼」。',true);
  if(step==='result'&&!answer) return notify('先粘贴模型结果，或试试虚构示例。',true);
  for(const name of ['source','model','result']) $(name+'-panel').hidden=name!==step;
  document.querySelectorAll('[data-step]').forEach(b=>{if(b.dataset.step===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
}
function guard(fn){return async event=>{const button=event?.currentTarget;if(button?.tagName==='BUTTON')button.classList.add('busy');try{await fn(event);}catch(e){notify(e.message||'操作没有完成，请重试。',true);}finally{button?.classList?.remove('busy');}};}
async function copy(value){
  try{await navigator.clipboard.writeText(value);}catch{
    const area=document.createElement('textarea');area.value=value;document.body.append(area);area.select();const ok=document.execCommand('copy');area.remove();if(!ok)throw Error('浏览器没有允许复制。请在文本框中手动选择并复制，或下载文件。');
  }
}
function download(name,value,type='application/json'){
  const blob=new Blob([typeof value==='string'||value instanceof Blob?value:JSON.stringify(value,null,2)+'\n'],{type});
  const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function invalidate(){prepared=null;answer=null;lastExport=null;$('answer').value='';$('request').value='';$('show-feedback').disabled=true;$('feedback-panel').hidden=true;show('source');$('source-count').textContent=length($('source').value)+' 字符';}
function budget(){return Number($('budget').value);}
function size(){const n=length(HEADER+$('prompt').value+'\n');$('size').textContent=`完整 prompt ${n} / ${budget()} 字符（含边界；不是 token 数）`;$('size').classList.toggle('error',n>budget());}
async function currentBundle(){if(!prepared||!answer)throw Error('请先生成并检查分身。');if(length(HEADER+$('prompt').value+'\n')>budget())throw Error('当前 prompt 超过预算，请先缩短或调整长度上限。');return makeBundle(answer,prepared.sources,$('prompt').value);}
function rememberExport(bundle,type){lastExport={...bundle,at:new Date().toISOString()};session.exports.push(lastExport);record(type);$('show-feedback').disabled=false;$('feedback-version').textContent=`反馈绑定到最近带走的版本 ${lastExport.portable.id.slice(0,12)}。之后在编辑框中的改动不属于该版本。`;}
async function exportVersion(type){const bundle=await currentBundle();rememberExport(bundle,type);return bundle;}
function appendText(parent,tag,value,cls=''){const n=document.createElement(tag);n.textContent=value;if(cls)n.className=cls;parent.append(n);return n;}
function render(){
  $('name').textContent=answer.name;$('tagline').textContent=answer.tagline;$('prompt').value=answer.prompt;
  $('result-kind').textContent=session.demo?'虚构示例 · 不是对你的判断':'引文已核对 · 等你确认的初稿';
  $('share-panel').hidden=!answer.presentation;$('share-legacy').hidden=!!answer.presentation;
  if(answer.presentation){$('share-name').value=answer.name;$('share-tagline').value=answer.tagline;$('share-tell').value=answer.presentation.tell;$('share-boundary').value=answer.presentation.boundary;
    $('share-evidence').textContent=answer.presentation.claim_ids.length?'模型为分享表达关联的判断：'+answer.presentation.claim_ids.join('、'):'目前没有足够判断依据。';resetCardReview();paintCard();}
  const evidence=$('evidence');evidence.replaceChildren();
  const bases={self_report:'自述',observed_choice:'记录中的选择',inference:'待确认的推断',task_requirement:'局部任务要求'};
  for(const c of answer.claims){
    const box=appendText(evidence,'section','','claim');appendText(box,'strong',c.statement);appendText(box,'p',`${c.id} · ${bases[c.basis]} · ${c.scope}`,'small');
    for(const v of c.conditions)appendText(box,'p','条件：'+v,'small');for(const v of c.exceptions)appendText(box,'p','例外：'+v,'small');
    for(const e of c.evidence){const src=prepared.sources.sources.find(s=>s.id===e.source_id);appendText(box,'blockquote',`${src.role} · ${e.relation}\n${e.quote}`);}
  }
  $('unknowns').replaceChildren();for(const v of answer.unknowns)appendText($('unknowns'),'li',v);
  if(!answer.unknowns.length)appendText($('unknowns'),'li','模型未列出未知项；这不表示它了解你的一切。');
  size();show('result');
}
for(const button of document.querySelectorAll('[data-step]'))button.addEventListener('click',()=>show(button.dataset.step));
$('source').addEventListener('input',invalidate);
$('kind').addEventListener('change',()=>{
  invalidate();$('source-hint').textContent=$('kind').value==='trajectory'?'按「用户：」「助手：」「工具：」分段，或粘贴带 role 的来源 JSON。助手的话不会算作你的偏好证据。':'请写自己的经历。对话记录请切换类型，保留谁说了什么。';
});
$('budget').addEventListener('change',()=>{if(prepared){prepared.budget=budget();$('request').value=makeRequest(prepared.sources,budget());}size();});
$('source-file').addEventListener('change',guard(async e=>{const file=e.target.files[0];if(!file)return;if(file.size>64000)throw Error('文件超过 64 KB，请选取相关片段。');$('source').value=await file.text();invalidate();notify('文件已在本页读入，尚未发送到任何模型。');e.target.value='';}));
$('prepare').addEventListener('click',guard(()=>{
  const sources=sourcesFrom($('source').value,$('kind').value);prepared={sources,kind:$('kind').value,budget:budget()};
  $('request').value=makeRequest(sources,budget());record('source_prepared');show('model');
  notify(`整理了 ${sources.sources.length} 段来源，其中 ${sources.sources.filter(s=>s.role==='user').length} 段是用户内容。复制前可以展开检查请求。`);
}));
$('copy-request').addEventListener('click',guard(async()=>{if(!prepared)throw Error('请先整理来源。');await copy($('request').value);record('request_copied');notify('请求已复制。请发给你选择的 LLM，再把完整 JSON 带回来。');}));
$('import').addEventListener('click',guard(async()=>{
  if(!prepared)throw Error('来源已更改，请重新整理请求。');const value=parseJSON($('answer').value);validateAnswer(value,prepared.sources,budget());
  await makeBundle(value,prepared.sources);answer=value;lastExport=null;$('show-feedback').disabled=true;$('feedback-panel').hidden=true;record('response_imported');render();notify('引文、说话者、字段和长度检查通过。请确认它的解释，再带走使用。');
}));
$('prompt').addEventListener('input',size);
$('copy-prompt').addEventListener('click',guard(async()=>{const bundle=await currentBundle();await copy(bundle.portable.text);rememberExport(bundle,'prompt_copied');notify('完整 prompt 已复制。放进真实任务里试一次，用完可以记下反馈。');}));
$('download-prompt').addEventListener('click',guard(async()=>{const b=await exportVersion('prompt_downloaded');download('runaway-prompt.txt',b.portable.text,'text/plain');notify('完整 prompt 已下载。');}));
$('download-portable').addEventListener('click',guard(async()=>{const b=await exportVersion('portable_downloaded');download('portable.json',b.portable);notify('已下载兼容 RunAWay CLI 的 portable.json。');}));
$('download-private').addEventListener('click',guard(async()=>{
  const b=await currentBundle();record('private_archive_downloaded');download('runaway.private.json',{schema_version:1,artifact_type:'browser_session',app_version:VERSION,prepared,answer,edited_prompt:$('prompt').value,...b,session});
  notify('私有档案已下载，含原始材料、详细表征和反馈。请勿直接公开。');
}));
$('demo').addEventListener('click',guard(async()=>{
  if(($('source').value||answer)&&!window.confirm('载入示例会清空当前标签页的材料和反馈。需要保留时请先下载私有档案。继续吗？'))return;
  const response=await fetch('./demo.json');if(!response.ok)throw Error('示例暂时无法载入。');const d=await response.json();
  session=freshSession();session.demo=true;record('demo_loaded');lastExport=null;$('feedback-panel').hidden=true;$('feedback-export').hidden=true;$('feedback-form').reset();$('include-content').checked=false;$('show-feedback').disabled=true;
  $('kind').value='trajectory';$('source').value=JSON.stringify(d.sources,null,2);$('budget').value='1600';
  prepared={sources:sourcesFrom($('source').value,'trajectory'),kind:'trajectory',budget:1600};answer=validateAnswer(d.answer,prepared.sources,1600);
  $('source-count').textContent=length($('source').value)+' 字符';$('answer').value=JSON.stringify(answer,null,2);$('request').value=makeRequest(prepared.sources,1600);
  render();notify('这是预先生成的虚构示例，没有调用模型，也没有推断你的偏好。清空本页后即可开始你自己的。');
}));
$('show-feedback').addEventListener('click',()=>{if(!lastExport)return;$('feedback-panel').hidden=false;$('feedback-version').textContent=`反馈绑定到最近带走的版本 ${lastExport.portable.id.slice(0,12)}。之后在编辑框中的改动不属于该版本。`;$('feedback-panel').scrollIntoView({behavior:'smooth',block:'start'});});
$('feedback-form').addEventListener('submit',guard(event=>{
  event.preventDefault();if(!lastExport)throw Error('先复制或下载 prompt，再记录实际使用反馈。');if(!$('used').checked)throw Error('请在实际使用后记录反馈。');
  const task=$('task').value,response=$('response').value,correction=$('correction').value;
  if(length(task)>12000||length(response)>20000||length(correction)>12000)throw Error('反馈内容过长，请保留相关片段。');
  session.feedback.push({id:crypto.randomUUID(),at:new Date().toISOString(),rating:$('rating').value,harness:$('harness').value,used_in_real_task:true,portable_id:lastExport.portable.id,prompt:lastExport.portable.text,task,assistant_response:response,correction});
  record('feedback_recorded');$('feedback-form').reset();updatePreview();$('feedback-export').hidden=false;notify('反馈已记在当前标签页，还没有上传。可以预览后下载，或去 GitHub 主动提交。');
}));
function updatePreview(){const report=feedbackReport(session,$('include-content').checked);$('feedback-preview').value=JSON.stringify(report,null,2);$('feedback-count').textContent=`本页已记录 ${session.feedback.length} 次使用反馈${session.demo?'（虚构示例）':''}。`;return report;}
$('include-content').addEventListener('change',updatePreview);
$('download-feedback').addEventListener('click',()=>{download('runaway-feedback.json',updatePreview());notify('反馈已下载，尚未提交给开发者。');});
$('github-feedback').addEventListener('click',()=>{
  const safe=feedbackReport(session,false);const counts={};for(const e of safe.events)counts[e.type]=(counts[e.type]||0)+1;
  const compact={app_version:VERSION,origin:safe.origin,operation_counts:counts,ratings:safe.feedback.map(f=>({rating:f.rating,harness:f.harness})),includes_source_text:false};
  const body='我愿意公开以下使用统计，不包含原文、prompt 或自由文本反馈。\n\n```json\n'+JSON.stringify(compact,null,2)+'\n```\n\n其他愿意公开的反馈（可选）：\n';
  window.open('https://github.com/xu2333/RunAWay/issues/new?title='+encodeURIComponent('[Feedback] Browser trial')+'&body='+encodeURIComponent(body),'_blank','noopener,noreferrer');
  notify('已请求打开公开 Issue 草稿；请检查后手动提交。原文和自由文本没有预填。');
});
$('clear').addEventListener('click',()=>{if(!window.confirm('清空本页材料、分身和反馈？此操作不能恢复；请先下载需要保留的私有档案。'))return;session=freshSession();$('source').value='';$('feedback-form').reset();$('include-content').checked=false;$('feedback-export').hidden=true;invalidate();notify('本页材料已清空。已下载的文件需要你在设备上自行删除。');});

function currentCard(){return validateCard({name:$('share-name').value,tagline:$('share-tagline').value,tell:$('share-tell').value,boundary:$('share-boundary').value});}
function resetCardReview(){sampleDraft=null;$('sample-draft').hidden=true;$('sample-public').checked=false;$('share-reviewed').checked=false;for(const id of ['recognizable','amusing','would-share'])$(id).value='unsure';}
function paintCard(){try{renderCard($('share-canvas'),currentCard(),session.demo);$('download-card').href=$('share-canvas').toDataURL('image/png');$('share-canvas').hidden=false;$('share-error').textContent='';}catch(e){$('download-card').removeAttribute('href');$('share-canvas').hidden=true;$('share-error').textContent=e.message;}}
function checkedCard(){if(!answer?.presentation)throw Error('先生成分享卡。');const card=currentCard();if(!$('share-reviewed').checked)throw Error('请先核对卡片上的四段文字并勾选分享确认。');return card;}
for(const id of ['share-name','share-tagline','share-tell','share-boundary'])$(id).addEventListener('input',()=>{resetCardReview();paintCard();});
for(const id of ['recognizable','amusing','would-share'])$(id).addEventListener('change',()=>{sampleDraft=null;$('sample-draft').hidden=true;$('sample-public').checked=false;});
$('copy-card').addEventListener('click',guard(async()=>{await copy(cardText(checkedCard(),session.demo));record('card_copied');notify('卡片文字已复制；随身 prompt 没有改变。');}));
$('download-card').addEventListener('click',event=>{
  try{checkedCard();record('card_download_requested');notify('已请求下载预览中的分享图片，没有上传。');}
  catch(e){event.preventDefault();notify(e.message,true);}
});
async function outputSample(){const card=checkedCard();const bundle=await makeBundle(answer,prepared.sources);return makeOutputSample(card,{recognizable:$('recognizable').value,amusing:$('amusing').value,would_share:$('would-share').value},bundle.profile.id,session.demo?'fictional_demo':'user_submitted');}
$('download-sample').addEventListener('click',guard(async()=>{const sample=await outputSample();session.output_samples.push(sample);download('runaway-output.json',sample);record('output_sample_downloaded');notify('卡片与评分已下载，尚未提交。虚构示例会单独标记。');}));
$('submit-sample').addEventListener('click',guard(async()=>{sampleDraft=await outputSample();$('sample-preview').value=JSON.stringify(sampleDraft,null,2);$('sample-public').checked=false;$('sample-draft').hidden=false;}));
$('open-sample-issue').addEventListener('click',guard(async()=>{
  if(!sampleDraft||!$('sample-public').checked)throw Error('请先预览投稿内容并勾选公开草稿确认。');
  const current=await outputSample();if(current.id!==sampleDraft.id)throw Error('卡片或评分已经改变，请重新预览。');
  const body='我愿意公开以下卡片文字与自评。它不是独立的真实性或传播效果验证。\n\n```json\n'+JSON.stringify(sampleDraft,null,2)+'\n```\n';
  window.open('https://github.com/xu2333/RunAWay/issues/new?title='+encodeURIComponent('[Output] '+sampleDraft.card.name)+'&body='+encodeURIComponent(body),'_blank','noopener,noreferrer');
  record('output_issue_draft_opened');notify('已请求打开 GitHub 公开草稿，请检查后手动提交。打开草稿不计作成功投稿。');
}));
