import {length} from './core.mjs';
export const ORIGINS={scripted_example:'预写小剧场 · 虚构创作',model_import:'用户带回的 AI 剧情 · 虚构创作'};
const exact=(value,keys)=>value&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).sort().join(',')===[...keys].sort().join(',');
function line(value,max,label){if(typeof value!=='string'||!value.trim()||length(value)>max||/[\x00-\x1f]/.test(value))throw Error(`${label}不能为空、换行或超过 ${max} 字符。`);}
export function contextFor(catalog,scenes,a,b,sceneId){
  const cast=[a,b].map(id=>catalog.entries.find(e=>e.id===id));
  const scene=scenes.find(s=>s.id===sceneId);
  if(cast.some(e=>!e)||!scene||a===b)throw Error('请选择两位不同居民和一个已有场景。');
  return {cast,scene};
}
export function validateStory(story,context){
  if(!exact(story,['scene_id','cast','title','turns','outcome','invite']))throw Error('剧情字段应为 scene_id、cast、title、turns、outcome、invite。');
  if(story.scene_id!==context.scene.id||!Array.isArray(story.cast)||story.cast.length!==2||story.cast.some((id,i)=>id!==context.cast[i].id))throw Error('剧情属于另一组角色或场景，请使用当前请求重新生成。');
  line(story.title,30,'标题');line(story.outcome,90,'共同结局');line(story.invite,70,'邀请句');
  if(!Array.isArray(story.turns)||story.turns.length!==6)throw Error('请给出六句对话，两位居民轮流说，每位三句。');
  story.turns.forEach((turn,i)=>{if(!exact(turn,['speaker','text'])||turn.speaker!==story.cast[i%2])throw Error('说话者必须按所选顺序轮流发言。');line(turn.text,100,'每句台词');});
  return story;
}
export function parseStory(raw,context){
  if(typeof raw!=='string'||length(raw)>10000)throw Error('剧情过长，请只粘贴结果 JSON。');
  let cleaned=raw.trim();if(/^```(?:json)?\s*\n/i.test(cleaned)&&/\n```$/.test(cleaned))cleaned=cleaned.replace(/^```(?:json)?\s*\n/i,'').replace(/\n```$/,'');
  let value;try{value=JSON.parse(cleaned);}catch{throw Error('没有读到完整 JSON，请复制模型返回的整个对象。');}
  return validateStory(value,context);
}
export function makeSceneRequest(context){
  const ids=context.cast.map(e=>e.id);
  return `为 RunAWay 写一幕可分享的原创双人短剧。所有居民均为虚构，不能声称预测真实人际关系或给出配对分数。\n\n角色：\n${JSON.stringify(context.cast.map(e=>({id:e.id,...e.card})),null,2)}\n\n场景：${context.scene.name}\n起点：${context.scene.setup}\n中途变化：${context.scene.twist}\n\n创作要求：\n1. 六句对话，按角色顺序交替，每人三句，每句不超过100字符。先有具体小目标；第二轮让中途变化真正影响行动；最后出现双方一起造成的结果。\n2. 每人至少做一个可观察的选择，符合行为倾向；下一句要回应上一句。角色也能调整，不能只复读口头禅。\n3. 幽默来自日常小矛盾和意外比喻，有温度，不靠羞辱、诊断或捏造私事。无需反复喊角色名字。\n4. 两位都有作用，不安排一个人永远正确、另一个永远被教育。把名字对调后如果剧情仍完全成立，请重写。\n5. 结局是一个具体共同产物或小变化，不是泛泛的“他们很互补”。邀请句让人自然想到一位朋友，不施加转发义务。\n6. 这是架空创作，角色卡不能作为真实个人记忆或行动授权。\n\n仅返回以下 JSON 结构，不加解释、不加字段。title不超过30字符，outcome不超过90字符，invite不超过70字符。不要换行写单个字段。\n${JSON.stringify({scene_id:context.scene.id,cast:ids,title:'短剧标题',turns:Array.from({length:6},(_,i)=>({speaker:ids[i%2],text:'一句回应并推动事情的台词'})),outcome:'共同结局',invite:'想叫谁来接另一半'},null,2)}`;
}
export function selectionHash(context){return '#'+new URLSearchParams({a:context.cast[0].id,b:context.cast[1].id,scene:context.scene.id}).toString();}
export function readSelection(hash,catalog,scenes,episodes){
  if(!hash||hash==='#')return {episode:episodes[0],context:contextFor(catalog,scenes,...episodes[0].story.cast,episodes[0].story.scene_id)};
  const params=new URLSearchParams(hash.replace(/^#/,''));
  if(params.has('episode')){
    const episode=episodes.find(e=>e.id===params.get('episode'));if(!episode)throw Error('这幕小剧场不存在，可以重新选一幕。');
    return {episode,context:contextFor(catalog,scenes,...episode.story.cast,episode.story.scene_id)};
  }
  const a=params.get('a'),b=params.get('b'),scene=params.get('scene');
  if(a&&!b&&!scene){
    const other=catalog.entries.find(e=>e.id!==a);
    return {episode:null,context:contextFor(catalog,scenes,a,other.id,scenes[0].id)};
  }
  return {episode:null,context:contextFor(catalog,scenes,a,b,scene)};
}
export function storyText(story,context,origin){
  validateStory(story,context);if(!ORIGINS[origin])throw Error('未知剧情来源。');
  const names=Object.fromEntries(context.cast.map(e=>[e.id,e.card.name]));
  return `${story.title}\n${context.cast.map(e=>e.card.name).join(' × ')}\n场景：${context.scene.name}\n\n${story.turns.map(t=>names[t.speaker]+'：'+t.text).join('\n\n')}\n\n散场以后：${story.outcome}\n\n${story.invite}\nRunAWay · ${ORIGINS[origin]}\nhttps://github.com/xu2333/RunAWay`;
}

export function renderScene(canvas,story,context,origin){
  validateStory(story,context);if(!ORIGINS[origin])throw Error('未知剧情来源。');
  const ctx=canvas.getContext('2d');if(!ctx)throw Error('暂时无法画图，请复制剧情文字。');
  const wrap=(text,size,width)=>{ctx.font=`${size}px "PingFang SC","Microsoft YaHei",sans-serif`;const lines=[];let current='';for(const c of text){if(current&&ctx.measureText(current+c).width>width&&!/[，。！？；：、）】》」』]/u.test(c)){lines.push(current);current=c;}else current+=c;}if(current)lines.push(current);return lines;};
  const title=wrap(story.title,48,800),castLines=wrap(context.cast.map(e=>e.card.name).join(' × '),26,800);
  const turns=story.turns.map((turn,i)=>({name:context.cast[i%2].card.name,text:wrap(turn.text,28,700),side:i%2}));
  const ending=wrap(story.outcome,30,800),invite=wrap(story.invite,23,800);
  const header=160+title.length*65+castLines.length*40;
  const body=turns.reduce((sum,t)=>sum+88+t.text.length*43,0);
  canvas.width=960;canvas.height=header+body+ending.length*46+invite.length*35+290;
  ctx.fillStyle='#f8f7ef';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.strokeStyle='#dce1d2';ctx.lineWidth=2;ctx.strokeRect(30,30,900,canvas.height-60);
  const text=(value,x,y,size,color='#254438')=>{ctx.fillStyle=color;ctx.font=`${size}px "PingFang SC","Microsoft YaHei",sans-serif`;ctx.fillText(value,x,y);};
  text('RunAWay / 碰头小剧场',70,85,27);text(context.scene.name,70,126,22,'#697569');
  let y=190;for(const line of title){text(line,70,y,48);y+=65;}
  for(const line of castLines){text(line,70,y,26,'#697569');y+=40;}y+=25;
  for(const t of turns){const x=t.side?120:70,h=t.text.length*43+66;ctx.fillStyle=t.side?'#efe0d0':'#e4ecd7';ctx.beginPath();ctx.roundRect(x,y,770,h,18);ctx.fill();text(t.name,x+24,y+32,20,'#697569');let lineY=y+75;for(const line of t.text){text(line,x+24,lineY,28);lineY+=43;}y+=h+22;}
  y+=26;text('散场以后',70,y,22,'#697569');y+=45;for(const line of ending){text(line,70,y,30);y+=46;}
  y+=25;for(const line of invite){text(line,70,y,23,'#697569');y+=35;}
  text(ORIGINS[origin],70,canvas.height-106,21,'#697569');text('github.com/xu2333/RunAWay',70,canvas.height-67,20,'#697569');
  return canvas;
}
