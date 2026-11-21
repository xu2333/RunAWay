import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm,writeFile,mkdir} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const script=fileURLToPath(new URL('../scripts/package_ios_device.py',import.meta.url));
test('device package distinguishes unprovisioned arm64 from simulator/wrong-architecture artifacts',async t=>{
  const dir=await mkdtemp(path.join(os.tmpdir(),'runaway-device-package-'));t.after(()=>rm(dir,{recursive:true,force:true}));
  const app=path.join(dir,'archive/Products/Applications/App.app');await mkdir(app,{recursive:true});
  const info={CFBundleSupportedPlatforms:['iPhoneOS'],CFBundleExecutable:'App',CFBundleIdentifier:'io.runaway.taste',CFBundleShortVersionString:'0.1.0'};
  async function plist(value){const r=spawnSync('python3',['-c','import plistlib,json,sys;open(sys.argv[1],"wb").write(plistlib.dumps(json.load(sys.stdin)))',path.join(app,'Info.plist')],{input:JSON.stringify(value),encoding:'utf8'});assert.equal(r.status,0,r.stderr);}
  await plist(info);const header=Buffer.alloc(32);header.writeUInt32LE(0xfeedfacf);header.writeUInt32LE(0x100000c,4);await writeFile(path.join(app,'App'),header);
  function run(name){return spawnSync('python3',['-B',script,'--archive',path.join(dir,'archive'),'--out',path.join(dir,name)],{encoding:'utf8'});}
  const ok=run('device');assert.equal(ok.status,0,ok.stderr);const result=JSON.parse(ok.stdout);assert.equal(result.distribution_signed,false);assert.equal(result.installable_without_signing,false);assert.equal(result.architecture,'arm64');
  await plist({...info,CFBundleSupportedPlatforms:['iPhoneSimulator']});assert.notEqual(run('simulator').status,0);
  await plist(info);header.writeUInt32LE(0x1000007,4);await writeFile(path.join(app,'App'),header);assert.notEqual(run('intel').status,0);
  header.writeUInt32LE(0x100000c,4);await writeFile(path.join(app,'App'),header);await writeFile(path.join(app,'embedded.mobileprovision'),'not an approved profile');assert.notEqual(run('profile').status,0);
  assert.equal(JSON.parse(await readFile(path.join(dir,'device/build-info.json'),'utf8')).apple_distribution_validation_performed,false);
});
