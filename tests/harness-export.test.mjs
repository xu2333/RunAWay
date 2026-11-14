import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,mkdir,rm,symlink,readdir} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {adapters,makeExport,BOUNDARY,BEGIN,END,sha256} from '../packages/harnesses/index.mjs';
import {makeBundle,SOURCE_FILES} from '../packages/harnesses/bundle.mjs';
import {zipFiles} from '../packages/harnesses/zip.mjs';
import {install} from '../packages/harnesses/install.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const prompt=BOUNDARY+'在可撤销时自动执行；不可撤销或条件不明时先问。\n';
const sources={};for(const name of SOURCE_FILES)sources[name]=await readFile(new URL('../packages/harnesses/'+name,import.meta.url),'utf8');
async function temp(t){const dir=await mkdtemp(path.join(os.tmpdir(),'runaway-export-'));t.after(()=>rm(dir,{recursive:true,force:true}));return dir;}
async function fixture(t,target='codex',body=prompt){
  const dir=await temp(t),bundleDir=path.join(dir,'bundle'),project=path.join(dir,'project');
  await mkdir(bundleDir);await mkdir(project);
  const manifest=await makeExport(target,body);
  for(const f of manifest.files){await mkdir(path.dirname(path.join(bundleDir,f.path)),{recursive:true});await writeFile(path.join(bundleDir,f.path),f.content);}
  await writeFile(path.join(bundleDir,'runaway-export.json'),JSON.stringify(manifest));
  return {dir,bundleDir,project,manifest};
}
test('three isolated adapters preserve every Unicode prompt byte and count full envelopes',async()=>{
  assert.equal(adapters.length,3);assert.equal(new Set(adapters.map(a=>a.path)).size,3);
  for(const a of adapters){const m=await makeExport(a.id,prompt);const f=m.files[0];assert.equal(f.content,a.preamble+BEGIN+'\n'+prompt+END+'\n');assert.equal(m.prompt_sha256,await sha256(prompt));assert.equal(f.characters,[...f.content].length);assert.equal(f.bytes,Buffer.byteLength(f.content));assert.equal(m.runtime_load_verified,false);}
  assert.match((await makeExport('antigravity',prompt)).files[0].content,/^---\ntrigger: always_on\n/);
});
test('reject damaged, unbounded, empty and marker-bearing prompts without truncation',async()=>{
  for(const bad of ['hello',BOUNDARY,BOUNDARY+'x'.repeat(24001),BOUNDARY+'\ud800',BOUNDARY+BEGIN,BOUNDARY+'\x00'])await assert.rejects(makeExport('codex',bad));
  await assert.rejects(makeExport('unknown',prompt));
});
test('Python zipfile checks CRC and portable bundle contains only prompt and installer files',async t=>{
  const dir=await temp(t);const {bytes}=await makeBundle('antigravity',prompt,sources);const zip=path.join(dir,'export.zip');await writeFile(zip,bytes);
  const out=spawnSync('python3',['-c','import zipfile,json,sys\nz=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None\nprint(json.dumps({"names":z.namelist(),"rule":z.read(".agents/rules/runaway.md").decode()}))',zip],{encoding:'utf8'});
  assert.equal(out.status,0,out.stderr);const result=JSON.parse(out.stdout);
  assert.equal(result.names.length,9);assert.ok(result.rule.includes(prompt));assert.ok(!result.names.some(n=>/source|private|profile|history/.test(n)));
  await assert.rejects(makeBundle('codex',prompt,{}));
  assert.throws(()=>zipFiles([{name:'../escape',text:'x'}]));assert.throws(()=>zipFiles([{name:'x',text:'x'},{name:'x',text:'x'}]));
});
for(const target of ['codex','claude-code','antigravity'])test(target+': install, no-op, update and remove preserve project text',async t=>{
  const f=await fixture(t,target),adapter=adapters.find(a=>a.id===target),file=path.join(f.project,adapter.path);
  if(target==='codex')await writeFile(file,'# Existing instructions\nKeep meaningful tests.\n');
  const before=target==='codex'?await readFile(file,'utf8'):null;
  assert.equal((await install({...f,dryRun:true})).status,'planned');assert.equal(await readFile(file,'utf8').catch(()=>null),before);
  await install(f);const first=await readFile(file,'utf8');await install(f);assert.equal(await readFile(file,'utf8'),first);
  const m=await makeExport(target,prompt+'条件变化时重新确认。\n');await writeFile(path.join(f.bundleDir,'runaway-export.json'),JSON.stringify(m));await writeFile(path.join(f.bundleDir,adapter.path),m.files[0].content);
  await install(f);assert.match(await readFile(file,'utf8'),/条件变化时重新确认/);
  await install({...f,remove:true});assert.equal(await readFile(file,'utf8').catch(()=>null),before);
});
test('edits, existing dedicated files, shadowing and legacy blocks are refused',async t=>{
  const f=await fixture(t);await install(f);await writeFile(path.join(f.project,'AGENTS.md'),(await readFile(path.join(f.project,'AGENTS.md'),'utf8')).replace('可撤销','不可撤销'));
  await assert.rejects(install(f),/changed/);
  const g=await fixture(t,'antigravity');await mkdir(path.join(g.project,'.agents/rules'),{recursive:true});await writeFile(path.join(g.project,'.agents/rules/runaway.md'),'My rule');await assert.rejects(install(g),/already exists/);
  const h=await fixture(t);await writeFile(path.join(h.project,'AGENTS.override.md'),'shadow');await assert.rejects(install(h),/shadows/);
  const j=await fixture(t);await writeFile(path.join(j.project,'AGENTS.md'),BEGIN+'old'+END);await assert.rejects(install(j),/untracked/);
});
test('unsafe paths, checksum corruption, symlinks and exclusive lock cause zero managed writes',async t=>{
  const f=await fixture(t);const outside=path.join(f.dir,'outside');await mkdir(outside);await symlink(outside,path.join(f.project,'.runaway'),'dir');await assert.rejects(install(f),/symlink/);assert.deepEqual(await readdir(outside),[]);
  const g=await fixture(t);await mkdir(path.join(g.project,'.runaway'));await writeFile(path.join(g.project,'.runaway/harness-export.lock'),'busy');await assert.rejects(install(g));assert.deepEqual(await readdir(g.project),['.runaway']);
  const h=await fixture(t);h.manifest.files[0].path='../escape';await writeFile(path.join(h.bundleDir,'runaway-export.json'),JSON.stringify(h.manifest));await assert.rejects(install(h),/checksum or path/);
  const j=await fixture(t);await writeFile(path.join(j.bundleDir,'AGENTS.md'),'tamper');await assert.rejects(install(j),/checksum/);assert.deepEqual(await readdir(j.project),[]);
});
test('exported standalone installer runs outside repository with no installed RunAWay',async t=>{
  const dir=await temp(t),zip=path.join(dir,'bundle.zip'),unpacked=path.join(dir,'unpacked'),project=path.join(dir,'project');await mkdir(project);
  await writeFile(zip,(await makeBundle('antigravity',prompt,sources)).bytes);
  const unzip=spawnSync('python3',['-c','import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])',zip,unpacked],{encoding:'utf8'});assert.equal(unzip.status,0,unzip.stderr);
  const run=spawnSync(process.execPath,[path.join(unpacked,'install.mjs'),'--project',project],{cwd:dir,encoding:'utf8'});assert.equal(run.status,0,run.stderr);assert.equal(JSON.parse(run.stdout).status,'installed');
  const missing=spawnSync(process.execPath,[path.join(unpacked,'install.mjs')],{cwd:dir,encoding:'utf8'});assert.equal(missing.status,1);
});
