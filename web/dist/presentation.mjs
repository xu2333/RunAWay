import {VERSION,canonical,hash,length} from './core.mjs';

export function validateCard(card) {
  if(!card||Object.keys(card).sort().join(',')!=='boundary,name,tagline,tell')throw Error('分享卡字段不完整。');
  for(const [key,max] of [['name',40],['tagline',160],['tell',100],['boundary',100]]) {
    if(typeof card[key]!=='string'||!card[key].trim()||length(card[key])>max||/[\x00-\x1f]/.test(card[key]))throw Error('分享卡文案为空、过长或包含换行。请检查四段文字。');
  }
  return card;
}
export const normalize = value => value.normalize('NFKC').toLowerCase().replace(/[\p{P}\p{Z}\p{S}\s]/gu,'');
export function cardText(card,demo=false) {
  validateCard(card);
  return `${card.name}\n${card.tagline}\n\n${card.tell}\n边界：${card.boundary}\n\nRunAWay · ${demo==='catalog'?'原创合成角色 · 娱乐创作':demo?'虚构故事示例':'个人表达，待验证'}\nhttps://github.com/xu2333/RunAWay`;
}
export async function makeOutputSample(card,ratings,profileId,origin) {
  validateCard(card);
  if(!/^[a-f0-9]{64}$/.test(profileId)||!['fictional_demo','user_submitted'].includes(origin))throw Error('分享卡来源无效。');
  if(!ratings||Object.keys(ratings).sort().join(',')!=='amusing,recognizable,would_share'||Object.values(ratings).some(v=>!['yes','no','unsure'].includes(v)))throw Error('请检查三项反馈。');
  const payload={schema_version:1,artifact_type:'runaway_output_sample',app_version:VERSION,origin,profile_id:profileId,
    card:{...card},ratings:{...ratings},evaluation:'self_report_only',source_history_included:false};
  // Card contents are opted in by the user; never include source history or compact prompt.
  return {...payload,id:await hash(canonical(payload))};
}
export async function validateSample(sample) {
  const expected=['schema_version','artifact_type','app_version','origin','profile_id','card','ratings','evaluation','source_history_included','id'];
  if(!sample||Object.keys(sample).sort().join(',')!==expected.sort().join(',')||sample.schema_version!==1||sample.artifact_type!=='runaway_output_sample'||sample.source_history_included!==false||sample.evaluation!=='self_report_only'||typeof sample.app_version!=='string')throw Error('不是有效的主动导出结果样本。');
  await makeOutputSample(sample.card,sample.ratings,sample.profile_id,sample.origin);
  const {id,...body}=sample;if(id!==await hash(canonical(body)))throw Error('结果样本被更改，请重新导出。');
  return sample;
}
const behavior = s=>normalize(s.card.tell)+'|'+normalize(s.card.boundary);
function bigrams(text){const a=[...text],b=new Set();for(let i=0;i<a.length-1;i++)b.add(a[i]+a[i+1]);return b;}
function similarity(a,b){const x=bigrams(a),y=bigrams(b);const common=[...x].filter(v=>y.has(v)).length;return x.size+y.size-common?common/(x.size+y.size-common):1;}
export async function auditSamples(samples,target=null) {
  if(target!==null&&(!Number.isInteger(target)||target<1))throw Error('target must be a positive integer');
  for(const s of samples)await validateSample(s);
  const unique=[...new Map(samples.map(s=>[s.id,s])).values()];
  const real=unique.filter(s=>s.origin==='user_submitted');
  const approved=real.filter(s=>Object.values(s.ratings).every(v=>v==='yes'));
  const behaviorCount=new Set(approved.map(behavior)).size;
  const pairs=[];let pairCount=0;
  for(let i=0;i<approved.length;i++)for(let j=i+1;j<approved.length;j++){
    const a=behavior(approved[i]),b=behavior(approved[j]);const score=similarity(a,b);
    if(score>=.65){pairCount++;if(pairs.length<50)pairs.push({ids:[approved[i].id,approved[j].id],similarity:Number(score.toFixed(3)),exact_behavior:a===b});}
  }
  return {target,input_files:samples.length,unique_samples:unique.length,duplicate_files:samples.length-unique.length,
    fictional_samples_excluded:unique.length-real.length,user_declared_samples:real.length,
    distinct_profile_ids:new Set(real.map(s=>s.profile_id)).size,
    all_three_self_ratings_yes:approved.length,unique_normalized_names:new Set(approved.map(s=>normalize(s.card.name))).size,
    unique_exact_behavior_texts:behaviorCount,remaining_to_target:target===null?null:Math.max(0,target-behaviorCount),
    near_duplicate_pair_count:pairCount,near_duplicate_pairs:pairs,near_duplicate_pairs_truncated:pairCount>pairs.length,
    conclusion:'Counts describe volunteered text samples and self-ratings, not unique people, independent quality, semantic diversity, fidelity or viral reach. Similarity is a review cue, not a semantic verdict. No automatic interesting-output pass.'};
}

// Render the exact preview that will be downloaded. No source text, prompt or evidence enters it.
export function renderCard(canvas,card,demo=false) {
  validateCard(card);
  const ctx=canvas.getContext('2d');if(!ctx)throw Error('浏览器无法生成图片，请复制卡片文字。');
  const wrap=(text,size,width)=>{
    ctx.font=`${size}px "PingFang SC", "Microsoft YaHei", sans-serif`;
    const lines=[];let line='';for(const char of text){if(line&&ctx.measureText(line+char).width>width&&!/[，。！？；：、）】》」』]/u.test(char)){lines.push(line);line=char;}else line+=char;}if(line)lines.push(line);return lines;
  };
  const sections=[{lines:wrap(card.name,68,800),size:68,gap:86,color:'#254438'},
    {lines:wrap(card.tagline,34,800),size:34,gap:51,color:'#53684e'},
    {label:demo==='catalog'?'这位居民的做法':'一眼认出我的做法',lines:wrap(card.tell,32,750),size:32,gap:49,color:'#254438'},
    ...(demo==='catalog'?[]:[{label:'但也有我的边界',lines:wrap(card.boundary,30,750),size:30,gap:46,color:'#53684e'}])];
  const contentHeight=sections.reduce((n,s)=>n+s.lines.length*s.gap+48+(s.label?52:0),0);
  canvas.width=960;canvas.height=Math.max(1080,contentHeight+350);
  ctx.fillStyle='#f8f7ef';ctx.fillRect(0,0,960,canvas.height);ctx.strokeStyle='#d8dfcc';ctx.lineWidth=2;ctx.strokeRect(36,36,888,canvas.height-72);
  ctx.fillStyle='#345d43';ctx.font='bold 32px sans-serif';ctx.fillText('RunAWay',80,102);
  ctx.fillStyle='#697569';ctx.font='20px sans-serif';ctx.fillText('your taste, to go.',80,137);
  // Small frog stamp, drawn locally instead of fetching an external asset.
  ctx.fillStyle='#b6cb93';ctx.beginPath();ctx.ellipse(817,117,47,38,0,0,Math.PI*2);ctx.fill();
  for(const x of [793,840]){ctx.beginPath();ctx.arc(x,89,19,0,Math.PI*2);ctx.fill();ctx.fillStyle='#254438';ctx.beginPath();ctx.arc(x,88,4,0,Math.PI*2);ctx.fill();ctx.fillStyle='#b6cb93';}
  ctx.strokeStyle='#254438';ctx.beginPath();ctx.arc(817,113,12,0,Math.PI);ctx.stroke();
  let y=230;
  for(const s of sections){if(s.label){ctx.fillStyle='#7b845f';ctx.font='22px sans-serif';ctx.fillText(s.label,80,y);y+=52;}
    ctx.fillStyle=s.color;ctx.font=`${s.size}px "PingFang SC", "Microsoft YaHei", sans-serif`;
    for(const line of s.lines){ctx.fillText(line,80,y);y+=s.gap;}y+=48;
  }
  ctx.fillStyle='#697569';ctx.font='22px sans-serif';ctx.fillText(demo==='catalog'?'原创合成角色 · 娱乐创作':demo?'虚构故事示例 · 不是对你的判断':'个人表达 · 待验证，不是人格鉴定',80,canvas.height-125);
  ctx.font='20px sans-serif';ctx.fillText('github.com/xu2333/RunAWay',80,canvas.height-82);
  return canvas;
}
