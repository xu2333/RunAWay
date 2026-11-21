import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm,symlink,mkdir} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {preparePersonalSigning} from '../apps/mobile/prepare-personal-signing.mjs';

test('Personal Team setup keeps a stable unique identifier and private team settings without signing',async t=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'runaway-personal-signing-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const first=await preparePersonalSigning(root);assert.match(first.bundle_id,/^io\.runaway\.taste\.personal\.local[a-f0-9]{12}$/);assert.equal(first.creates_credentials,false);assert.equal(first.signs_or_installs,false);
  const file=path.join(root,'.runaway/ios-personal-signing.xcconfig'),before=await readFile(file,'utf8');const again=await preparePersonalSigning(root);assert.equal(again.bundle_id,first.bundle_id);assert.equal(await readFile(file,'utf8'),before);
  assert.equal((await preparePersonalSigning(root,'ABCDE12345')).team_configured,true);assert.match(await readFile(file,'utf8'),/^DEVELOPMENT_TEAM = ABCDE12345$/m);
  await assert.rejects(preparePersonalSigning(root,'password or token'));
  const other=path.join(root,'other');await mkdir(other);await symlink(path.join(root,'.runaway'),path.join(other,'.runaway'),'dir');await assert.rejects(preparePersonalSigning(other),/symlink/);
});
