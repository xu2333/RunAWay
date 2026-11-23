import {Capacitor,registerPlugin} from '@capacitor/core';

const SaveDocument=registerPlugin('SaveDocument');
export async function cleanExports() {
  if(!Capacitor.isNativePlatform()) return;
  await SaveDocument.clear();
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
  // The native system picker writes only to the owner's selected document.
  let binary=''; for(const byte of bytes) binary+=String.fromCharCode(byte);
  return SaveDocument.save({name,data:btoa(binary),mime});
}
export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const area=document.createElement('textarea');area.value=text;document.body.append(area);area.select();
    try { if(!document.execCommand('copy'))throw Error('请长按文本框，手动选择并复制。'); }
    finally { area.remove(); }
  }
}
