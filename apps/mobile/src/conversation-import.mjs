import {Unzip, UnzipInflate} from 'fflate';

const MiB = 1024 * 1024;
const maxText = 64 * MiB;
const maxZip = 256 * MiB;
const decoder = () => new TextDecoder('utf-8', {fatal:true});
function decode(bytes) {
  try { return decoder().decode(bytes); }
  catch { throw Error('文件编码无法识别，请选 UTF-8 文本或原始导出 ZIP。'); }
}
function json(text) {
  try { return JSON.parse(text); }
  catch { throw Error('对话文件不是完整的 JSON，请重新选择原始导出文件。'); }
}
function turn(role, text) {
  if (!['user','assistant'].includes(role) || typeof text !== 'string' || !text.trim()) return [];
  return [{role,text}];
}
function blocks(content, allowed) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  return content.filter(b => allowed.includes(b?.type) && typeof b.text === 'string').map(b => b.text).join('\n');
}
function chatGPT(c) {
  const seen = new Set(), path = [];
  let id = c.current_node;
  if (!id) throw Error('这段 ChatGPT 对话缺少当前分支，请复制屏幕上的对话片段。');
  while (id != null) {
    const node = Object.hasOwn(c.mapping,id) && c.mapping[id];
    if (!node || seen.has(id)) throw Error('ChatGPT 对话分支不完整，请复制所需片段。');
    seen.add(id);
    const m = node.message;
    if (m && !m.metadata?.is_visually_hidden_from_conversation && (!m.recipient || m.recipient==='all') &&
        ['text','multimodal_text'].includes(m.content?.content_type) && Array.isArray(m.content.parts)) {
      path.push(...turn(m.author?.role,m.content.parts.filter(t=>typeof t==='string').join('\n')));
    }
    id = node.parent;
  }
  return path.reverse();
}
function archiveEntry(c) {
  if (c?.mapping && typeof c.mapping === 'object')
    return {title:c.title || 'ChatGPT 对话', read:()=>chatGPT(c)};
  if (Array.isArray(c?.chat_messages))
    return {title:c.name || 'Claude 对话', read:()=>c.chat_messages.flatMap(m=>
      turn(m.sender==='human'?'user':m.sender, blocks(m.content,['text']) || m.text))};
  throw Error('文件中有无法识别的对话，请选择 ChatGPT 或 Claude 的 conversations JSON。');
}
function logTurns(rows) {
  if (rows.some(r=>r?.type==='response_item' || r?.type==='session_meta')) {
    return rows.flatMap(r=>{
      const m=r.payload;
      if (r.type!=='response_item' || m?.type!=='message') return [];
      const t=blocks(m.content,['input_text','output_text']);
      if (m.role==='user' && /^\s*<(?:environment_context|user_instructions|permissions instructions|subagent_notification|heartbeat|turn_aborted|INSTRUCTIONS|skills_instructions|in-app-browser-context)\b/i.test(t)) return [];
      return turn(m.role,t);
    });
  }
  if (rows.some(r=>['user','assistant'].includes(r?.type) && r.message)) {
    const turns=[],children=new Map();
    for (const r of rows) {
      if (r?.isSidechain || r?.isMeta || r?.isCompactSummary || !['user','assistant'].includes(r?.type) || r.message?.role!==r.type) continue;
      if (r.parentUuid && r.uuid) {
        if(children.has(r.parentUuid) && children.get(r.parentUuid)!==r.uuid) throw Error('这个会话文件含有分支，请从目标分支复制所需消息。');
        children.set(r.parentUuid,r.uuid);
      }
      const text=blocks(r.message.content,['text']);
      if(r.type==='user' && /^\s*<(?:local-command-|command-name>|system-reminder>)/i.test(text)) continue;
      turns.push(...turn(r.type,text));
    }
    return turns;
  }
  throw Error('未识别这些日志。请选择 Codex 或 Claude Code 的单个会话文件。');
}
function codexMarkdown(raw) {
  const turns=[]; let role=null, lines=[], fence=null;
  const flush=()=>turns.push(...turn(role,lines.join('\n').trim()));
  for (const line of raw.split(/\r?\n/).slice(1)) {
    const match=/^( {0,3})(`{3,}|~{3,})(.*)$/.exec(line);
    if (match) {
      if (!fence) fence=match[2];
      else if(match[2][0]===fence[0] && match[2].length>=fence.length && !match[3].trim()) fence=null;
    }
    const heading=!fence && /^## (User|Assistant|Plan|Activity|System|Developer|Tool|Reasoning)$/.exec(line);
    if (heading) { flush(); role=heading[1].toLowerCase(); lines=[]; }
    else lines.push(line);
  }
  flush(); return turns;
}
// Return descriptors so choosing one chat never adds siblings to the request.
export function recognize(raw, name='') {
  const text=raw.trim();
  if (/Claude Code v\d+\./.test(text.slice(0,200)) && /^❯ /m.test(text)) {
    // The terminal renders assistant text and operational notices with the same dot.
    // Expose every segment for explicit selection; discard the terminal banner.
    const turns=[]; let role=null, lines=[];
    const flush=()=>turns.push(...turn(role,lines.join('\n').trim()));
    for(const line of text.split(/\r?\n/)){
      const start=/^([❯⏺]) (.*)$/.exec(line);
      if(start){flush();role=start[1]==='❯'?'user':'assistant';lines=[start[2]];}
      else if(role)lines.push(line.replace(/^  /,''));
    }
    flush();
    return [{title:'Claude Code 文字导出',review:true,read:()=>turns}];
  }
  if (/^# Codex conversation\r?\n/.test(text)) return [{title:'Codex 对话',read:()=>codexMarkdown(text)}];
  if (/\.jsonl$/i.test(name) || /^\{[^\n]*\}\s*\r?\n\s*\{/.test(text)) {
    return [{title:'会话记录',read:()=>logTurns(text.split(/\r?\n/).filter(s=>s.trim()).map(json))}];
  }
  if (text.startsWith('[') || text.startsWith('{')) {
    let data;
    try { data=JSON.parse(text); } catch { return null; }
    if (Array.isArray(data) && data.some(c=>c?.mapping || c?.chat_messages)) return data.map(archiveEntry);
    if (data?.mapping || data?.chat_messages) return [archiveEntry(data)];
    if (data?.type && (data.payload || data.message)) return [{title:'会话记录',read:()=>logTurns([data])}];
  }
  return null;
}
async function archivedChats(file) {
  if (file.size>maxZip) throw Error('压缩包超过 256 MiB。请先解压，再选择 conversations JSON 或复制一段对话。');
  let total=0, found=0;
  const chats=[];
  const zip=new Unzip(entry=>{
    if (!/(^|\/)conversations(?:[-_]\d+(?:-of-\d+)?)?\.json$/i.test(entry.name) || /(^|\/)__MACOSX\//.test(entry.name)) return;
    if (++found>256 || entry.originalSize>maxText-total) throw Error('导出的对话数据超过 64 MiB，请选较小的分卷或复制片段。');
    const chunks=[]; let size=0;
    entry.ondata=(err,chunk,final)=>{
      if(err) throw err;
      size+=chunk.length;total+=chunk.length;
      if(total>maxText) throw Error('导出的对话数据超过 64 MiB，请选较小的分卷或复制片段。');
      chunks.push(chunk);
      if(final) {
        const bytes=new Uint8Array(size); let offset=0;
        for(const c of chunks){ bytes.set(c,offset);offset+=c.length; }
        const data=json(decode(bytes));
        if(!Array.isArray(data)) throw Error('压缩包中的会话文件格式无法识别。');
        for(const c of data) chats.push(archiveEntry(c));
      }
    };
    entry.start();
  });
  zip.register(UnzipInflate);
  for(let start=0;start<file.size;start+=256*1024){
    const bytes=new Uint8Array(await file.slice(start,start+256*1024).arrayBuffer());
    for(let i=0;i<bytes.length;i+=4096){
      const stop=Math.min(i+4096,bytes.length);
      zip.push(bytes.subarray(i,stop),start+stop===file.size);
    }
  }
  if(!chats.length) throw Error('压缩包里没有可导入的 conversations JSON。也可以直接复制对话。');
  return chats;
}
export async function readConversationFile(file) {
  if(/\.zip$/i.test(file.name)) return {chats:await archivedChats(file)};
  if(file.size>maxText) throw Error('文件超过 64 MiB，请选一个会话或较小的分卷。');
  const raw=decode(new Uint8Array(await file.arrayBuffer()));
  return {chats:recognize(raw,file.name),raw};
}
export function pack(turns) {
  if(!turns.length) throw Error('所选范围没有可导入的用户或助手文字。');
  return JSON.stringify({schema_version:1,sources:turns.map(({role,text},i)=>({id:'message-'+(i+1),episode_id:'submitted',role,text}))});
}
