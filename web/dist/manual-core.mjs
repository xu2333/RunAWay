export const MANUAL_LABELS={persuade:'想说服我',friction:'容易让我卡住',change:'我会改主意，当'};
const len=s=>[...s].length;
const exact=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&Object.keys(v).sort().join(',')===[...keys].sort().join(',');
export function validateManual(manual,claims){
  if(!exact(manual,['headline','items'])||typeof manual.headline!=='string'||!manual.headline.trim()||len(manual.headline)>60||/[\x00-\x1f]/.test(manual.headline)||!Array.isArray(manual.items)||manual.items.length>3)throw Error('使用说明书需要 headline（60 字内）和最多三条 items。');
  const seen=new Set(),ids=new Set(claims.map(c=>c.id));
  for(const item of manual.items){
    if(!exact(item,['kind','text','claim_ids'])||!Object.hasOwn(MANUAL_LABELS,item.kind)||seen.has(item.kind)||typeof item.text!=='string'||!item.text.trim()||len(item.text)>120||/[\x00-\x1f]/.test(item.text))throw Error('说明书条目类型重复、文案为空或超过 120 字。');
    if(!Array.isArray(item.claim_ids)||!item.claim_ids.length||new Set(item.claim_ids).size!==item.claim_ids.length||item.claim_ids.some(id=>!ids.has(id)))throw Error('每条说明书都要关联已有判断；没有证据就省略该项。');
    seen.add(item.kind);
  }
  if(!manual.items.length&&manual.headline!=='材料还不足以写使用说明')throw Error('没有依据时，请明确标记材料不足。');
  return manual;
}
export function manualText(name,manual,claims,demo=false){
  validateManual(manual,claims);
  return `${name} · 我的使用说明书\n${manual.headline}\n\n${manual.items.map(i=>MANUAL_LABELS[i.kind]+'：'+i.text).join('\n\n')}\n\n${demo?'虚构示例，不代表真实人物':'本人核对的表达，适用范围有限'}\nRunAWay · your taste, to go.\nhttps://github.com/xu2333/RunAWay`;
}
export function renderManual(canvas,name,manual,claims,demo=false){
  validateManual(manual,claims);const ctx=canvas.getContext('2d');if(!ctx)throw Error('暂时无法生成图片，可以复制文字。');
  const wrap=(text,size,width)=>{ctx.font=`${size}px "PingFang SC","Microsoft YaHei",sans-serif`;let line='';const lines=[];for(const c of text){if(line&&ctx.measureText(line+c).width>width&&!/[，。！？；：、）】》]/u.test(c)){lines.push(line);line=c;}else line+=c;}if(line)lines.push(line);return lines;};
  const title=wrap(name,48,800),headline=wrap(manual.headline,40,800),items=manual.items.map(i=>({...i,lines:wrap(i.text,40,750)}));
  canvas.width=960;canvas.height=Math.max(1080,340+title.length*64+headline.length*58+items.reduce((n,i)=>n+100+i.lines.length*56,0));
  ctx.fillStyle='#f8f7ef';ctx.fillRect(0,0,960,canvas.height);ctx.strokeStyle='#dce1d2';ctx.strokeRect(32,32,896,canvas.height-64);
  const draw=(s,x,y,size,color='#254438')=>{ctx.fillStyle=color;ctx.font=`${size}px "PingFang SC","Microsoft YaHei",sans-serif`;ctx.fillText(s,x,y);};
  draw('RunAWay / 我的使用说明书',70,94,28);let y=185;
  for(const s of title){draw(s,70,y,48);y+=64;}y+=12;for(const s of headline){draw(s,70,y,40,'#66774e');y+=58;}y+=25;
  for(const i of items){draw(MANUAL_LABELS[i.kind],70,y,30,'#7b845f');y+=43;for(const s of i.lines){draw(s,70,y,40);y+=56;}y+=57;}
  draw(demo?'虚构示例 · 不是对你的判断':'本人核对的表达 · 适用范围有限',70,canvas.height-112,21,'#697569');draw('github.com/xu2333/RunAWay',70,canvas.height-70,20,'#697569');
  return canvas;
}
