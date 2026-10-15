import {cardText,renderCard} from './presentation.mjs';
import {validateCatalog,filterEntries,entryFromHash,pickEntry,fictionalPrompt} from './catalog-core.mjs';
const $=id=>document.getElementById(id),pageSize=24;
let data,filtered=[],page=0,selected=null;
const dialog=$('resident');

function show(entry){
  if(!entry)return;
  selected=entry;
  $('resident-title').textContent=entry.card.name;
  $('resident-tagline').textContent=entry.card.tagline;
  $('resident-tell').textContent=entry.card.tell;
  $('resident-boundary').textContent=entry.card.boundary;
  $('resident-meta').textContent=`${entry.id} · ${data.categories.find(c=>c.id===entry.category).name} · 原创合成角色`;
  $('role-prompt').value=fictionalPrompt(entry);
  $('copy-fallback').hidden=true;$('action-status').textContent='';
  $('save-image').removeAttribute('href');
  try{renderCard($('resident-canvas'),entry.card,'catalog');$('save-image').href=$('resident-canvas').toDataURL('image/png');$('save-image').download=`runaway-${entry.id}.png`;}
  catch{$('action-status').textContent='图片暂时没画好，可以先复制文字。';}
  history.replaceState(null,'',`#${entry.id}`);
  if(!dialog.open)dialog.showModal();
  dialog.scrollTop=0;
}
function render(){
  filtered=filterEntries(data,$('search').value,$('category').value);
  const pages=Math.max(1,Math.ceil(filtered.length/pageSize));page=Math.min(page,pages-1);
  const grid=$('catalog-grid');grid.replaceChildren();
  for(const entry of filtered.slice(page*pageSize,(page+1)*pageSize)){
    const card=document.createElement('button');card.className='resident-card';
    card.setAttribute('aria-label',`${entry.id} ${entry.card.name}，查看角色`);
    for(const [tag,cls,value] of [['span','card-id',entry.id],['strong','',entry.card.name],['span','card-joke',entry.card.tagline],['span','card-street',data.categories.find(c=>c.id===entry.category).name+' ↗']]){
      const node=document.createElement(tag);node.className=cls;node.textContent=value;card.append(node);
    }
    card.addEventListener('click',()=>show(entry));grid.append(card);
  }
  $('catalog-status').textContent=filtered.length?`找到 ${filtered.length} 位居民 · 共 ${data.entries.length} 位`:'这条街暂时没找到。换个关键词，或重逛全部。';
  $('page-status').textContent=`${page+1} / ${pages}`;
  $('prev').disabled=page===0;$('next').disabled=page>=pages-1;
}
async function copy(value){
  try{await navigator.clipboard.writeText(value);$('action-status').textContent='复制好了，带走吧。';$('copy-fallback').hidden=true;}
  catch{$('copy-fallback').value=value;$('copy-fallback').hidden=false;$('copy-fallback').focus();$('copy-fallback').select();$('action-status').textContent='浏览器未允许自动复制，请从下方手动复制。';}
}
$('search').addEventListener('input',()=>{page=0;render();});
$('category').addEventListener('change',()=>{page=0;render();});
$('clear').addEventListener('click',()=>{$('search').value='';$('category').value='';page=0;render();});
for(const [id,step] of [['prev',-1],['next',1]])$(id).addEventListener('click',()=>{page+=step;render();$('browse-title').scrollIntoView({block:'start'});});
$('random').addEventListener('click',()=>show(pickEntry(data.entries,selected?.id)));
$('another').addEventListener('click',()=>show(pickEntry(data.entries,selected?.id)));
$('close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('close',()=>history.replaceState(null,'',location.pathname+location.search));
$('copy-text').addEventListener('click',()=>copy(cardText(selected.card,'catalog')+'\n角色编号：'+selected.id));
$('copy-role').addEventListener('click',()=>copy(fictionalPrompt(selected)));
$('copy-link').addEventListener('click',()=>copy(location.href));
$('save-image').addEventListener('click',event=>{if(!$('save-image').hasAttribute('href')){event.preventDefault();return;}$('action-status').textContent='已请求下载图片，请查看浏览器下载列表。';});
window.addEventListener('hashchange',()=>{if(data){const entry=entryFromHash(data,location.hash);if(entry)show(entry);else if(dialog.open)dialog.close();}});
try{
  const response=await fetch('./catalog.json');if(!response.ok)throw Error('读取失败');data=validateCatalog(await response.json());
  for(const c of data.categories){const option=document.createElement('option');option.value=c.id;option.textContent=c.name+' · 25';$('category').append(option);}
  for(const id of ['search','category','random','clear'])$(id).disabled=false;
  render();const initial=entryFromHash(data,location.hash);if(initial)show(initial);
}catch(error){$('catalog-status').textContent='居民册暂时没打开。请刷新重试；本地使用时请通过 HTTP 服务打开页面。';}
