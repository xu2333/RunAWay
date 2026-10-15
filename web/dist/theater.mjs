import {validateCatalog,filterEntries} from './catalog-core.mjs';
import {SCENES,EPISODES} from './theater-data.mjs';
import {contextFor,validateStory,parseStory,makeSceneRequest,selectionHash,readSelection,storyText,renderScene,ORIGINS} from './theater-core.mjs';
const $=id=>document.getElementById(id);
let catalog,context,current=null;
function status(message,error=false){$('action-status').textContent=message;$('action-status').hidden=false;$('action-status').classList.toggle('error',error);}
function options(side){
  const select=$('cast-'+side),selected=context.cast[side==='a'?0:1];
  const entries=filterEntries(catalog,$('find-'+side).value);
  select.replaceChildren();
  const matches=entries.some(e=>e.id===selected.id)?entries:[selected,...entries];
  for(const entry of matches){const option=document.createElement('option');option.value=entry.id;option.textContent=entry.card.name+' · '+entry.id;select.append(option);}select.value=selected.id;
  $('anchor-'+side).textContent=selected.card.tell+(entries.length?'': ' · 没找到匹配项，保留当前选择。');
}
function sync(){
  options('a');options('b');$('scene').value=context.scene.id;
  $('setup').textContent=context.scene.setup;
  $('scene-request').value=makeSceneRequest(context);
}
function clearStory(){
  current=null;$('story').hidden=true;$('empty-stage').hidden=false;$('generation').hidden=true;
  $('scene-answer').value='';$('save-scene').removeAttribute('href');$('copy-fallback').hidden=true;$('action-status').hidden=true;
  for(const button of $('episodes').children)button.setAttribute('aria-pressed','false');
}
function selectedChanged(){
  try{const next=contextFor(catalog,SCENES,$('cast-a').value,$('cast-b').value,$('scene').value);context=next;clearStory();sync();history.replaceState(null,'',selectionHash(context));$('notice').hidden=true;}
  catch(error){status(error.message,true);sync();}
}
function show(story,origin,episodeId=null){
  validateStory(story,context);current={story,origin,episodeId};
  $('story-title').textContent=story.title;$('story-origin').textContent=ORIGINS[origin];$('story-scene').textContent=context.scene.name;
  const badges=$('cast-badges');badges.replaceChildren();
  context.cast.forEach((entry,i)=>{if(i){const x=document.createElement('span');x.textContent='×';badges.append(x);}const a=document.createElement('a');a.href='./gallery.html#'+entry.id;a.textContent=entry.card.name+' ↗';badges.append(a);});
  $('dialogue').replaceChildren();story.turns.forEach((turn,i)=>{const div=document.createElement('div');div.className='speech'+(i%2?' other':'');const name=document.createElement('div');name.className='speaker';name.textContent=context.cast[i%2].card.name;const p=document.createElement('p');p.textContent=turn.text;div.append(name,p);$('dialogue').append(div);});
  $('outcome').textContent=story.outcome;$('invite-line').textContent=story.invite;
  $('copy-episode').hidden=!episodeId;$('import-note').hidden=origin!=='model_import';
  $('save-scene').removeAttribute('href');
  try{renderScene($('scene-canvas'),story,context,origin);$('save-scene').href=$('scene-canvas').toDataURL('image/png');$('save-scene').download=`runaway-${context.cast.map(e=>e.id).join('-')}.png`;}
  catch(error){status(error.message,true);}
  $('empty-stage').hidden=true;$('story').hidden=false;
}
function loadEpisode(episode){
  context=contextFor(catalog,SCENES,...episode.story.cast,episode.story.scene_id);
  $('find-a').value='';$('find-b').value='';clearStory();sync();show(episode.story,'scripted_example',episode.id);
  for(const button of $('episodes').children)button.setAttribute('aria-pressed',String(button.dataset.episode===episode.id));
  history.replaceState(null,'','#episode='+episode.id);
}
async function copy(value){
  try{await navigator.clipboard.writeText(value);$('copy-fallback').hidden=true;status('复制好了。');}
  catch{$('copy-fallback').value=value;$('copy-fallback').hidden=false;$('copy-fallback').focus();$('copy-fallback').select();status('浏览器未允许自动复制，请从下方手动复制。');}
}
for(const side of ['a','b']){$('find-'+side).addEventListener('input',()=>options(side));$('cast-'+side).addEventListener('change',selectedChanged);}
$('scene').addEventListener('change',selectedChanged);
$('prepare-scene').addEventListener('click',()=>{$('generation').hidden=false;$('scene-request').value=makeSceneRequest(context);$('generation').scrollIntoView({block:'start'});});
$('copy-request').addEventListener('click',()=>copy(makeSceneRequest(context)));
$('import-scene').addEventListener('click',()=>{try{const story=parseStory($('scene-answer').value,context);show(story,'model_import');for(const button of $('episodes').children)button.setAttribute('aria-pressed','false');history.replaceState(null,'',selectionHash(context));status('剧情已排好。检查两位的选择与接话，再带走。');$('story').scrollIntoView({block:'start'});}catch(error){status(error.message,true);$('action-status').scrollIntoView({block:'center'});}});
$('copy-story').addEventListener('click',()=>{if(current)copy(storyText(current.story,context,current.origin));});
$('copy-episode').addEventListener('click',()=>{if(current?.episodeId)copy(location.origin+location.pathname+'#episode='+current.episodeId);});
$('invite-pair').addEventListener('click',()=>copy(`想看看这两位碰到一起会怎样：${context.cast.map(e=>e.card.name).join(' × ')}。场景：${context.scene.name}。你想演哪一位？\n${location.origin+location.pathname+selectionHash(context)}\n这是虚构角色组合；链接不含自生成剧情。`));
$('save-scene').addEventListener('click',event=>{if(!$('save-scene').hasAttribute('href')){event.preventDefault();return;}status('已请求下载双人剧照，请查看浏览器下载列表。');});
function fromHash(){try{const selection=readSelection(location.hash,catalog,SCENES,EPISODES);if(selection.episode)loadEpisode(selection.episode);else{context=selection.context;$('find-a').value='';$('find-b').value='';clearStory();sync();}}catch(error){loadEpisode(EPISODES[0]);status(error.message,true);}}
window.addEventListener('hashchange',()=>{if(catalog)fromHash();});
try{
  const response=await fetch('./catalog.json');if(!response.ok)throw Error('读取居民册失败。');catalog=validateCatalog(await response.json());
  for(const scene of SCENES){const option=document.createElement('option');option.value=scene.id;option.textContent=scene.name;$('scene').append(option);}
  for(const episode of EPISODES){const button=document.createElement('button');button.textContent=SCENES.find(s=>s.id===episode.story.scene_id).name;button.dataset.episode=episode.id;button.setAttribute('aria-pressed','false');button.addEventListener('click',()=>loadEpisode(episode));$('episodes').append(button);}
  fromHash();for(const id of ['find-a','find-b','cast-a','cast-b','scene','prepare-scene','invite-pair'])$(id).disabled=false;$('notice').hidden=true;
}catch(error){$('notice').textContent='小剧场暂时没打开，请刷新重试。本地使用时请通过 HTTP 服务打开页面。';$('notice').classList.add('error');}
