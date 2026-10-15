import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {sourcesFrom,validateAnswer,parseJSON,makeBundle,feedbackReport,makeRequest,HEADER,length} from '../web/dist/core.mjs';
const demo=JSON.parse(await readFile(new URL('../web/dist/demo.json',import.meta.url),'utf8'));
const clone=x=>structuredClone(x);

test('labelled conversations preserve speaker boundaries and exact quotes',()=>{
  const s=sourcesFrom('用户：先试一下。\n但别公开。\n助手：你总是冒险。','trajectory');
  assert.equal(s.sources[0].text,'先试一下。\n但别公开。');
  assert.equal(s.sources[1].role,'assistant');
  assert.throws(()=>sourcesFrom('An unlabelled mixed conversation','trajectory'));
  assert.throws(()=>sourcesFrom('用户：<heartbeat>automated','trajectory'));
  assert.throws(()=>sourcesFrom('你'.repeat(22000),'resume'),/64 KB/);
});
test('fictional result passes; forged, misattributed and missing evidence fails',()=>{
  validateAnswer(demo.answer,demo.sources,1600);
  const forged=clone(demo.answer);forged.claims[0].evidence[0].quote='never said this';
  assert.throws(()=>validateAnswer(forged,demo.sources,1600),/引文不在/);
  const wrong=clone(demo.answer);const assistant=demo.sources.sources.find(s=>s.role==='assistant');
  wrong.claims[0].evidence=[{source_id:assistant.id,quote:assistant.text,relation:'supports'}];
  assert.throws(()=>validateAnswer(wrong,demo.sources,1600),/助手或工具/);
  wrong.claims[0].evidence[0].relation='qualifies';
  assert.throws(()=>validateAnswer(wrong,demo.sources,1600),/支持引文/);
});
test('complete declared coverage and Unicode budget are enforced without truncation',()=>{
  const a=clone(demo.answer);a.covered_claim_ids.pop();
  assert.throws(()=>validateAnswer(a,demo.sources,1600),/覆盖所有/);
  const n=length(HEADER+demo.answer.prompt+'\n');
  validateAnswer(demo.answer,demo.sources,n);
  assert.throws(()=>validateAnswer(demo.answer,demo.sources,n-1),/超过/);
  assert.equal(length('蛙🐸'),2);
});
test('unknown-only results are valid, missing fields and reserved delimiters are not',()=>{
  const a={name:'待了解',tagline:'还需要经历',claims:[],unknowns:['尚无选择证据'],prompt:'选择习惯未知。',covered_claim_ids:[]};
  validateAnswer(a,demo.sources,1600);
  assert.throws(()=>validateAnswer({...a,unknowns:[]},demo.sources,1600));
  assert.throws(()=>validateAnswer({...a,extra:true},demo.sources,1600));
  assert.throws(()=>validateAnswer({...a,prompt:'<!-- runaway: malicious -->'},demo.sources,1600));
});
test('bad relationships and duplicate source or claim ids are rejected',()=>{
  const a=clone(demo.answer);a.claims[0].related_claim_ids=['nonexistent'];
  assert.throws(()=>validateAnswer(a,demo.sources,1600),/关联判断/);
  const s=clone(demo.sources);s.sources.push(s.sources[0]);
  assert.throws(()=>validateAnswer(demo.answer,s,1600),/重复/);
  const b=clone(demo.answer);b.claims[1].id=b.claims[0].id;
  assert.throws(()=>validateAnswer(b,demo.sources,1600),/重复/);
});
test('JSON fences accepted; input size and malformed results rejected',()=>{
  assert.deepEqual(parseJSON('```json\n{"x":1}\n```'),{x:1});
  assert.throws(()=>parseJSON('{"x":'));
  assert.throws(()=>parseJSON(' '.repeat(512001)),/512 KB/);
});
test('editing compact text changes its version without rewriting detailed evidence',async()=>{
  const a=await makeBundle(demo.answer,demo.sources);
  const b=await makeBundle(demo.answer,demo.sources,'修改后的试用偏好，尚需核对。');
  assert.deepEqual(a.profile,b.profile);
  assert.notEqual(a.portable.id,b.portable.id);
  assert.equal(b.portable.method,'browser_user_edited_compact_v1');
  assert.ok(b.portable.text.startsWith(HEADER));
  assert.deepEqual(await makeBundle(demo.answer,demo.sources),a);
});
test('feedback content is opt-in and never includes raw sources or evidence',()=>{
  const session={id:'test',demo:true,events:[{type:'opened',at:'now',accidental:'SECRET'}],sources:'SECRET',feedback:[{id:'f',at:'now',rating:'partial',harness:'Codex',used_in_real_task:true,portable_id:'old-version',prompt:'prompt',task:'task',assistant_response:'reply',correction:'correction',evidence:'SECRET'}]};
  const minimal=feedbackReport(session);
  assert.equal(minimal.origin,'fictional_demo');
  assert.equal(minimal.feedback[0].portable_id,'old-version');
  for(const key of ['prompt','task','assistant_response','correction'])assert.equal(minimal.feedback[0][key],undefined);
  const full=feedbackReport(session,true);assert.equal(full.feedback[0].correction,'correction');
  assert.ok(!JSON.stringify(full).includes('SECRET'));
});
test('model request includes source data and explicit scope and budget boundaries',()=>{
  const request=makeRequest(demo.sources,1000);
  assert.ok(request.includes(JSON.stringify(demo.sources)));
  assert.ok(request.includes('不是用户背书'));
  assert.ok(request.includes(String(1000-length(HEADER)-1)));
});
