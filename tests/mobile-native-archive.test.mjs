import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {Session} from '../apps/mobile/src/session.mjs';

test('native archive inspector compares actual file with the fixed demo and refuses changed prompt/origin',async t=>{
  const dir=await mkdtemp(path.join(os.tmpdir(),'runaway-native-archive-'));t.after(()=>rm(dir,{recursive:true,force:true}));
  const demo=JSON.parse(await readFile(new URL('../web/dist/demo.json',import.meta.url),'utf8'));
  const session=new Session();session.prepare(JSON.stringify(demo.sources),'trajectory',2400);session.importAnswer(JSON.stringify(demo.answer));session.origin='fictional_demo';
  const archive=path.join(dir,'saved.json'),report=path.join(dir,'report.json');const bytes=Buffer.from(JSON.stringify(session.archive())+'\n');await writeFile(archive,bytes);
  const script=fileURLToPath(new URL('../apps/mobile/check-native-archive.mjs',import.meta.url));
  function run(out){return spawnSync(process.execPath,[script,'--archive',archive,'--out',out],{encoding:'utf8'});}
  const first=run(report);assert.equal(first.status,0,first.stderr);const result=JSON.parse(await readFile(report,'utf8'));
  assert.equal(result.file_sha256,createHash('sha256').update(bytes).digest('hex'));assert.equal(result.exact_profile_and_prompt_match,true);assert.equal(result.model_calls,0);
  const changed=session.archive();changed.edited_prompt+=' 另一个选择。';await writeFile(archive,JSON.stringify(changed));assert.equal(run(path.join(dir,'bad-prompt.json')).status,1);
  changed.edited_prompt=session.body;changed.origin='user_provided';await writeFile(archive,JSON.stringify(changed));assert.equal(run(path.join(dir,'bad-origin.json')).status,1);
});
