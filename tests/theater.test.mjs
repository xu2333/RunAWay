import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {SCENES,EPISODES} from '../web/dist/theater-data.mjs';
import {contextFor,validateStory,parseStory,makeSceneRequest,selectionHash,readSelection,storyText,renderScene} from '../web/dist/theater-core.mjs';
const catalog=JSON.parse(await readFile(new URL('../web/dist/catalog.json',import.meta.url),'utf8'));
const context=e=>contextFor(catalog,SCENES,...e.story.cast,e.story.scene_id);
test('all eight original scripts refer to actual residents and alternate six bounded turns',()=>{
  assert.equal(EPISODES.length,8);assert.equal(new Set(EPISODES.map(e=>e.id)).size,8);
  for(const episode of EPISODES){assert.equal(episode.origin,'scripted_example');validateStory(episode.story,context(episode));}
});
test('requests contain only the selected pair and require responses to a shared interruption',()=>{
  const c=context(EPISODES[0]),request=makeSceneRequest(c);
  for(const entry of c.cast)for(const value of Object.values(entry.card))assert.ok(request.includes(value));
  assert.ok(request.includes(c.scene.twist));assert.ok(request.includes('下一句要回应上一句'));
  assert.ok(!request.includes('后悔药分装师'));assert.ok(request.length<6000);
});
test('preset links reproduce scripts; combination links never include imported story text',()=>{
  for(const e of EPISODES){const parsed=readSelection('#episode='+e.id,catalog,SCENES,EPISODES);assert.equal(parsed.episode,e);}
  const c=context(EPISODES[0]),hash=selectionHash(c),parsed=readSelection(hash,catalog,SCENES,EPISODES);
  assert.equal(parsed.episode,null);assert.deepEqual(parsed.context,c);
  assert.ok(!hash.includes(EPISODES[0].story.title));assert.ok(!hash.includes('turns'));
  const single=readSelection('#a=RW-0101',catalog,SCENES,EPISODES);assert.equal(single.context.cast[0].id,'RW-0101');assert.notEqual(single.context.cast[1].id,'RW-0101');
  assert.throws(()=>readSelection('#episode=missing',catalog,SCENES,EPISODES));
  assert.throws(()=>contextFor(catalog,SCENES,'RW-0001','RW-0001','trip'));
  assert.throws(()=>contextFor(catalog,SCENES,'missing','RW-0001','trip'));
});
test('old-context responses, extra fields, attribution errors and oversized lines fail before export',()=>{
  const e=EPISODES[0],c=context(e),copy=()=>structuredClone(e.story);
  assert.deepEqual(parseStory('```json\n'+JSON.stringify(e.story)+'\n```',c),e.story);
  assert.throws(()=>validateStory(e.story,context(EPISODES[1])),/另一组/);
  const swapped={...c,cast:[...c.cast].reverse()};assert.throws(()=>validateStory(e.story,swapped));
  assert.throws(()=>validateStory({...e.story,compatibility:99},c));
  let changed=copy();changed.turns[1].speaker=changed.cast[0];assert.throws(()=>validateStory(changed,c));
  changed=copy();changed.turns[0].text='哈'.repeat(101);assert.throws(()=>validateStory(changed,c));
  changed=copy();changed.turns.pop();assert.throws(()=>validateStory(changed,c));
  assert.throws(()=>parseStory('x'.repeat(10001),c));
});
test('text exports include complete dialogue, both names and actual origin, with no compatibility score',()=>{
  for(const e of EPISODES){const c=context(e),text=storyText(e.story,c,e.origin);for(const t of e.story.turns)assert.ok(text.includes(t.text));for(const person of c.cast)assert.ok(text.includes(person.card.name));assert.ok(text.includes('预写小剧场'));assert.ok(text.includes(e.story.outcome));}
  assert.ok(storyText(EPISODES[0].story,context(EPISODES[0]),'model_import').includes('AI 剧情'));
  assert.throws(()=>storyText(EPISODES[0].story,context(EPISODES[0]),'real_conversation'));
});
test('PNG layout grows for maximal dialogue and keeps all six lines above the provenance footer',()=>{
  const story=structuredClone(EPISODES[0].story);story.title='标题'.repeat(15);story.outcome='结局'.repeat(45);story.invite='邀请'.repeat(35);
  story.turns.forEach(t=>t.text='对话'.repeat(50));
  const painted=[];const ctx={measureText:text=>({width:[...text].length*28}),fillRect(){},strokeRect(){},beginPath(){},roundRect(){},fill(){},fillText(text,x,y){painted.push({text,x,y});}};
  const canvas={width:0,height:0,getContext:()=>ctx};renderScene(canvas,story,context(EPISODES[0]),'model_import');
  assert.equal(canvas.width,960);assert.ok(canvas.height>2000);
  assert.ok(painted.every(p=>p.y>0&&p.y<canvas.height));
  const provenance=painted.find(p=>p.text.includes('虚构创作'));
  assert.ok(painted.filter(p=>!p.text.includes('github.com')&&p!==provenance).every(p=>p.y<provenance.y));
});
