import {normalize,validateCard} from './presentation.mjs';

export function validateCatalog(data){
  if(data?.artifact_type!=='runaway_synthetic_catalog'||data.schema_version!==1||data.entries?.length!==700||data.categories?.length!==28)throw Error('角色目录格式不正确。');
  const categories=new Set(data.categories.map(c=>c.id));
  if(categories.size!==28)throw Error('目录分类重复。');
  const ids=new Set(),names=new Set();
  for(const entry of data.entries){
    validateCard(entry.card);
    const name=normalize(entry.card.name);
    if(!/^RW-\d{4}$/.test(entry.id)||ids.has(entry.id)||names.has(name)||!categories.has(entry.category)||entry.origin!=='synthetic_catalog')throw Error('角色来源或编号不正确。');
    ids.add(entry.id);names.add(name);
  }
  for(const category of categories)if(data.entries.filter(e=>e.category===category).length!==25)throw Error('分类数量不正确。');
  return data;
}
export function filterEntries(data,query='',category=''){
  const terms=query.trim().split(/\s+/u).map(normalize).filter(Boolean);
  const labels=new Map(data.categories.map(c=>[c.id,c.name]));
  return data.entries.filter(e=>{
    if(category&&e.category!==category)return false;
    const haystack=normalize([e.id,e.card.name,e.card.tagline,e.card.tell,labels.get(e.category)].join(' '));
    return terms.every(term=>haystack.includes(term));
  });
}
export function entryFromHash(data,hash){
  return data.entries.find(e=>e.id===hash.replace(/^#/,''))||null;
}
export function pickEntry(entries,previousId='',random=Math.random){
  const pool=entries.length>1?entries.filter(e=>e.id!==previousId):entries;
  return pool.length?pool[Math.min(pool.length-1,Math.max(0,Math.floor(random()*pool.length)))]:null;
}
export function fictionalPrompt(entry){
  if(entry.origin!=='synthetic_catalog')throw Error('仅用于原创虚构角色。');
  validateCard(entry.card);
  return `请扮演 RunAWay 的原创虚构角色「${entry.card.name}」（${entry.id}），参与我接下来给出的情境。\n一句话：${entry.card.tagline}\n行为倾向：${entry.card.tell}\n适用提醒：${entry.card.boundary}\n\n这是娱乐用的角色设定，不是对我或任何真实人物的判断。把倾向转化为具体选择与说话方式，不必每句重复梗；信息不足时保留不确定性。遵守当前任务的明确要求，不把角色设定当成事实身份或行动授权。\n\n场景：〔在这里写你的架空场景或任务〕`;
}
