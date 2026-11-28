import {Session} from './session.mjs';
import {adapters,BOUNDARY} from '../../../packages/harnesses/index.mjs';
import {makeBundle as harnessBundle} from '../../../packages/harnesses/bundle.mjs';
import {length,sourcesFrom} from '../../../web/dist/core.mjs';
import {copyText,saveFile,cleanExports} from './io.mjs';
import {pack,recognize,readConversationFile} from './conversation-import.mjs';
import {clipboardMessages,plainParagraphs,groupParagraphs} from './clipboard-messages.mjs';
import {createPicker} from './conversation-picker.mjs';
import demo from './paper-crane.json';

const $=id=>document.getElementById(id),session=new Session();
let imported=null, copiedMessages=null, pastedParagraphs=null, pendingPaste=null;
let fictional=false,active=false,storageReady=Promise.resolve();
function notify(text,error=false){$('notice').hidden=false;$('notice').textContent=text;$('notice').classList.toggle('error',error);}
function show(step){
  if(step==='model'&&!session.prepared)return notify('请先放入经历并整理请求。',true);
  if(step==='result'&&!session.answer&&!session.portable)return notify('请先导入提炼结果或已有的 portable.json。',true);
  if(step==='model'){
    const roles={user:'你',assistant:'助手',tool:'工具',context:'背景'};
    const counts=new Map();
    for(const {role} of session.prepared.sources.sources)counts.set(role,(counts.get(role)??0)+1);
    $('excerpt').hidden=!imported;
    $('source-summary').textContent='这份请求含有'+Array.from(counts,([role,n])=>roles[role]+'的 '+n+' 段文字').join('、')+'。';
  }
  if(step==='source'){
    const pair=!copiedMessages && unlabelledPair();
    $('clipboard-review').hidden=!copiedMessages;
    $('paragraph-review').hidden=!pastedParagraphs;
    $('prepare').textContent=pastedParagraphs?'确认说话人和分段，生成请求 →':'生成提炼请求 →';
    $('confirm-pair').hidden=!pair;
    $('prepare').hidden=!!pair || !!copiedMessages;
  }
  $('intro').hidden=step!=='source';
  for(const name of ['source','model','result'])$(name+'-panel').hidden=name!==step;
  document.querySelectorAll('[data-step]').forEach(b=>{if(b.dataset.step===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
}
function guard(fn){return async event=>{
  if(active)return;active=true;const button=event.currentTarget;button.disabled=true;
  try{await storageReady;await fn(event);}catch(e){notify(e.message||'操作没有完成。',true);}
  finally{button.disabled=false;active=false;}
};}
function clearAnswerError(){
  $('answer-repair').hidden=true;
  $('answer').removeAttribute('aria-invalid');
  $('answer-error').textContent='';
  $('repair-request').value='';
  $('repair-status').textContent='';
}
function resetHandoff(){
  clearAnswerError();
  $('source-error').hidden=true;
  $('source').removeAttribute('aria-invalid');
  $('copy-status').hidden=true;
  $('request-preview').open=false;
  $('send-request').open=true;
  $('send-label').textContent='把提炼请求发给模型';
}
function invalidate({keepCopied=false}={}){
  if(!keepCopied) clearPasteReview();
  imported=null;resetHandoff();session.reset();fictional=false;$('reviewed').checked=false;$('request').value='';$('answer').value='';show('source');$('source-count').textContent=length($('source').value)+' 字符 · 最多 64 KB';}
function append(parent,tag,text){const n=document.createElement(tag);n.textContent=text;parent.append(n);return n;}
function updateSize(){const value=session.portable?session.portable.text:BOUNDARY+$('prompt').value+'\n';$('prompt-size').textContent=`完整 prompt ${length(value)} 字符（包含边界，不是 token 数）`;$('reviewed').checked=false;}
function render(){
  const a=session.answer;
  $('zip-status').hidden=true;
  $('install-guide').open=false;
  $('name').textContent=a?.name??'带回来的判断';$('tagline').textContent=a?.tagline??'已有 prompt 已校验文件完整性；尚未验证其来源与保真度。';
  $('result-status').textContent=fictional?'虚构示例 · 不是对你的判断':'等你核对的候选';
  $('own-dialogue').hidden=!fictional;
  $('prompt').value=session.body;$('prompt').readOnly=!!session.portable;
  $('evidence-panel').hidden=!a;$('save-private').disabled=!a;
  $('evidence').replaceChildren();$('unknowns').replaceChildren();
  if(a){for(const c of a.claims){const el=append($('evidence'),'section','');el.className='claim';append(el,'strong',c.statement);append(el,'p','范围：'+c.scope);for(const s of c.conditions)append(el,'p','条件：'+s);for(const s of c.exceptions)append(el,'p','例外：'+s);for(const e of c.evidence)append(el,'blockquote',e.quote);}for(const u of a.unknowns)append($('unknowns'),'li',u);}
  updateSize();show('result');
}
async function checkedBundle(){if(!$('reviewed').checked)throw Error('请先检查随身 prompt 并勾选确认。');if(!session.portable)session.body=$('prompt').value;return session.bundle();}
async function save(name,value,mime='application/json'){const saved=await saveFile(name,typeof value==='string'||value instanceof Uint8Array?value:JSON.stringify(value,null,2)+'\n',mime);notify(saved.status==='saved'?'系统已完成文件保存。':'已请求下载，请以浏览器文件界面为准。');return saved.status;}
async function readFile(input,max=512000){const file=input.files?.[0];if(!file)return null;if(file.size>max)throw Error(`文件超过 ${max/1000} KB，请选择相关片段。`);try{return new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());}catch{throw Error('文件编码无法识别。请选择 UTF-8 文本文件；原有材料未改变。');}}
function confirmReplace(){return !($('source').value||session.portable||session.answer)||window.confirm('替换当前材料？请先保存想保留的私有档案。');}
for(const b of document.querySelectorAll('[data-step]'))b.addEventListener('click',()=>show(b.dataset.step));
function clearPasteReview(){
  copiedMessages=null; pastedParagraphs=null;
  $('clipboard-rows').replaceChildren(); $('paragraph-rows').replaceChildren();
}
function offerParagraphReview(raw,scroll){
  const paragraphs=plainParagraphs(raw);
  if(!paragraphs || recognize(raw)) return;
  pastedParagraphs=paragraphs;
  for(const {text} of pastedParagraphs){
    const row=document.createElement('label'), check=document.createElement('input');
    check.type='checkbox'; row.append(check);
    append(row,'span',text); $('paragraph-rows').append(row);
  }
  show('source');
  if(scroll) $('prepare').scrollIntoView({block:'nearest'});
}
$('source').addEventListener('paste',event=>{
  const field=event.currentTarget;
  pendingPaste=null;
  if($('kind').value!=='trajectory' || field.selectionStart!==0 ||
     field.selectionEnd!==field.value.length || !event.clipboardData) return;
  const plain=event.clipboardData.getData('text/plain').replace(/\r\n?/g,'\n');
  const messages=clipboardMessages(plain,event.clipboardData.getData('text/html'));
  if(messages) pendingPaste={plain,messages};
});
$('source').addEventListener('input',event=>{
  const paste=pendingPaste;
  pendingPaste=null;
  invalidate();
  const raw=event.currentTarget.value;
  if($('kind').value!=='trajectory' || unlabelledPair()) return;
  if(!paste || paste.plain!==raw){
    offerParagraphReview(raw,event.inputType==='insertFromPaste' || event.data?.includes('\n'));
    return;
  }
  copiedMessages=paste.messages;
  for(const [i,text] of copiedMessages.entries()){
    const row=document.createElement('label'), role=document.createElement('select');
    role.setAttribute('aria-label',`第 ${i+1} 条的说话人`);
    role.add(new Option('我','user'));role.add(new Option('助手','assistant'));
    role.value=i%2===0?'user':'assistant';
    row.append(role);
    append(row,'span',text);
    $('clipboard-rows').append(row);
  }
  show('source');
  $('clipboard-review').scrollIntoView({block:'nearest'});
});
$('confirm-messages').addEventListener('click',guard(async()=>{
  if(!copiedMessages) return;
  const roles=$('clipboard-rows').querySelectorAll('select');
  presentTurns(copiedMessages.map((text,i)=>({text,role:roles[i].value})),true);
}));
$('kind').addEventListener('change',invalidate);
$('budget').addEventListener('change',()=>{const saved=imported;invalidate({keepCopied:true});imported=saved;});
// Offer a shortcut only for two plain, single-line paragraphs. The click supplies the roles.
function unlabelledPair() {
  const raw=$('source').value;
  if(imported || $('kind').value!=='trajectory' || raw.length>64000) return null;
  const parts=raw.trim().split(/\r?\n(?:[^\S\r\n]*\r?\n)+/);
  if(parts.length!==2) return null;
  const markup=/^\s*[\[\{<#❯⏺`]/;
  const speaker=/^\s*(?:用户|我|助手|工具|user|assistant|tool|你说|you said|chatgpt\s*(?:说|said))\s*(?:[:：]|$)/i;
  if(parts.some(line=>/[\r\n]/.test(line) || markup.test(line) || speaker.test(line))) return null;
  return parts;
}
$('confirm-pair').addEventListener('click',guard(async()=>{
  const pair=unlabelledPair();
  if(pair) presentTurns([{role:'user',text:pair[0]},{role:'assistant',text:pair[1]}],true);
}));
function presentTurns(turns,advance) {
  const structured=pack(turns);
  if(new TextEncoder().encode(structured).length>64000) throw Error('这段超过 64 KB，请选择较短的对话。');
  const transcript=turns.map(m=>(m.role==='user'?'用户：':'助手：')+m.text).join('\n');
  // Validate before replacing a draft. Preserve roles even when a quoted line looks like a speaker.
  sourcesFrom(structured,'trajectory');
  $('kind').value='trajectory'; $('source').value=transcript; invalidate(); imported=structured;
  if(advance){
    $('request').value=session.prepare(structured,'trajectory',Number($('budget').value));
    $('notice').hidden=true; show('model'); $('copy-request').focus();
  }
}
const pickConversation=createPicker(turns=>presentTurns(turns,true),text=>save('runaway-dialogue.json',text));
$('excerpt').addEventListener('click',()=>{
  if(imported) pickConversation([{title:'当前对话',read:()=>JSON.parse(imported).sources}],{selectRange:true});
});
for (const role of ['user','assistant']) $('append-'+role).addEventListener('click',guard(async()=>{
  const text=$('turn-text').value;
  if(!text.trim()) throw Error('请先粘贴一条发言。');
  const raw=$('source').value;
  let previous=[];
  if(raw.trim()){
    try{previous=sourcesFrom(imported??raw,'trajectory').sources;}
    catch{throw Error('上方有尚未分清说话人的文字。请先把它剪切到逐条输入框，再选择是谁说的。');}
  }
  if(previous.some(m=>!['user','assistant'].includes(m.role))) throw Error('已有工具或背景材料，请在上方直接编辑。');
  presentTurns([...previous,{role,text}],false);
  $('turn-text').value=''; $('turn-text').focus();
  notify('已加入'+(role==='user'?'你的':'助手的')+'发言。');
}));
$('source-file').addEventListener('change',guard(async e=>{
  const file=e.target.files?.[0];
  $('prepare').disabled=true;
  try{
    if(!file)return;
    const {chats,raw}=await readConversationFile(file);
    if(chats){if(confirmReplace())pickConversation(chats);return;}
    if(file.size>64000)throw Error('普通文本超过 64 KB，请复制需要的片段。');
    if(!confirmReplace())return;
    $('source').value=raw; invalidate(); notify('材料已在本机读入。没有上传。');
  }finally{e.target.value='';$('prepare').disabled=false;}
}));
$('archive-file').addEventListener('change',guard(async e=>{try{const text=await readFile(e.target,2000000);if(text===null||!confirmReplace())return;const result=await session.restore(text);clearPasteReview();imported=null;resetHandoff();fictional=session.origin==='fictional_demo';$('reviewed').checked=false;if(result.kind==='archive'){$('source').value=JSON.stringify(session.prepared.sources,null,2);$('kind').value='trajectory';$('budget').value=String(session.prepared.budget);$('request').value=session.request();}else{$('source').value='';$('request').value='';}$('answer').value='';$('source-count').textContent=length($('source').value)+' 字符 · 最多 64 KB';render();notify('文件已在本机打开。请再次核对后导出。');}finally{e.target.value='';}}));
$('prepare').addEventListener('click',guard(async()=>{
  try{
    if(pastedParagraphs){
      const choices=Array.from($('paragraph-rows').querySelectorAll('input'),el=>el.checked);
      if(!choices.includes(true) || !choices.includes(false)) throw Error('请勾选你写的段落，助手的段落留空。');
      presentTurns(groupParagraphs(pastedParagraphs,choices),true);
      return;
    }
    // Editing a source field already invalidates its request and answer.
    if(!session.prepared){
      const raw=$('source').value;
      if(!imported && $('kind').value==='trajectory'){
        const chats=recognize(raw);
        if(chats){pickConversation(chats);return;}
      }
      $('request').value=session.prepare(imported??raw,$('kind').value,Number($('budget').value));
    }
  }catch(error){
    $('source-error').textContent=error.message.startsWith('对话请用')?
      '没有认出说话人。可粘贴带「用户：」「助手：」的对话，或展开「复制出来没有说话人？」逐条加入。':error.message;
    $('source-error').hidden=false;
    $('source').setAttribute('aria-invalid','true');
    $('source-error').scrollIntoView({block:'center'});
    return;
  }
  $('notice').hidden=true;
  show('model');
  $('model-panel').scrollIntoView({block:'start'});
}));
async function copyField(field,status,success,preview){
  try{
    await copyText(field.value);
    status.textContent=success;
  }catch{
    if(preview)preview.open=true;
    field.focus();
    field.select();
    status.textContent='文字已选中。请用系统的「复制」，再去模型里粘贴。';
    status.hidden=false;
    return false;
  }
  status.hidden=false;
  return true;
}
$('copy-request').addEventListener('click',guard(async()=>{
  const copied=await copyField($('request'),$('copy-status'),'去模型里粘贴并发送，拿到回复后回到本页。',$('request-preview'));
  if(copied){
    $('send-label').textContent='请求已复制 · 再次查看';
    $('send-request').open=false;
    $('send-heading').focus();
  }
}));
$('copy-repair').addEventListener('click',guard(async()=>{
  await copyField($('repair-request'),$('repair-status'),'已复制，发回刚才的模型对话即可。');
}));
$('save-request').addEventListener('click',guard(async()=>{if(!session.prepared)throw Error('请先整理来源。');await save('runaway-request.private.txt',$('request').value,'text/plain');}));
$('answer-file').addEventListener('change',guard(async e=>{try{const text=await readFile(e.target);if(text!==null){clearAnswerError();$('answer').value=text;}}finally{e.target.value='';}}));
$('answer').addEventListener('input',clearAnswerError);
$('import-answer').addEventListener('click',guard(async()=>{
  const raw=$('answer').value;
  if(!raw.trim()){
    $('answer').focus();
    return;
  }
  try{session.importAnswer(raw);}
  catch(error){
    $('answer-error').textContent=error.message;
    $('repair-request').value='网页核对结果时提示「'+error.message+'」。请按本对话最初的提炼请求修正，并重新给出完整 JSON。';
    $('answer').setAttribute('aria-invalid','true');
    $('answer-repair').hidden=false;
    $('answer-error').scrollIntoView({block:'center'});
    return;
  }
  clearAnswerError();
  render();
  notify('引文、说话者、字段和长度检查通过。仍需你检查解释是否符合自己。');
  $('result-panel').scrollIntoView({block:'start'});
}));
$('prompt').addEventListener('input',()=>{if(!session.portable)session.body=$('prompt').value;updateSize();});
for(const adapter of adapters){
  const button=document.createElement('button');
  button.type='button';
  button.dataset.harness=adapter.id;
  const label=append(button,'span',adapter.label);
  append(label,'small',adapter.path);
  append(button,'b','↗');
  button.addEventListener('click',guard(async()=>{
    const {portable}=await checkedBundle();
    const result=await harnessBundle(adapter.id,portable.text,RUNAWAY_HARNESS_SOURCES);
    const filename='runaway-'+adapter.id+'.zip';
    const status=await save(filename,result.bytes,'application/zip');
    $('zip-status').textContent=status==='saved' ? '已保存 '+filename : '已请求下载 '+filename+'。如果浏览器弹出保存窗口，请确认下载。';
    $('zip-status').hidden=false;
    $('install-guide').open=true;
    $('zip-status').scrollIntoView({block:'nearest'});
  }));
  $('harnesses').append(button);
}
$('save-portable').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await save('portable.json',portable);}));
$('save-prompt').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await save('runaway-prompt.txt',portable.text,'text/plain');}));
$('copy-prompt').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await copyText(portable.text);notify('完整 prompt 已复制，包含适用边界。');}));
$('save-private').addEventListener('click',guard(async()=>{if(!session.portable)session.body=$('prompt').value;await session.bundle();await save('runaway.private.json',session.archive());}));
$('demo-source').textContent=demo.dialogue;
$('demo-body').textContent=demo.answer.prompt;
$('demo').addEventListener('click',()=>{
  $('demo-preview').showModal();
});
$('load-demo').addEventListener('click',guard(async()=>{
  if(!confirmReplace())return;
  $('demo-preview').close();
  $('kind').value='trajectory';$('budget').value='768';$('source').value=demo.dialogue;
  invalidate();
  $('request').value=session.prepare(demo.dialogue,'trajectory',768);
  session.importAnswer(JSON.stringify(demo.answer));session.origin='fictional_demo';
  $('answer').value=JSON.stringify(demo.answer,null,2);fictional=true;render();
  notify('这是用三句虚构对话实际生成的短卡。你可以展开出处，或核对后导出。');
}));
$('own-dialogue').addEventListener('click',guard(async()=>{
  if(!fictional)return;
  if(session.answer&&session.body!==session.answer.prompt&&!window.confirm('放下编辑过的示例，开始自己的对话？'))return;
  $('source').value='';$('kind').value='trajectory';$('budget').value='768';
  invalidate();$('notice').hidden=true;$('source').focus();
}));
$('clear').addEventListener('click',guard(async()=>{if(!window.confirm('清空本次材料？已导出的文件需要你在设备上另行删除。'))return;$('turn-text').value='';$('source').value='';invalidate();$('prompt').value='';$('evidence').replaceChildren();$('unknowns').replaceChildren();$('name').textContent='';$('tagline').textContent='';await cleanExports();notify('本次材料已清空。');}));
storageReady=cleanExports().catch(()=>notify('上次临时导出文件未能清理；可在系统设置清除 App 缓存。',true));
