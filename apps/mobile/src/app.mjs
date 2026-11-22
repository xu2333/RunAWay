import {Session} from './session.mjs';
import {adapters,BOUNDARY} from '../../../packages/harnesses/index.mjs';
import {makeBundle as harnessBundle} from '../../../packages/harnesses/bundle.mjs';
import {length} from '../../../web/dist/core.mjs';
import {copyText,saveFile,cleanExports} from './io.mjs';
import demo from './paper-crane.json';

const $=id=>document.getElementById(id),session=new Session();
let fictional=false,active=false,storageReady=Promise.resolve();
function notify(text,error=false){$('notice').hidden=false;$('notice').textContent=text;$('notice').classList.toggle('error',error);}
function show(step){
  if(step==='model'&&!session.prepared)return notify('请先放入经历并整理请求。',true);
  if(step==='result'&&!session.answer&&!session.portable)return notify('请先导入提炼结果或已有的 portable.json。',true);
  for(const name of ['source','model','result'])$(name+'-panel').hidden=name!==step;
  document.querySelectorAll('[data-step]').forEach(b=>{if(b.dataset.step===step)b.setAttribute('aria-current','step');else b.removeAttribute('aria-current');});
}
function guard(fn){return async event=>{
  if(active)return;active=true;const button=event.currentTarget;button.disabled=true;
  try{await storageReady;await fn(event);}catch(e){notify(e.message||'操作没有完成。',true);}
  finally{button.disabled=false;active=false;}
};}
function invalidate(){session.reset();fictional=false;$('reviewed').checked=false;$('request').value='';$('answer').value='';show('source');$('source-count').textContent=length($('source').value)+' 字符 · 最多 64 KB';}
function append(parent,tag,text){const n=document.createElement(tag);n.textContent=text;parent.append(n);return n;}
function updateSize(){const value=session.portable?session.portable.text:BOUNDARY+$('prompt').value+'\n';$('prompt-size').textContent=`完整 prompt ${length(value)} 字符（包含边界，不是 token 数）`;$('reviewed').checked=false;}
function render(){
  const a=session.answer;
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
async function save(name,value,mime='application/json'){const saved=await saveFile(name,typeof value==='string'||value instanceof Uint8Array?value:JSON.stringify(value,null,2)+'\n',mime);notify(saved.status==='saved'?'系统已完成文件保存。':'已请求下载，请以浏览器文件界面为准。');}
async function readFile(input,max=512000){const file=input.files?.[0];if(!file)return null;if(file.size>max)throw Error(`文件超过 ${max/1000} KB，请选择相关片段。`);try{return new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());}catch{throw Error('文件编码无法识别。请选择 UTF-8 文本文件；原有材料未改变。');}}
function confirmReplace(){return !($('source').value||session.portable||session.answer)||window.confirm('替换当前材料？请先保存想保留的私有档案。');}
for(const b of document.querySelectorAll('[data-step]'))b.addEventListener('click',()=>show(b.dataset.step));
for(const id of ['source','kind','budget'])$(id).addEventListener(id==='source'?'input':'change',invalidate);
$('source-file').addEventListener('change',guard(async e=>{try{const text=await readFile(e.target,64000);if(text!==null&&confirmReplace()){$('source').value=text;invalidate();notify('材料已在本机读入。没有上传。');}}finally{e.target.value='';}}));
$('archive-file').addEventListener('change',guard(async e=>{try{const text=await readFile(e.target,2000000);if(text===null||!confirmReplace())return;const result=await session.restore(text);fictional=session.origin==='fictional_demo';$('reviewed').checked=false;if(result.kind==='archive'){$('source').value=JSON.stringify(session.prepared.sources,null,2);$('kind').value='trajectory';$('budget').value=String(session.prepared.budget);$('request').value=session.request();}else{$('source').value='';$('request').value='';}$('answer').value='';$('source-count').textContent=length($('source').value)+' 字符 · 最多 64 KB';render();notify('文件已在本机打开。请再次核对后导出。');}finally{e.target.value='';}}));
$('prepare').addEventListener('click',guard(async()=>{$('request').value=session.prepare($('source').value,$('kind').value,Number($('budget').value));fictional=false;show('model');notify('请求已准备。只有你主动复制或保存后，才会把内容交给所选模型。');}));
$('copy-request').addEventListener('click',guard(async()=>{if(!session.prepared)throw Error('请先整理来源。');await copyText($('request').value);notify('请求已复制。接下来由你决定交给哪个模型。');}));
$('save-request').addEventListener('click',guard(async()=>{if(!session.prepared)throw Error('请先整理来源。');await save('runaway-request.private.txt',$('request').value,'text/plain');}));
$('answer-file').addEventListener('change',guard(async e=>{try{const text=await readFile(e.target);if(text!==null)$('answer').value=text;}finally{e.target.value='';}}));
$('import-answer').addEventListener('click',guard(async()=>{session.importAnswer($('answer').value);render();notify('引文、说话者、字段和长度检查通过。仍需你检查解释是否符合自己。');}));
$('prompt').addEventListener('input',()=>{if(!session.portable)session.body=$('prompt').value;updateSize();});
for(const adapter of adapters){const b=document.createElement('button');b.type='button';b.dataset.harness=adapter.id;const label=append(b,'span',adapter.label);append(label,'small',adapter.path);append(b,'b','↗');b.addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();const result=await harnessBundle(adapter.id,portable.text,RUNAWAY_HARNESS_SOURCES);await save('runaway-'+adapter.id+'.zip',result.bytes,'application/zip');}));$('harnesses').append(b);}
$('save-portable').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await save('portable.json',portable);}));
$('save-prompt').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await save('runaway-prompt.txt',portable.text,'text/plain');}));
$('copy-prompt').addEventListener('click',guard(async()=>{const {portable}=await checkedBundle();await copyText(portable.text);notify('完整 prompt 已复制，包含适用边界。');}));
$('save-private').addEventListener('click',guard(async()=>{if(!session.portable)session.body=$('prompt').value;await session.bundle();await save('runaway.private.json',session.archive());}));
$('demo').addEventListener('click',guard(async()=>{
  if(!confirmReplace())return;
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
$('clear').addEventListener('click',guard(async()=>{if(!window.confirm('清空本次材料？已导出的文件需要你在设备上另行删除。'))return;$('source').value='';invalidate();$('prompt').value='';$('evidence').replaceChildren();$('unknowns').replaceChildren();$('name').textContent='';$('tagline').textContent='';await cleanExports();notify('本次材料已清空。');}));
storageReady=cleanExports().catch(()=>notify('上次临时导出文件未能清理；可在系统设置清除 App 缓存。',true));
