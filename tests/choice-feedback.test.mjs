import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {makeChoiceRequest} from '../web/dist/choice-core.mjs';
import {makeTrialSnapshot,makeTrialRecord,publicTrialSummary,publicTrialIssueUrl} from '../web/dist/choice-feedback.mjs';

const contract=JSON.parse(readFileSync(new URL('../web/dist/choice-contract.json',import.meta.url),'utf8'));
const material='SECRET_MEMORY：在这个条件下先试。';
const queries=[{id:'q1',scenario:'SECRET_TASK：这次怎么选？',options:{A:'SECRET_OPTION_A',B:'SECRET_OPTION_B'}}];
const at='2026-11-06T12:00:00.000Z', later='2026-11-06T12:01:00.000Z';
const snapshot=(options={})=>makeTrialSnapshot(contract,material,queries,{createdAt:at,...options});
const record=(s=snapshot({referenceLabel:'A'}),raw='{"q1":"SECRET_OPTION_A"}')=>
  makeTrialRecord(contract,s,raw,{rating:'fits',correction:'SECRET_CORRECTION'},later);

test('local reference and timing never alter the exact model request',()=>{
  for(const readerMode of ['standard','coverage']) {
    const expected=makeChoiceRequest(contract,material,queries,'text',readerMode);
    for(const referenceLabel of ['', 'A','B'])for(const referenceAfterPrediction of [false,true]) {
      const s=snapshot({readerMode,referenceLabel,referenceAfterPrediction});
      assert.deepEqual(s.request,expected);
      const payload=JSON.parse(s.request.prompt.split('\nREADER_INPUT_JSON:\n')[1]);
      assert.deepEqual(Object.keys(payload).sort(),['material','queries']);
      assert.doesNotMatch(s.request.prompt,/reference_recorded|reference_timing|declared_choice_match/);
    }
  }
});

test('recorded timing is preserved and a declared match is only a self-report',()=>{
  const before=record(), after=record(snapshot({referenceLabel:'A',referenceAfterPrediction:true,referenceAt:later}));
  assert.equal(before.reference.timing,'before_prediction_in_session');
  assert.equal(after.reference.timing,'after_prediction_in_session');
  assert.equal(before.metrics.declared_choice_match,true);
  assert.equal(after.metrics.declared_choice_match,true);
  assert.equal(after.independent_fidelity_verified,false);
  assert.equal(after.model_calls_by_app,0);
});

test('unknown and absent reference remain distinct from an omitted model answer',()=>{
  const unknown=record(snapshot({referenceLabel:'A'}),'{"q1":"U"}');
  assert.equal(unknown.metrics.model_returned_unknown,true);
  assert.equal(unknown.metrics.declared_choice_match,false);
  const unscored=record(snapshot(),'{"q1":"U"}');
  assert.equal(unscored.reference.timing,'not_recorded');
  assert.equal(unscored.metrics.declared_choice_match,null);
  assert.throws(()=>record(snapshot(),'{}'));
});

test('public summary and issue draft contain no prompt,task,options,reference or correction text',()=>{
  const privateRecord=record();
  assert.match(JSON.stringify(privateRecord),/SECRET_MEMORY/);
  assert.match(JSON.stringify(privateRecord),/SECRET_CORRECTION/);
  const summary=publicTrialSummary(contract,privateRecord);
  const url=new URL(publicTrialIssueUrl(summary));
  assert.equal(url.origin,'https://github.com');
  assert.equal(url.pathname,'/xu2333/RunAWay/issues/new');
  assert.doesNotMatch(JSON.stringify(summary)+url.searchParams.get('body'),/SECRET_/);
  assert.equal(summary.includes_prompt_or_task_text,false);
  assert.equal(summary.includes_free_text,false);
  assert.equal(summary.model_identity_verified,false);
});

test('synthetic origin remains explicit while ordinary uploads are only unverified',()=>{
  const demo=publicTrialSummary(contract,record(snapshot({synthetic:true,referenceLabel:'A'})));
  assert.equal(demo.origin,'demo_or_edited_demo');
  const supplied=publicTrialSummary(contract,record());
  assert.equal(supplied.origin,'user_supplied_unverified');
  assert.equal(supplied.independent_fidelity_verified,false);
  assert.throws(()=>snapshot({synthetic:'real'}));
});

test('changed request,local reference,prediction or metrics cannot become a summary',()=>{
  for(const fault of ['request','reference','decoded','metrics']) {
    const r=structuredClone(record());
    if(fault==='request')r.request.prompt+='changed';
    if(fault==='reference')r.reference.text='changed';
    if(fault==='decoded')r.prediction.decoded.q1.text='changed';
    if(fault==='metrics')r.metrics.declared_choice_match=false;
    assert.throws(()=>publicTrialSummary(contract,r),fault);
  }
});

test('public issue builder rejects arbitrary free text and unsupported validation claims',()=>{
  for(const field of ['correction','prompt','token']) {
    const summary={...publicTrialSummary(contract,record()),[field]:'PRIVATE_SECRET'};
    assert.throws(()=>publicTrialIssueUrl(summary));
  }
  for(const field of ['includes_prompt_or_task_text','includes_free_text','model_identity_verified','independent_fidelity_verified']) {
    const summary={...publicTrialSummary(contract,record()),[field]:true};
    assert.throws(()=>publicTrialIssueUrl(summary));
  }
});

test('bad labels,timestamps,ratings and damaged correction text fail explicitly',()=>{
  for(const options of [{referenceLabel:'U'},{referenceLabel:'C'},{referenceAfterPrediction:1},
    {createdAt:'not a date'},{referenceLabel:'A',referenceAt:'not a date'}]) assert.throws(()=>snapshot(options));
  assert.throws(()=>makeTrialRecord(contract,snapshot(),'{"q1":"U"}',{rating:'verified',correction:''},later));
  assert.throws(()=>makeTrialRecord(contract,snapshot(),'{"q1":"U"}',{rating:'fits',correction:'\ufffd'},later));
});

test('summary reference and unknown combinations stay internally consistent',()=>{
  const valid=publicTrialSummary(contract,record());
  for(const change of [{reference_recorded:false},{reference_timing:'not_recorded'},
    {declared_choice_match:null},{model_returned_unknown:true},{origin:'verified_real_user'},
    {reader_mode:'hidden_gold'},{model_calls_by_app:1}]) assert.throws(()=>publicTrialIssueUrl({...valid,...change}));
  const none=publicTrialSummary(contract,record(snapshot(),'{"q1":"U"}'));
  assert.doesNotThrow(()=>publicTrialIssueUrl(none));
});
