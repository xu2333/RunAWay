import {pack} from './conversation-import.mjs';

const $=id=>document.getElementById(id);
const size=value=>new TextEncoder().encode(value).length;
export function createPicker(apply, saveExcerpt) {
  const dialog=$('conversation-picker'), choice=$('chat-choice');
  let chats=[], turns=[];
  const error=message=>{ $('chat-error').textContent=message; $('chat-error').hidden=!message; };
  function range() {
    const a=$('turn-from').valueAsNumber, b=$('turn-to').valueAsNumber;
    if(!Number.isInteger(a)||!Number.isInteger(b)||a<1||b>turns.length||b<a)
      throw Error('请选择有效的起止条数。');
    const selected=turns.slice(a-1,b);
    if($('chat-review').hidden)return selected;
    return selected.filter((_,i)=>$('chat-blocks').children[a-1+i].querySelector('input').checked);
  }
  function preview(){
    try {
      const part=range();
      if(!part.length) throw Error('请选中要保留的发言。');
      const first=part[0].text, last=part[part.length-1].text;
      $('chat-range-preview').textContent='开头：'+first.slice(0,90)+'\n结尾：'+last.slice(-90);
      if(size(pack(part))>64000) throw Error('这段超出 64 KB，请缩小起止范围。');
      error(''); $('save-excerpt').disabled=$('choose-chat').disabled=false;
    } catch(e){ error(e.message); $('save-excerpt').disabled=$('choose-chat').disabled=true; }
  }
  function select(){
    turns=[]; $('chat-review').hidden=true; $('chat-blocks').replaceChildren(); error(''); $('save-excerpt').disabled=$('choose-chat').disabled=true;
    $('chat-range-preview').textContent=''; $('chat-size').textContent='';
    try {
      if(!choice.value) throw Error('没有匹配的对话。');
      const chat=chats[Number(choice.value)];
      turns=chat.read();
      if(chat.review){
        if(turns.length>300)throw Error('文字版超过 300 段，请选择会话 JSONL 或复制较短片段。');
        $('chat-review').hidden=false;
        for(const t of turns){
          const label=document.createElement('label'),box=document.createElement('input');
          box.type='checkbox';box.checked=t.role==='user';label.append(box,
            (t.role==='user'?'我：':'助手或提示：')+t.text);
          $('chat-blocks').append(label);
        }
      }
      if(!turns.length) throw Error('这段对话没有可导入的文字，请换一段。');
      $('chat-size').textContent=turns.length+' 条用户及助手文字，可选连续片段。';
      $('turn-from').value='1'; $('turn-to').value=String(turns.length);
      for(const id of ['turn-from','turn-to']) $(id).max=String(turns.length);
      preview();
    } catch(e){error(e.message);}
  }
  function filter(){
    choice.replaceChildren();
    const q=$('chat-filter').value.trim().toLowerCase();
    chats.forEach((chat,index)=>{
      const title=String(chat.title);
      if (title.toLowerCase().includes(q)) choice.add(new Option(title,String(index)));
    });
    select();
  }
  $('chat-filter').addEventListener('input',filter);
  choice.addEventListener('change',select);
  $('chat-blocks').addEventListener('change',preview);
  for(const id of ['turn-from','turn-to']) $(id).addEventListener('input',preview);
  $('choose-chat').addEventListener('click',()=>{
    try{apply(range());dialog.close();}catch(e){error(e.message);}
  });
  $('save-excerpt').addEventListener('click',async()=>{
    try{await saveExcerpt(pack(range()));dialog.close();}catch(e){error(e.message);}
  });
  dialog.addEventListener('close',()=>{
    chats=[]; turns=[]; choice.replaceChildren(); $('chat-blocks').replaceChildren(); $('chat-filter').value='';
    $('chat-range-preview').textContent=''; $('chat-size').textContent=''; error('');
  });
  return (items,{selectRange=false}={})=>{
    if(!selectRange && items.length===1 && !items[0].review){
      const only=items[0].read();
      if(size(pack(only))<=64000){apply(only);return;}
    }
    chats=items; $('chat-filter').value=''; filter(); dialog.showModal();
  };
}
