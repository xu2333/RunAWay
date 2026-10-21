import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {makeChoiceRequest,decodeChoiceResponse,parseChoiceAnswer} from '../web/dist/choice-core.mjs';
const contract=JSON.parse(readFileSync(new URL('../web/dist/choice-contract.json',import.meta.url),'utf8'));
const queries=[{id:'q1',scenario:'同一处岔路 🌱',options:{A:'先试一小步',B:'先理清结构',C:'先问两个人'}}, {id:'q2',scenario:'同一处岔路 🌱',options:{A:'先问两个人',B:'先试一小步',C:'先理清结构'}}];

test('browser requests match the Python reader byte for byte in both modes',()=>{
  for (const mode of ['label','text']) for (const readerMode of ['standard','coverage']) {
    const input={material:'未知时请停下。\n“新条件”需要重新判断。',queries,mode,readerMode};
    const py=spawnSync('python3',['-B','-c','import json,sys;from runaway.choice_reader import make_request;x=json.load(sys.stdin);print(json.dumps(make_request(x["material"],x["queries"],answer_format=x["mode"],reader_mode=x["readerMode"]),ensure_ascii=False))'],{input:JSON.stringify(input),encoding:'utf8'});
    assert.equal(py.status,0,py.stderr);
    const actual=makeChoiceRequest(contract,input.material,queries,mode,readerMode), expected=JSON.parse(py.stdout);
    assert.equal(actual.prompt,expected.prompt);
    assert.deepEqual(JSON.parse(JSON.stringify(actual.schema)),expected.schema);
  }
  const checked=spawnSync('python3',['-B','scripts/build_choice_contract.py','--check'],{encoding:'utf8'});
  assert.equal(checked.status,0,checked.stderr);
});

test('coverage mode leaves facts, options, schema and the standard default unchanged',()=>{
  const standard=makeChoiceRequest(contract,'记忆',queries);
  const explicit=makeChoiceRequest(contract,'记忆',queries,'text','standard');
  const coverage=makeChoiceRequest(contract,'记忆',queries,'text','coverage');
  assert.deepEqual(standard,explicit);
  assert.deepEqual(coverage.schema,standard.schema);
  assert.equal(coverage.prompt.split('\nREADER_INPUT_JSON:\n')[1],standard.prompt.split('\nREADER_INPUT_JSON:\n')[1]);
  assert.equal(contract.default_reader_mode,'standard');
  assert.throws(()=>makeChoiceRequest(contract,'记忆',queries,'text','guess'));
});

test('exact action text follows its public position; U stays unknown',()=>{
  const result=decodeChoiceResponse(queries,JSON.stringify({q1:'先试一小步',q2:'先试一小步'}));
  assert.equal(result.q1.label,'A');assert.equal(result.q2.label,'B');
  assert.equal(result.q1.text,result.q2.text);
  const unknown=decodeChoiceResponse(queries,'{"q1":"U","q2":"U"}');
  assert.equal(unknown.q1.unknown,true);assert.equal(unknown.q1.text,null);
});

test('strict response parsing rejects silent repairs, duplicate keys and missing answers',()=>{
  for (const raw of ['{"q1":"U","q1":"U"}','{"q1":"U","q\\u0031":"U"}','{"q1":NaN}','{"q1":42}','{"q1":"U",}','{"q1":"U"} trailing','{"q1":"broken\\x"}','{"q1":"U"', '["U"]']) assert.throws(()=>parseChoiceAnswer(raw),raw);
  for (const raw of ['{"q1":"先试一小步。","q2":"U"}','{"q1":"A","q2":"U"}','{"q1":" 先试一小步","q2":"U"}','{"q1":"U"}','{"q1":"U","q2":"U","extra":"U"}']) assert.throws(()=>decodeChoiceResponse(queries,raw),raw);
  assert.equal(parseChoiceAnswer('```json\n{"q1":"U"}\n```').q1,'U');
  assert.equal(parseChoiceAnswer('{"__proto__":"U"}').__proto__,'U');
});

test('ambiguous choices and damaged historical characters are rejected',()=>{
  for (const text of ['U','先试一小步']) {
    const q=structuredClone(queries);q[0].options.B=text;
    assert.throws(()=>makeChoiceRequest(contract,'记忆',q));
  }
  assert.throws(()=>makeChoiceRequest(contract,'损坏\ufffd',queries));
  assert.throws(()=>decodeChoiceResponse(queries,'{"q1":"\\ud800","q2":"U"}'));
});

test('trial page has local assets, no persistent storage or outgoing submission',()=>{
  const page=readFileSync(new URL('../web/dist/choices.html',import.meta.url),'utf8');
  const app=readFileSync(new URL('../web/dist/choices.mjs',import.meta.url),'utf8');
  assert.match(page,/connect-src 'self'/);
  assert.doesNotMatch(page,/(?:src|href)="https?:/);
  assert.doesNotMatch(app,/localStorage|sessionStorage|indexedDB|innerHTML|sendBeacon|https?:\/\//);
  assert.match(app,/independent_fidelity_verified:false/);
  assert.match(app,/model_calls_by_app:0/);
  const demo=JSON.parse(readFileSync(new URL('../web/dist/choice-demo.json',import.meta.url),'utf8'));
  assert.equal(demo.synthetic,true);
  makeChoiceRequest(contract,demo.material,demo.queries);
});
