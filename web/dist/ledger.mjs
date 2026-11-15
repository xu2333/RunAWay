import {parseJSON} from './core.mjs';
import {createTemporal} from './temporal-core.mjs';
import {createLedger} from './preference-ledger.mjs';
const $=id=>document.getElementById(id), state={};let ledger,book,engine;
const notice=s=>{$('notice').textContent=s;};
let pending=Promise.resolve();
function act(fn){pending=pending.then(fn).catch(e=>notice(e.message));return pending;}
async function read(file){if(!file||file.size>8000000)throw Error('请选择不超过8 MB的JSON文件。');return parseJSON(new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer()));}
async function render(){
 $('rows').replaceChildren();$('download').disabled=!book.entries.length;
 if(!state.artifact)return;
 for(const r of await ledger.summarize(book,state.artifact)){
  const p=document.createElement('p');p.textContent=`${r.preference_id} · ${r.action} · ${r.origin==='demo_or_edited_demo'?'虚构示例':'用户记录（未独立验证）'}：采纳 ${r.adopted} / 纠正 ${r.corrected} / 未决 ${r.unresolved}${r.corrected?' · 优先复核':''}`;$('rows').append(p);
  for(const c of r.contexts){const line=document.createElement('blockquote');line.textContent=c.situation+' · '+c.outcome;$('rows').append(line);}
 }
}
await act(async()=>{
 const responses=await Promise.all([fetch('./temporal-protocol.json'),fetch('./choice-contract.json')]);
 if(responses.some(r=>!r.ok))throw Error('本地协议未加载。');
 const [protocol,contract]=await Promise.all(responses.map(r=>r.json()));engine=createTemporal(protocol);ledger=createLedger(engine,contract);book=ledger.empty();$('add').disabled=false;
 for(const key of ['artifact','portable','trial'])$(key).addEventListener('change',()=>act(async()=>{
  delete state[key];$('attributed').checked=false;if(key==='artifact')$('preference').replaceChildren();
  const value=await read($(key).files[0]);
  if(key==='artifact'){
   await engine.validate(value);
   const events=Object.values(await engine.effective(value)).flatMap(g=>[...g.regular,...g.exception,...g.constraint]);
   for(const e of events)$('preference').add(new Option(e.id+' · '+e.action,e.id));
  }
  state[key]=value;await render();notice('已读入本机文件。');
 }));
 $('add').addEventListener('click',()=>act(async()=>{
  if(!state.artifact||!state.portable||!state.trial)throw Error('请先读入三个对应的文件。');
  book=await ledger.add(book,{...state,preference_id:$('preference').value,outcome:$('outcome').value,attributed:$('attributed').checked});await render();notice('已记入；重复记录不会增加次数。请下载保存。');
 }));
 $('restore').addEventListener('change',()=>act(async()=>{book=await ledger.merge(book,await read($('restore').files[0]));await render();notice('已合并并重新核验绑定。');}));
 $('download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(book,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='runaway-ledger.private.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 $('clear').addEventListener('click',()=>{if(confirm('清空本页全部材料和未下载账本？'))location.reload();});
});
