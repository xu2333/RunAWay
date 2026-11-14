import {Capacitor} from '@capacitor/core';
import {Filesystem,Directory} from '@capacitor/filesystem';
import {Share} from '@capacitor/share';

const EXPORTS='runaway-exports';
export async function cleanExports() {
  if(!Capacitor.isNativePlatform()) return;
  try { await Filesystem.rmdir({path:EXPORTS,directory:Directory.Cache,recursive:true}); }
  catch(e) { if(e?.code!=='OS-PLUG-FILE-0008' && !/not exist|not found|doesn't exist/i.test(e?.message||'')) throw e; }
}
export async function saveFile(name,data,mime) {
  if(!/^[A-Za-z0-9_.-]+$/.test(name)) throw Error('Invalid export name.');
  const bytes=typeof data==='string'?new TextEncoder().encode(data):data;
  if(!Capacitor.isNativePlatform()) {
    const blob=new Blob([bytes],{type:mime}),url=URL.createObjectURL(blob),a=document.createElement('a');
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    return {status:'download_requested'};
  }
  // Cache is outside device backups; no private history is stored automatically.
  // The OS chooser lets the owner save to Files or explicitly share elsewhere.
  let binary=''; for(const byte of bytes) binary+=String.fromCharCode(byte);
  const folder=EXPORTS+'/'+crypto.randomUUID(),file=folder+'/'+name;
  await Filesystem.mkdir({path:folder,directory:Directory.Cache,recursive:true});
  try {
    const result=await Filesystem.writeFile({path:file,directory:Directory.Cache,data:btoa(binary)});
    await Share.share({title:'RunAWay · 带走你的判断',files:[result.uri],dialogTitle:'保存到文件或发送到你的设备'});
    return {status:'share_sheet_closed'};
  } catch(e) {
    await Filesystem.rmdir({path:folder,directory:Directory.Cache,recursive:true}).catch(()=>{});
    throw e;
  }
  // Keep a successful hand-off readable by its recipient. Clean this cache on
  // the next cold launch or explicit clear, rather than racing another app.
}
export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const area=document.createElement('textarea');area.value=text;document.body.append(area);area.select();
    const ok=document.execCommand('copy');area.remove();if(!ok)throw Error('请长按文本框，手动选择并复制。');
  }
}
