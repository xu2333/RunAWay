#!/usr/bin/env node
// Offline export only; this command never invokes a model or edits a project.
import {readFile,writeFile} from 'node:fs/promises';
import {makeBundle,SOURCE_FILES} from '../packages/harnesses/bundle.mjs';
import {sha256} from '../packages/harnesses/index.mjs';
import {canonical} from '../web/dist/core.mjs';

try {
  const args=process.argv.slice(2),options={};
  for(let i=0;i<args.length;i++){
    if(!['--portable','--target','--out'].includes(args[i])||!args[i+1]||Object.hasOwn(options,args[i]))throw Error('Usage: node scripts/export_harness.mjs --portable portable.json --target codex|claude-code|antigravity --out NEW.zip');
    options[args[i]]=args[++i];
  }
  if(Object.keys(options).length!==3)throw Error('Specify --portable, --target and --out.');
  const portable=JSON.parse(await readFile(options['--portable'],'utf8')),{id,...base}=portable;
  if(portable.artifact_type!=='portable_expression'||portable.schema_version!==1||id!==await sha256(canonical(base)))throw Error('portable.json checksum or type differs.');
  const sources={};for(const name of SOURCE_FILES)sources[name]=await readFile(new URL('../packages/harnesses/'+name,import.meta.url),'utf8');
  const result=await makeBundle(options['--target'],portable.text,sources);
  await writeFile(options['--out'],result.bytes,{flag:'wx',mode:0o600});
  console.log(JSON.stringify({status:'exported',target:options['--target'],path:options['--out'],runtime_load_verified:false}));
}catch(e){console.error(e.message);process.exitCode=1;}
