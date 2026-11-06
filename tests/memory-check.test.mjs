import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdtempSync,rmSync,statSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {ARMS,buildCheck,verifyCheck,evaluateCheck} from '../scripts/memory_check_core.mjs';
import {canonical} from '../web/dist/core.mjs';
import {makeChoiceRequest} from '../web/dist/choice-core.mjs';
const contract=JSON.parse(readFileSync(new URL('../web/dist/choice-contract.json',import.meta.url),'utf8'));
const cli=fileURLToPath(new URL('../scripts/check_memory.mjs',import.meta.url));
const queries=Array.from({length:8},(_,i)=>({id:'q'+(i+1),scenario:'SECRET_TASK_'+i,
  options:{A:'SECRET_OPTION_A',B:'SECRET_OPTION_B'}}));
function value(changes={}) {return {schema_version:1,kind:'runaway_memory_check',
  source_text:'SECRET_FULL_SOURCE：用户：安全可撤销时才自动。助手：不要把我的建议当成用户认可。🐸',
  memory_text:'SECRET_CARD：可撤销时自动。',queries,
  reference:{q1:'A',q2:'A',q3:'A',q4:'A',q5:'U',q6:'U',q7:'A',q8:'B'},reader_mode:'standard',...changes};}
const packet=(changes={})=>({...buildCheck(contract,value(changes)),dependencies:{}});
function answer(labels) {return {raw:JSON.stringify(Object.fromEntries(queries.map((q,i)=>
  [q.id,labels[i]==='U'?'U':q.options[labels[i]]])))};}
const complete=()=>({
  full:answer(['A','A','A','A','U','U','B','B']),
  card:answer(['A','A','U','B','U','A','A','B']),
  none:answer(['B','A','U','U','U','U','A','A'])});
const invoke=args=>spawnSync(process.execPath,[cli,...args],{encoding:'utf8',timeout:10000});
function temporary(fn) {const dir=mkdtempSync(join(tmpdir(),'runaway-check-'));try{return fn(dir);}finally{rmSync(dir,{recursive:true,force:true});}}
function prepare(dir,reference=true) {
  const input=value(),files={source:input.source_text,memory:input.memory_text,questions:JSON.stringify(input.queries)};
  if(reference)files.reference=JSON.stringify(input.reference);
  const args=['prepare'];
  for(const [name,contents]of Object.entries(files)) {
    const path=join(dir,name+'.txt');writeFileSync(path,contents);args.push('--'+name,path);
  }
  const out=join(dir,'prepared');args.push('--out',out);
  const result=invoke(args);assert.equal(result.status,0,result.stderr);return out;
}

test('three requests change only material and exclude declared answers from all arms',()=>{
  for(const reader_mode of ['standard','coverage']) {
    const p=packet({reader_mode});
    for(const arm of ARMS) {
      const payload=JSON.parse(p.requests[arm].prompt.split('\nREADER_INPUT_JSON:\n')[1]);
      assert.deepEqual(Object.keys(payload).sort(),['material','queries']);
      assert.deepEqual(payload.queries,queries);
      assert.equal(payload.material,arm==='full'?p.case.source_text:arm==='card'?p.case.memory_text:'');
      assert.deepEqual(p.requests[arm],makeChoiceRequest(contract,payload.material,queries,'text',reader_mode));
    }
    assert.equal(canonical(p.requests.full.schema),canonical(p.requests.card.schema));
    assert.equal(canonical(p.requests.none.schema),canonical(p.requests.card.schema));
    const changed=packet({reader_mode,reference:Object.fromEntries(queries.map(q=>[q.id,'B']))});
    assert.equal(canonical(p.requests),canonical(changed.requests));
    assert.notEqual(p.case_sha256,changed.case_sha256);
  }
});

test('complete matrix separates retained choices, source-control failure and two kinds of unknown loss',()=>{
  const {summary,review}=evaluateCheck(contract,packet(),complete());
  assert.equal(summary.cases,8);
  assert.deepEqual(summary.partition,{incomplete_response_set:0,unscored_no_reference:0,
    source_control_disagrees_with_reference:1,unknown_retained:1,
    choice_retained_no_increment_over_no_memory:1,choice_retained_with_no_memory_difference:2,
    card_choice_where_reference_and_source_unknown:1,card_unknown_where_source_matches_choice:1,
    card_different_choice_where_source_matches:1});
  assert.equal(review.cases[6].disposition,'source_control_disagrees_with_reference');
  assert.equal(review.cases[6].answers.card,'A');
  assert.equal(summary.by_arm.full.declared_matches,7);
  assert.equal(summary.by_arm.card.unknown_answers,2);
  assert.equal(Object.values(summary.partition).reduce((a,b)=>a+b),8);
});

test('missing response stays missing for every question, never becomes unknown or a smaller denominator',()=>{
  const responses=complete();delete responses.none;
  const {summary,review}=evaluateCheck(contract,packet(),responses);
  assert.equal(summary.partition.incomplete_response_set,8);
  assert.equal(summary.by_arm.none.missing_or_invalid_answers,8);
  assert.equal(summary.by_arm.none.unknown_answers,0);
  assert.equal(review.arms.none.status,'not_provided');
  assert.equal(review.cases[0].answers.none,null);
  assert.equal(summary.by_arm.card.valid_answers,8);
});

test('invalid, duplicate-key and partial answers reject their entire arm without repair',()=>{
  for(const raw of ['{"q1":"U","q\\u0031":"U"}','{"q1":"U"}',
    answer(['A','A','A','A','U','U','B','B']).raw.replace('SECRET_OPTION_A','A'),'{"q1":42}']) {
    const responses={...complete(),card:{raw}};
    const {summary,review}=evaluateCheck(contract,packet(),responses);
    assert.equal(review.arms.card.status,'invalid');
    assert.equal(summary.partition.incomplete_response_set,8);
    assert.equal(summary.by_arm.card.missing_or_invalid_answers,8);
    assert.equal(summary.by_arm.card.unknown_answers,0);
  }
});

test('without a reference predictions remain unscored, even when both source and card agree',()=>{
  const {summary}=evaluateCheck(contract,packet({reference:null}),complete());
  assert.equal(summary.partition.unscored_no_reference,8);
  assert.equal(summary.reference_provided,false);
  for(const arm of ARMS){assert.equal(summary.by_arm[arm].unscored_answers,8);assert.equal(summary.by_arm[arm].declared_matches,0);}
});

test('invalid cases and references fail before preparing requests',()=>{
  for(const changes of [{source_text:''},{memory_text:'\ufffd'},{reader_mode:'guess'},
    {reference:{q1:'A'}},{reference:{...value().reference,q1:'C'}},
    {queries:[]},{queries:Array(33).fill(queries[0])},{queries:[{...queries[0],options:{A:'U',B:'other'}}]}])
    assert.throws(()=>packet(changes));
});

test('packet changes cannot silently relabel a result as a new source or request',()=>{
  const p=packet();assert.doesNotThrow(()=>verifyCheck(contract,p));
  for(const change of [x=>x.requests.card.prompt+='edited',x=>x.case.memory_text+='edited',
    x=>x.case.reference.q1='B',x=>x.case_sha256='0'.repeat(64),x=>x.extra='PRIVATE']) {
    const damaged=structuredClone(p);change(damaged);assert.throws(()=>verifyCheck(contract,damaged));
  }
});

test('aggregate is text-free and makes no independence, identity or upstream-binding claim',()=>{
  const {summary,review}=evaluateCheck(contract,packet(),complete());
  assert.doesNotMatch(JSON.stringify(summary),/SECRET_|case_sha256|q1|raw|source_text|memory_text/);
  assert.match(JSON.stringify(review),/SECRET_OPTION_A/);
  for(const key of ['reference_timing_verified','source_sufficiency_verified','heldout_independence_verified',
    'model_identity_verified','response_request_binding_verified','independent_fidelity_verified'])assert.equal(summary[key],false);
  assert.equal(summary.model_calls_by_check,0);assert.equal(summary.network_requests_by_check,0);
  assert.equal(summary.material_characters.full,[...value().source_text].length);
});

test('CLI prepares private requests and imports three manual responses end to end',()=>temporary(dir=>{
  const prepared=prepare(dir),args=['import','--prepared',prepared];
  for(const [arm,response]of Object.entries(complete())) {
    const path=join(dir,arm+'.json');writeFileSync(path,response.raw);args.push('--'+arm+'-answer',path);
  }
  const out=join(dir,'result');args.push('--out',out);const result=invoke(args);
  assert.equal(result.status,0,result.stderr);
  assert.equal(JSON.parse(result.stdout).partition.card_unknown_where_source_matches_choice,1);
  assert.doesNotMatch(result.stdout,/SECRET_|runaway-check-/);
  const saved=JSON.parse(readFileSync(join(out,'review.private.json'),'utf8'));
  assert.equal(saved.arms.full.status,'valid');
  if(process.platform!=='win32') {
    assert.equal(statSync(prepared).mode&0o777,0o700);assert.equal(statSync(out).mode&0o777,0o700);
    for(const path of [join(prepared,'prepared.private.json'),join(prepared,'full.request.private.md'),
      join(out,'review.private.json'),join(out,'summary.json')])assert.equal(statSync(path).mode&0o777,0o600);
  }
}));

test('CLI leaves a report and nonzero exit for missing or invalid responses',()=>temporary(dir=>{
  const prepared=prepare(dir),answerFile=join(dir,'bad.json');writeFileSync(answerFile,'{"q1":"U"}');
  const result=invoke(['import','--prepared',prepared,'--card-answer',answerFile,
    '--full-answer',join(dir,'MISSING_SECRET'),'--out',join(dir,'partial')]);
  assert.equal(result.status,2,result.stderr);assert.equal(result.stderr,'');
  const summary=JSON.parse(result.stdout);
  assert.equal(summary.partition.incomplete_response_set,8);
  assert.equal(summary.by_arm.full.status,'invalid');assert.equal(summary.by_arm.none.status,'not_provided');
  assert.doesNotMatch(result.stdout,/SECRET_|runaway-check-/);
}));

test('CLI rejects changed manual packets, compiler fingerprints and symlinked preparations',()=>temporary(dir=>{
  const prepared=prepare(dir),answerFile=join(dir,'response.json');writeFileSync(answerFile,complete().card.raw);
  const run=out=>invoke(['import','--prepared',prepared,'--card-answer',answerFile,'--out',join(dir,out)]);
  const markdown=join(prepared,'full.request.private.md'),original=readFileSync(markdown,'utf8');
  writeFileSync(markdown,original+'EDIT');assert.equal(JSON.parse(run('changed').stderr).reason,'request_changed');
  writeFileSync(markdown,original);
  const manifest=join(prepared,'prepared.private.json'),saved=readFileSync(manifest,'utf8'),p=JSON.parse(saved);
  p.dependencies['web/dist/choice-core.mjs']='0'.repeat(64);writeFileSync(manifest,JSON.stringify(p));
  assert.equal(JSON.parse(run('compiler').stderr).reason,'compiler_changed');writeFileSync(manifest,saved);
  const linked=join(dir,'linked');symlinkSync(prepared,linked,'dir');
  const result=invoke(['import','--prepared',linked,'--card-answer',answerFile,'--out',join(dir,'symlink')]);
  assert.equal(JSON.parse(result.stderr).reason,'prepared_symlink');
}));

test('CLI rejects malformed selected inputs and protects an existing output',()=>temporary(dir=>{
  const prepared=prepare(dir,false),response=join(dir,'response.json');writeFileSync(response,complete().card.raw);
  const before=readFileSync(join(prepared,'prepared.private.json'),'utf8');
  const result=invoke(['import','--prepared',prepared,'--card-answer',response,'--out',prepared]);
  assert.equal(JSON.parse(result.stderr).reason,'output_exists');
  assert.equal(readFileSync(join(prepared,'prepared.private.json'),'utf8'),before);
  writeFileSync(join(dir,'questions.txt'),'[{"id":"q1","id":"q2"}]');
  const invalid=invoke(['prepare','--source',join(dir,'source.txt'),'--memory',join(dir,'memory.txt'),
    '--questions',join(dir,'questions.txt'),'--out',join(dir,'invalid')]);
  assert.equal(JSON.parse(invalid.stderr).reason,'invalid_json');
}));

test('selected UTF-8 text preserves BOM, role labels and line endings in the full request',()=>temporary(dir=>{
  const source='\ufeff用户：原话 🐸\r\n助手：建议不是背书。\r\n';
  const files={source,memory:'用户已说明的条件。',questions:JSON.stringify(queries)};
  const args=['prepare'];
  for(const [name,contents]of Object.entries(files)) {
    const path=join(dir,name);writeFileSync(path,contents);args.push('--'+name,path);
  }
  const out=join(dir,'unicode');args.push('--out',out);
  const result=invoke(args);assert.equal(result.status,0,result.stderr);
  const p=JSON.parse(readFileSync(join(out,'prepared.private.json'),'utf8'));
  assert.equal(p.case.source_text,source);
  const payload=JSON.parse(p.requests.full.prompt.split('\nREADER_INPUT_JSON:\n')[1]);
  assert.equal(payload.material,source);
}));
