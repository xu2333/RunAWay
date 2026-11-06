import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,readFileSync as read,statSync,mkdirSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {makeTrialSnapshot,makeTrialRecord,publicTrialSummary} from '../web/dist/choice-feedback.mjs';
import {analyzeFeedback,parseFeedbackJSON,digest,IntakeError} from '../scripts/feedback_intake_core.mjs';

const contract=JSON.parse(readFileSync(new URL('../web/dist/choice-contract.json',import.meta.url),'utf8'));
const cli=fileURLToPath(new URL('../scripts/choice_feedback.mjs',import.meta.url));
const material='SECRET_MEMORY：证据不足时暂停。';
const queries=[{id:'q1',scenario:'SECRET_TASK',options:{A:'SECRET_OPTION_A',B:'SECRET_OPTION_B'}}];
function record(index=0,options={},raw='{"q1":"SECRET_OPTION_A"}',feedback={rating:'fits',correction:'SECRET_CORRECTION'}) {
  const createdAt=new Date(Date.UTC(2026,10,6,12,index)).toISOString();
  const importedAt=new Date(Date.UTC(2026,10,6,13,index)).toISOString();
  const snapshot=makeTrialSnapshot(contract,material,queries,{createdAt,referenceLabel:'A',...options});
  return makeTrialRecord(contract,snapshot,raw,feedback,importedAt);
}
const analyze=values=>analyzeFeedback(values.map((value,file_index)=>({file_index,value})),contract);
const invoke=(inputs,out)=>spawnSync(process.execPath,[cli,'summarize',...inputs.flatMap(p=>['--input',p]),'--out',out],{encoding:'utf8',timeout:10000});
function temporary(fn) {
  const dir=mkdtempSync(join(tmpdir(),'runaway-intake-'));
  try {return fn(dir);}finally {rmSync(dir,{recursive:true,force:true});}
}

test('mixed feedback retains file denominators and mutually exclusive local-event partitions',()=>{
  const demo=record(0,{synthetic:true}),post=record(1,{referenceAfterPrediction:true});
  const none=record(2,{referenceLabel:''}),match=record(3);
  const disagreement=record(4,{},'{"q1":"SECRET_OPTION_B"}'),unknown=record(5,{},'{"q1":"U"}');
  const published=publicTrialSummary(contract,match);
  const {summary,review}=analyze([demo,post,none,match,disagreement,unknown,match,published,published,{bad:true}]);
  assert.deepEqual(summary.totals,{input_files:10,valid_private_files:7,valid_public_summary_files:2,rejected_files:1});
  assert.equal(summary.private_local_events.distinct,6);
  assert.equal(summary.private_local_events.exact_duplicate_extra_files,1);
  assert.deepEqual(summary.private_local_events.partitions,{ready_for_manual_review:3,excluded_conflicting_versions:0,
    excluded_demo:1,excluded_no_reference:1,excluded_post_prediction:1});
  assert.deepEqual(summary.private_local_events.manual_review_outcomes,{matched_declared_choice:1,
    choice_disagreement:1,returned_unknown_requires_source_review:1});
  assert.equal(summary.public_summary_files.content_groups,1);
  assert.equal(summary.public_summary_files.identical_content_extra_files,1);
  assert.equal(summary.public_summary_files.not_deduplicated_as_people_or_cases,true);
  assert.equal(review.files.length,10);assert.equal(review.events.length,6);
  assert.equal(summary.unique_participants_verified,false);
  assert.equal(summary.independent_fidelity_verified,false);
  assert.equal(summary.model_calls_by_intake,0);
});

test('canonical records deduplicate independently of formatting or filename',()=>{
  const original=record(),reversed=Object.fromEntries(Object.entries(original).reverse());
  const parsed=parseFeedbackJSON(JSON.stringify(reversed,null,4));
  assert.equal(digest(original),digest(parsed));
  const {summary,review}=analyze([original,parsed]);
  assert.equal(summary.private_local_events.distinct,1);
  assert.equal(summary.private_local_events.exact_duplicate_extra_files,1);
  assert.deepEqual(review.events[0].file_indexes,[0,1]);
});

test('edited feedback is one event with explicit versions, never a best or latest rating',()=>{
  const original=record(),edited=record(0,{},'{"q1":"SECRET_OPTION_A"}',{rating:'misses',correction:''});
  const {summary,review}=analyze([original,edited,original]);
  assert.equal(summary.private_local_events.distinct,1);
  assert.equal(summary.private_local_events.feedback_revision_events,1);
  assert.equal(summary.private_local_events.exact_duplicate_extra_files,1);
  assert.equal(review.events[0].rating,'multiple_versions');
  assert.equal(review.events[0].unique_record_versions,2);
  assert.equal(review.events[0].correction_provided,true);
});

test('conflicting reference or origin excludes all versions without silently picking a gold',()=>{
  for(const changed of [record(0,{referenceLabel:'B'}),record(0,{synthetic:true}),
    record(0,{referenceAfterPrediction:true})]) {
    const {summary,review}=analyze([record(),changed]);
    assert.equal(summary.private_local_events.distinct,1);
    assert.equal(summary.private_local_events.partitions.excluded_conflicting_versions,1);
    assert.equal(summary.private_local_events.partitions.ready_for_manual_review,0);
    assert.equal(review.events[0].reference_or_origin_variants,2);
    assert.equal(review.events[0].review_reason,null);
  }
});

test('private and public validation rejects tampering instead of upgrading old records',()=>{
  const privateBad=structuredClone(record());privateBad.metrics.declared_choice_match=false;
  const publicBad={...publicTrialSummary(contract,record()),independent_fidelity_verified:true};
  const freeText={...publicTrialSummary(contract,record()),note:'SECRET_LEAK'};
  const old={...record(),schema_version:1};
  const {summary,review}=analyze([privateBad,publicBad,freeText,old]);
  assert.equal(summary.totals.rejected_files,4);
  assert.deepEqual(summary.rejections,{invalid_record:3,unsupported_record:1});
  assert.deepEqual(review.events,[]);
  assert.doesNotMatch(JSON.stringify(summary),/SECRET_|event_id|record_sha256|selected_files/);
});

test('strict JSON rejects duplicate decoded keys, damaged Unicode and malformed numbers',()=>{
  for(const text of ['{"a":1,"a":2}','{"x":{"a":1,"\\u0061":2}}','[1,]',
    '{"a":1,}','{"a":NaN}','1e309','01','true false','"\\ud800"','"\\ufffd"',
    '['.repeat(66)+'0'+']'.repeat(66)])assert.throws(()=>parseFeedbackJSON(text),IntakeError,text);
  const valid=parseFeedbackJSON('{"__proto__":{"x":1},"unicode":"青蛙🐸","n":-1.25e2}');
  assert.equal(Object.getPrototypeOf(valid),null);
  assert.equal(valid.unicode,'青蛙🐸');assert.equal(valid.n,-125);
  assert.equal({}.x,undefined);
  assert.throws(()=>analyzeFeedback([null],contract),IntakeError);
});

test('public summaries are file counts even when different files have identical content',()=>{
  const published=publicTrialSummary(contract,record());
  const {summary}=analyze([published,published]);
  assert.equal(summary.private_local_events.distinct,0);
  assert.equal(summary.private_local_events.partitions.ready_for_manual_review,0);
  assert.equal(summary.public_summary_files.counts.rating.fits,2);
  assert.equal(summary.public_summary_files.counts.declared_choice_match.true,2);
  assert.equal(summary.counts_are_files_and_local_events_not_people,true);
  assert.equal(summary.network_requests_by_intake,0);
});

test('CLI produces private pointers and a text-free summary without changing selected files',()=>temporary(dir=>{
  const input=join(dir,'SECRET_FILENAME.json'),out=join(dir,'review');
  const original=JSON.stringify(record());writeFileSync(input,original);
  const result=invoke([input,input],out);assert.equal(result.status,0,result.stderr);
  const summary=JSON.parse(result.stdout),review=JSON.parse(read(join(out,'review.private.json'),'utf8'));
  assert.equal(summary.private_local_events.distinct,1);
  assert.equal(summary.private_local_events.exact_duplicate_extra_files,1);
  assert.doesNotMatch(result.stdout,/SECRET_|runaway-intake-|event_id|record_sha256/);
  assert.deepEqual(review.selected_files,[{file_index:0,path:input},{file_index:1,path:input}]);
  assert.doesNotMatch(JSON.stringify(review),/SECRET_MEMORY|SECRET_TASK|SECRET_CORRECTION/);
  assert.equal(read(input,'utf8'),original);
  if(process.platform!=='win32') {
    assert.equal(statSync(out).mode&0o777,0o700);
    for(const file of ['summary.json','review.private.json'])assert.equal(statSync(join(out,file)).mode&0o777,0o600);
  }
}));

test('CLI rejection reports preserve denominator and never print content or selected paths',()=>temporary(dir=>{
  const valid=join(dir,'valid.json'),broken=join(dir,'SECRET_BROKEN.json');
  const duplicate=join(dir,'duplicate.json'),large=join(dir,'large.json'),missing=join(dir,'missing');
  writeFileSync(valid,JSON.stringify(record()));writeFileSync(broken,Buffer.from([0xff,0xfe]));
  writeFileSync(duplicate,'{"kind":"a","kind":"b"}');writeFileSync(large,' '.repeat(2000001));
  const result=invoke([valid,broken,duplicate,large,missing,dir],join(dir,'report'));
  assert.equal(result.status,2,result.stderr);
  const summary=JSON.parse(result.stdout);
  assert.equal(summary.totals.input_files,6);assert.equal(summary.totals.rejected_files,5);
  assert.deepEqual(summary.rejections,{invalid_json:2,input_too_large:1,unreadable_input:1,not_regular_file:1});
  assert.equal(result.stderr,'');assert.doesNotMatch(result.stdout,/SECRET_|runaway-intake-/);
}));

test('CLI never overwrites an output directory or recursively discovers records',()=>temporary(dir=>{
  const input=join(dir,'input.json'),out=join(dir,'existing');
  writeFileSync(input,JSON.stringify(record()));mkdirSync(out);writeFileSync(join(out,'marker'),'KEEP');
  const result=invoke([input],out);assert.equal(result.status,2);
  assert.equal(JSON.parse(result.stderr).reason,'output_exists');
  assert.equal(read(join(out,'marker'),'utf8'),'KEEP');
  const directory=invoke([dir],join(dir,'new'));
  assert.equal(JSON.parse(directory.stdout).totals.valid_private_files,0);
  assert.equal(JSON.parse(directory.stdout).totals.rejected_files,1);
}));

test('CLI enforces a cumulative byte budget across individually acceptable files',()=>temporary(dir=>{
  const input=join(dir,'padding.json');writeFileSync(input,' '.repeat(1999998)+'{}');
  const result=invoke(Array(17).fill(input),join(dir,'budget-review'));
  assert.equal(result.status,2,result.stderr);
  const summary=JSON.parse(result.stdout);
  assert.equal(summary.totals.input_files,17);
  assert.equal(summary.totals.rejected_files,17);
  assert.deepEqual(summary.rejections,{unsupported_record:16,byte_budget_exhausted:1});
}));

test('CLI rejects a selected FIFO without blocking for a writer',()=>temporary(dir=>{
  if(process.platform==='win32')return;
  const fifo=join(dir,'pipe');const made=spawnSync('mkfifo',[fifo],{encoding:'utf8'});
  assert.equal(made.status,0,made.stderr);
  const result=invoke([fifo],join(dir,'pipe-review'));
  assert.equal(result.status,2,result.stderr);
  assert.deepEqual(JSON.parse(result.stdout).rejections,{not_regular_file:1});
}));
