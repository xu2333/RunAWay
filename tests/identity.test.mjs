import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {makeBundle,validateAnswer,makeRequest} from '../web/dist/core.mjs';
import {validateManual,manualText,renderManual} from '../web/dist/manual-core.mjs';
import {lockCase,makeTrial,prediction,assess,puzzleText,revealText} from '../web/dist/holdout-core.mjs';
const d=JSON.parse(await readFile(new URL('../web/dist/demo.json',import.meta.url),'utf8'));
const bundle=await makeBundle(d.answer,d.sources);
const input={...d.holdout_demo,source:'SECRET_HISTORY '+d.holdout_demo.source,reason:'SECRET_REASON'};
const heldout=await lockCase(input,d.sources);
const p=(id,choice='unknown')=>({request_id:id,choice,reason:'材料不足，暂不判断。'});
test('manual angles need real claim IDs; omissions and legacy answers remain supported',()=>{
  validateAnswer(d.answer,d.sources,1600);
  const old=structuredClone(d.answer);delete old.manual;validateAnswer(old,d.sources,1600);
  assert.throws(()=>validateManual({...d.answer.manual,items:[{kind:'persuade',text:'声称',claim_ids:['fake']}]},d.answer.claims));
  assert.throws(()=>validateManual({...d.answer.manual,items:[d.answer.manual.items[0],d.answer.manual.items[0]]},d.answer.claims));
  assert.throws(()=>validateManual({headline:'说点什么',items:[]},[]));
  validateManual({headline:'材料还不足以写使用说明',items:[]},[]);
  validateManual({...d.answer.manual,items:[d.answer.manual.items[0]]},d.answer.claims);
  assert.throws(()=>validateManual({headline:'x',items:[{kind:'toString',text:'x',claim_ids:[d.answer.claims[0].id]}]},d.answer.claims));
});
test('manual edits do not rewrite profile or portable identity and shares omit evidence',async()=>{
  const changed=structuredClone(d.answer);changed.manual.items[0].text='本人修改的措辞';assert.deepEqual(await makeBundle(changed,d.sources),bundle);
  const share=manualText(d.answer.name,changed.manual,d.answer.claims,true);assert.ok(share.includes('虚构示例'));assert.ok(share.includes('本人修改'));
  for(const c of d.answer.claims)for(const e of c.evidence)assert.ok(!share.includes(e.quote));
});
test('maximal manual card keeps content above provenance footer',()=>{
  const manual={headline:'标题'.repeat(30),items:['persuade','friction','change'].map(kind=>({kind,text:'正文'.repeat(60),claim_ids:[d.answer.claims[0].id]}))};
  const painted=[],ctx={measureText:text=>({width:[...text].length*40}),fillRect(){},strokeRect(){},fillText(text,x,y){painted.push({text,y});}};
  const canvas={getContext:()=>ctx};renderManual(canvas,'名字'.repeat(20),manual,d.answer.claims);
  const footer=painted.find(p=>p.text.includes('本人核对'));
  assert.ok(painted.every(p=>p.y<canvas.height));assert.ok(painted.filter(p=>p!==footer&&!p.text.includes('github.com')).every(p=>p.y<footer.y-25));
});
test('heldout must be separate, confirmed, verbatim and absent from extraction material',async()=>{
  await assert.rejects(lockCase({...input,confirmed:false},d.sources));
  await assert.rejects(lockCase({...input,quote:'this quote was never in the source'},d.sources));
  const leaking=structuredClone(d.sources);leaking.sources[0].text+='\n'+input.quote.split('').join(' ');
  await assert.rejects(lockCase(input,leaking),/移除整段/);
  await assert.rejects(lockCase({...input,question:input.quote},d.sources),/透露答案/);
  await assert.rejects(lockCase({...input,a:input.quote},d.sources),/透露答案/);
  assert.ok(!makeRequest(d.sources,1600).includes(input.quote));
});
test('neither trial request exposes private answer or history; only personalized receives prompt',async()=>{
  const t=await makeTrial(heldout,bundle.portable);
  for(const m of Object.values(t.modes))for(const secret of ['SECRET_HISTORY','SECRET_REASON',input.quote])assert.ok(!m.request.includes(secret));
  assert.ok(t.modes.personalized.request.includes(bundle.portable.text));assert.ok(!t.modes.baseline.request.includes(bundle.portable.text));
  const other=await lockCase({...input,actual:'B',reason:'OTHER_SECRET'},d.sources);
  assert.deepEqual((await makeTrial(other,bundle.portable)).modes,t.modes,'changing hidden answer cannot influence predictions');
  const changed=await makeBundle(d.answer,d.sources,d.answer.prompt+' 新条件。');
  const next=await makeTrial(heldout,changed.portable);
  assert.equal(t.modes.baseline.id,next.modes.baseline.id);assert.notEqual(t.modes.personalized.id,next.modes.personalized.id);
  assert.throws(()=>prediction(JSON.stringify(p(t.modes.personalized.id)),next.modes.personalized.id));
});
test('reveal binds both predictions, permits abstention, and does not manufacture accuracy',async()=>{
  const t=await makeTrial(heldout,bundle.portable),baseline=prediction(JSON.stringify(p(t.modes.baseline.id)),t.modes.baseline.id),personalized=p(t.modes.personalized.id,'A');
  const result=assess(heldout,t,baseline,personalized);assert.equal(result.baseline.match,false);assert.equal(result.personalized.match,true);assert.ok(result.note.includes('不是准确率'));
  assert.throws(()=>assess(heldout,t,personalized,baseline));assert.throws(()=>assess(heldout,t,{...baseline,choice:'C'},personalized));
  assert.throws(()=>prediction(JSON.stringify({...baseline,score:1}),t.modes.baseline.id));
  const puzzle=puzzleText(heldout),reveal=revealText(heldout,result);
  assert.ok(!puzzle.includes(input.reason));assert.ok(reveal.includes(input.reason));
  for(const s of [puzzle,reveal])for(const secret of ['SECRET_HISTORY',input.quote])assert.ok(!s.includes(secret));
  assert.ok(assess(heldout,{...t,retest:true},baseline,personalized).note.includes('复测'));
  const demo=await lockCase(input,d.sources,true),dt=await makeTrial(demo,bundle.portable);assert.ok(assess(demo,dt,p(dt.modes.baseline.id),p(dt.modes.personalized.id)).note.includes('虚构演示'));
});
