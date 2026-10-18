import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {createTemporal} from '../web/dist/temporal-core.mjs';
const protocol=JSON.parse(await readFile(new URL('../web/dist/temporal-protocol.json',import.meta.url)));
const demo=JSON.parse(await readFile(new URL('../web/dist/temporal-demo.json',import.meta.url)));
const engine=createTemporal(protocol);
const PY=`import json,sys
from runaway import temporal as t
v=json.load(sys.stdin)
try:
 a=v.get('artifact');op=v['op']
 if op=='spans':r=t.spans(v['sources'])
 elif op=='request':r=t.make_request(v['sources'])
 elif op=='bind':r=t.bind(v['answer'],v['sources'])
 elif op=='resolve':r=t.resolve(a,v['domain'],v['context'],v.get('through'))
 elif op=='render':r=t.render(a,v['budget'],v.get('domains'))
 elif op=='fixture':
  import runpy
  s,answer=runpy.run_path('tests/test_temporal.py',run_name='fixture_only')['fixture']()
  r={'sources':s,'answer':answer}
 else:raise ValueError('Unknown operation')
 print(json.dumps({'value':r},ensure_ascii=False))
except (ValueError,KeyError,TypeError) as e:print(json.dumps({'error':str(e)}))
`;
function python(value){
 const r=spawnSync(process.env.PYTHON??'python3',['-B','-c',PY],{input:JSON.stringify(value),encoding:'utf8',env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'}});
 assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout);
}
const sources=text=>({schema_version:1,sources:[{id:'s',episode_id:'e',role:'user',text}]});

test('browser and CLI bind the actual diagnostic extractions to identical artifacts and requests',async()=>{
 for(const c of demo.cases){
  assert.equal(await engine.makeRequest(c.sources),python({op:'request',sources:c.sources}).value);
  const a=await engine.bind(c.answer,c.sources);
  assert.deepEqual(a,python({op:'bind',sources:c.sources,answer:c.answer}).value);
  assert.deepEqual(await engine.render(a,768),python({op:'render',artifact:a,budget:768}).value);
  assert.equal((await engine.render(a,768)).text,c.prompt);
  for(const x of [false,true])for(const y of [false,true]){
   const context={'方向尚未验证':x,'改动不可撤销':y};
   assert.deepEqual(await engine.resolve(a,'产品验证',context),python({op:'resolve',artifact:a,domain:'产品验证',context}).value);
  }
  for(const through of ['r16','r17','r18']){
   const context={'方向尚未验证':true,'改动不可撤销':true};
   assert.deepEqual(await engine.resolve(a,'产品验证',context,through),python({op:'resolve',artifact:a,domain:'产品验证',context,through}).value);
  }
 }
});

test('source offsets and hashes use codepoints across CRLF, Unicode line separators and emoji',async()=>{
 for(const raw of ['操作🐈：不可撤销时确认。\r\n撤销前条。\n','alpha\u0085beta\u2028🐈\u2029end','\ufeff前言\n\n尾行']){
  const s=sources(raw);assert.deepEqual(await engine.spans(s),python({op:'spans',sources:s}).value);
 }
});

test('replacement, clear restoration, weak evidence and missing context agree with hand-checked CLI semantics',async()=>{
 const f=python({op:'fixture'}).value,a=await engine.bind(f.answer,f.sources);
 for(const [domain,context,through] of [['文件标记',{},'e9'],['文件标记',{},'e10'],['产品验证',{'方向未验证':false,'改动不可撤销':false},null],['产品验证',{'方向未验证':true},null],['产品验证',{'方向未验证':true,'改动不可撤销':true},'e5'],['产品验证',{'方向未验证':true,'改动不可撤销':true},'e6']]){
  assert.deepEqual(await engine.resolve(a,domain,context,through),python({op:'resolve',artifact:a,domain,context,through}).value);
 }
});

test('numeric and prototype-like domain labels keep source order and cannot alter object prototypes',async()=>{
 const s=sources('10：选一。\n2：选二。\n__proto__：安全时选三。'),spans=await engine.spans(s);
 const event=(id,domain,action,i,condition=[])=>({id,kind:condition.length?'constraint':'regular',domain,action,strength:0,when_all:condition,target:'',span_ids:[spans[i].id]});
 const answer={scope:'合成开发。',events:[event('a','10','选一',0),event('b','2','选二',1),event('c','__proto__','选三',2,[{predicate:'安全',equals:true}])],unmodeled:[]};
 const a=await engine.bind(answer,s),full=await engine.render(a,1000),partial=await engine.render(a,1000,['2']);
 assert.deepEqual(full.included_domains,['10','2','__proto__']);
 assert.deepEqual(full,python({op:'render',artifact:a,budget:1000}).value);
 assert.deepEqual(partial,python({op:'render',artifact:a,budget:1000,domains:['2']}).value);
 assert.deepEqual(partial.omitted_domains,['10','__proto__']);
 assert.equal((await engine.resolve(a,'__proto__',{'安全':true})).action,'选三');assert.equal({}.action,undefined);
});

test('budget failure withholds text and neither truncates nor chooses domains automatically',async()=>{
 const c=demo.cases[0],a=await engine.bind(c.answer,c.sources),r=await engine.render(a,100);
 assert.equal(r.status,'budget_blocked');assert.equal(r.text,null);assert.equal(r.required_characters,183);
 assert.deepEqual(r,python({op:'render',artifact:a,budget:100}).value);
 await assert.rejects(engine.render(a,1000,null,null,128));
 assert.equal((await engine.render(a,1000,null,()=>385,384)).text,null);
});

test('bad graphs, misquoted phrases, unsupported spans and damaged text fail in both runtimes',async()=>{
 const c=demo.cases[0];
 for(const kind of ['forward','phrase','span','extra','damaged']){
  const answer=structuredClone(c.answer);
  if(kind==='forward')answer.events[5].target='r18';
  if(kind==='phrase')answer.events[0].action='没有记录的偏好';
  if(kind==='span')answer.events[0].span_ids=['invented'];
  if(kind==='extra')answer.events[0].quote='rewritten';
  if(kind==='damaged')answer.scope='\ud800';
  await assert.rejects(engine.bind(answer,c.sources));assert.ok(python({op:'bind',answer,sources:c.sources}).error);
 }
 const source=sources('<heartbeat>自动运行任务</heartbeat>');
 await assert.rejects(engine.spans(source));assert.ok(python({op:'spans',sources:source}).error);
});
