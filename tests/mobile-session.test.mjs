import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {Session} from '../apps/mobile/src/session.mjs';
import {BOUNDARY,makeExport} from '../packages/harnesses/index.mjs';
import {HEADER,hash,canonical} from '../web/dist/core.mjs';

const demo=JSON.parse(await readFile(new URL('../web/dist/demo.json',import.meta.url),'utf8'));
function ready(){const s=new Session();s.prepare(JSON.stringify(demo.sources),'trajectory',2400);s.importAnswer(JSON.stringify(demo.answer));return s;}
test('mobile imports the actual website profile with exact quotes and the same prompt bytes',async()=>{
  const s=ready(),bundle=await s.bundle();assert.equal(bundle.portable.text,HEADER+demo.answer.prompt+'\n');
  for(const target of ['codex','claude-code','antigravity'])assert.ok((await makeExport(target,bundle.portable.text)).files[0].content.includes(bundle.portable.text));
  const bad=structuredClone(demo.answer);bad.claims[0].evidence[0].quote='A made up quote';assert.throws(()=>s.importAnswer(JSON.stringify(bad)),/引文/);
  assert.equal((await s.bundle()).portable.id,bundle.portable.id);
});
test('private archive roundtrip preserves source, detailed evidence, edits and export identity',async()=>{
  const s=ready();s.body+=' 条件不足时先确认。';const first=await s.bundle();const next=new Session();
  await next.restore(JSON.stringify(s.archive()));const second=await next.bundle();
  assert.deepEqual(second,first);assert.deepEqual(next.answer.claims,s.answer.claims);assert.deepEqual(next.prepared.sources,s.prepared.sources);
  assert.ok(next.request().includes('SOURCE_JSON:'));assert.equal(next.request(),s.request());
});
test('existing 1600-character browser session restores without losing original material',async()=>{
  const s=ready();s.prepared.budget=1600;
  const old={...s.archive(),artifact_type:'browser_session',prepared:{...s.prepared,holdout:{private:true}}};
  const next=new Session();await next.restore(JSON.stringify(old));assert.equal(next.prepared.budget,1600);assert.deepEqual((await next.bundle()).portable,(await s.bundle()).portable);
});
test('portable-only import checks identity and strips raw source from harness export',async()=>{
  const first=await ready().bundle(),next=new Session();await next.restore(JSON.stringify(first.portable));
  assert.deepEqual((await next.bundle()).portable,first.portable);assert.equal(next.answer,null);assert.equal(next.prepared,null);assert.throws(()=>next.archive());
  const bad={...first.portable,text:BOUNDARY+'tampered'};await assert.rejects(next.restore(JSON.stringify(bad)),/校验/);assert.deepEqual((await next.bundle()).portable,first.portable);
  const packet=await makeExport('codex',first.portable.text);assert.ok(!Object.hasOwn(packet,'sources'));assert.ok(!Object.hasOwn(packet,'profile'));
});
test('over-budget edits, malformed archives, broken Unicode and automation sources fail closed',async()=>{
  const s=ready(),before=await s.bundle();const bad=s.archive();bad.edited_prompt='x'.repeat(2401);
  await assert.rejects(s.restore(JSON.stringify(bad)),/预算/);assert.deepEqual(await s.bundle(),before);
  await assert.rejects(s.restore('{bad'));assert.deepEqual(await s.bundle(),before);
  s.body='x'.repeat(2401);await assert.rejects(s.bundle(),/预算/);
  assert.throws(()=>new Session().prepare('<heartbeat>','experience',1536),/自动化/);
  assert.throws(()=>new Session().prepare('\ud800','experience',1536));
});
test('native configuration has no server URL, network permission or broad file grants',async()=>{
  const get=name=>readFile(new URL('../apps/mobile/'+name,import.meta.url),'utf8');
  const config=JSON.parse(await get('capacitor.config.json'));assert.equal(config.server.url,undefined);assert.equal(config.plugins.CapacitorHttp.enabled,false);assert.equal(config.server.cleartext,false);
  const android=await get('android/app/src/main/AndroidManifest.xml');assert.ok(!android.includes('uses-permission'));assert.ok(android.includes('android:allowBackup="false"'));
  const paths=await get('android/app/src/main/res/xml/file_paths.xml');assert.ok(!paths.includes('external-path'));assert.ok(paths.includes('runaway-exports/'));
  const html=await get('src/index.html');assert.ok(html.includes("connect-src 'none'"));assert.ok(!/https?:\/\//.test(html));
  const source=await get('src/app.mjs');assert.ok(!/\b(fetch|XMLHttpRequest|WebSocket|localStorage|indexedDB)\b/.test(source));
});
