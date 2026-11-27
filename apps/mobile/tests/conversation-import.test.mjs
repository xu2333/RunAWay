import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {zipSync,strToU8} from 'fflate';
import {pack,recognize,readConversationFile} from '../src/conversation-import.mjs';
import {Session} from '../src/session.mjs';

const fixture = name=>readFile(new URL('fixtures/chat-import/'+name,import.meta.url),'utf8');
const labels=['user','assistant','user'];
for(const name of ['codex-export.md','rollout.jsonl','claude-code.jsonl','chatgpt-conversations.json','claude-conversations.json']){
  test('read '+name+' without rewriting or inverting speakers',async()=>{
    const {chats}=await readConversationFile(new File([await fixture(name)],name));
    const turns=chats[0].read();assert.deepEqual(turns.map(m=>m.role),labels);
    assert.deepEqual(turns.map(m=>m.text),['潮牌只写展柜号。','那也写库房号吗？','不写库房号，空着。']);
    const s=new Session();s.prepare(pack(turns),'trajectory',768);
    assert.equal(s.prepared.sources.sources.length,3);
  });
}
test('follow the displayed chat branch, excluding hidden messages and sibling conversations',async()=>{
  const [chat]=JSON.parse(await fixture('chatgpt-conversations.json'));
  chat.mapping.alt={...chat.mapping['3'],message:{author:{role:'user'},content:{content_type:'text',parts:['WRONG_BRANCH']}}};
  chat.mapping['2'].children.push('alt');chat.mapping['1'].message.metadata={is_visually_hidden_from_conversation:true};
  const two=JSON.parse(await fixture('claude-conversations.json'));
  const raw=zipSync({'part/conversations-000.json':strToU8(JSON.stringify([chat])),'conversations-001.json':strToU8(JSON.stringify(two)),'assets/conversation-image.bin':new Uint8Array([0xff])});
  const {chats}=await readConversationFile(new File([raw],'history.zip'));
  assert.equal(chats.length,2);assert.deepEqual(chats[0].read().map(m=>m.role),['assistant','user']);assert.doesNotMatch(pack(chats[0].read()),/WRONG_BRANCH/);
  chat.mapping['2'].parent='3';assert.throws(()=>recognize(JSON.stringify(chat))[0].read(),/分支/);
});
test('tool results, app-injected context and a duplicated Codex event stay out',async()=>{
  const raw=await fixture('rollout.jsonl');
  const result=recognize(raw+'\n'+[JSON.stringify({type:'event_msg',payload:{type:'user_message',message:'duplicate'}}),JSON.stringify({type:'response_item',payload:{role:'user',type:'message',content:[{type:'input_text',text:'<environment_context>internal'}]}})].join('\n'))[0].read();
  assert.deepEqual(result.map(t=>t.role),labels);
  const cc=await fixture('claude-code.jsonl');
  const tool=JSON.stringify({type:'user',message:{role:'user',content:[{type:'tool_result',content:'not a user'}]}});
  assert.equal(recognize(cc+'\n'+tool)[0].read().length,3);
});
test('Codex fenced text keeps its speaker and Activity is excluded',()=>{
  const text='# Codex conversation\n## User\nhello\n## Activity\nprivate output\n## Assistant\n~~~\n## User\n~~~';
  assert.deepEqual(recognize(text)[0].read(),[{role:'user',text:'hello'},{role:'assistant',text:'~~~\n## User\n~~~'}]);
});
test('unknown or damaged archive is actionable',async()=>{
  await assert.rejects(readConversationFile(new File([zipSync({'photo.jpg':new Uint8Array(1)})],'data.zip')),/没有可导入/);
  await assert.rejects(readConversationFile(new File([new Uint8Array([255])],'x.txt')),/UTF-8/);
});
test('native Claude Code export requires operator review of dots including status output',async()=>{
  const [chat]=recognize(await fixture('claude-export.txt'));
  assert.equal(chat.review,true);
  assert.deepEqual(chat.read().map(t=>t.role),['user','assistant','user','assistant']);
  assert.match(chat.read()[3].text,/Session model/);
});
