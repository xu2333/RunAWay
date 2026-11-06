#!/usr/bin/env node
import {open,readFile,writeFile,mkdir,lstat} from 'node:fs/promises';
import {constants} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {canonical} from '../web/dist/core.mjs';
import {IntakeError,parseFeedbackJSON} from './feedback_intake_core.mjs';
import {ARMS,buildCheck,verifyCheck,evaluateCheck} from './memory_check_core.mjs';

const ROOT=dirname(dirname(fileURLToPath(import.meta.url)));
const DEPENDENCIES=['scripts/check_memory.mjs','scripts/memory_check_core.mjs','scripts/feedback_intake_core.mjs',
  'web/dist/core.mjs','web/dist/choice-core.mjs','web/dist/text-integrity.mjs','web/dist/choice-contract.json'];
async function text(path,limit=64000) {
  let file;
  try {
    file=await open(path,constants.O_RDONLY|constants.O_NONBLOCK);
    const stat=await file.stat();if(!stat.isFile())throw new IntakeError('not_regular_file');
    if(stat.size>limit)throw new IntakeError('input_too_large');
    const buffer=Buffer.alloc(limit+1);let count=0;
    while(count<buffer.length) {
      const {bytesRead}=await file.read(buffer,count,buffer.length-count,null);
      if(!bytesRead)break;count+=bytesRead;
    }
    if(count>limit)throw new IntakeError('input_too_large');
    try{return new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(buffer.subarray(0,count));}
    catch {throw new IntakeError('invalid_utf8');}
  }catch(error){if(error instanceof IntakeError)throw error;throw new IntakeError('unreadable_input');}
  finally {await file?.close();}
}
async function hashes() {
  return Object.fromEntries(await Promise.all(DEPENDENCIES.map(async name=>
    [name,createHash('sha256').update(await readFile(resolve(ROOT,name))).digest('hex')])));
}
async function absent(path) {
  try {await lstat(path);throw new IntakeError('output_exists');}
  catch(error){if(error.code!=='ENOENT')throw error;}
}
async function save(out,files) {
  await absent(out);await mkdir(dirname(out),{recursive:true,mode:0o700});await mkdir(out,{mode:0o700});
  for(const [name,value]of Object.entries(files)) {
    const raw=typeof value==='string'?value:JSON.stringify(value,null,2)+'\n';
    if(Buffer.byteLength(raw)>2000000)throw new IntakeError('output_too_large');
    await writeFile(resolve(out,name),raw,{flag:'wx',mode:0o600});
  }
}
function argsFor(argv) {
  if(argv.length===1&&argv[0]==='--help')return null;
  const command=argv.shift(),allowed=command==='prepare'?['source','memory','questions','reference','reader-mode','out']:
    command==='import'?['prepared','full-answer','card-answer','none-answer','out']:[];
  if(!allowed.length)throw new IntakeError('invalid_arguments');
  const values={};
  while(argv.length) {
    const key=argv.shift(),value=argv.shift();
    if(!key?.startsWith('--')||!value||!allowed.includes(key.slice(2))||Object.hasOwn(values,key.slice(2)))
      throw new IntakeError('invalid_arguments');
    values[key.slice(2)]=value;
  }
  const required=command==='prepare'?['source','memory','questions','out']:['prepared','out'];
  if(required.some(k=>!values[k]))throw new IntakeError('invalid_arguments');
  if(command==='import'&&!ARMS.some(arm=>values[arm+'-answer']))throw new IntakeError('invalid_arguments');
  return {command,values};
}
async function loadPrepared(path,contract) {
  const names=['prepared.private.json',...ARMS.flatMap(arm=>[arm+'.request.private.json',arm+'.request.private.md'])];
  if((await lstat(path)).isSymbolicLink())throw new IntakeError('prepared_symlink');
  for(const name of names)if((await lstat(resolve(path,name))).isSymbolicLink())throw new IntakeError('prepared_symlink');
  const packet=parseFeedbackJSON(await text(resolve(path,names[0]),2000000));
  verifyCheck(contract,packet);
  if(canonical(packet.dependencies)!==canonical(await hashes()))throw new IntakeError('compiler_changed');
  for(const arm of ARMS) {
    const req=parseFeedbackJSON(await text(resolve(path,arm+'.request.private.json'),2000000));
    const markdown=await text(resolve(path,arm+'.request.private.md'),2000000);
    if(canonical(req)!==canonical(packet.requests[arm])||markdown!==packet.requests[arm].prompt+'\n')
      throw new IntakeError('request_changed');
  }
  return packet;
}
export async function main(argv=process.argv.slice(2)) {
  try {
    const args=argsFor([...argv]);
    if(args===null){console.log('prepare --source experience.txt --memory prompt.md --questions questions.json [--reference reference.private.json] --out NEW_DIR\nimport --prepared PREPARED_DIR --full-answer full.json --card-answer card.json --none-answer none.json --out NEW_DIR');return 0;}
    const {command,values:v}=args,out=resolve(v.out);await absent(out);
    const contract=JSON.parse(await readFile(resolve(ROOT,'web/dist/choice-contract.json'),'utf8'));
    if(command==='prepare') {
      const value={schema_version:1,kind:'runaway_memory_check',source_text:await text(v.source),
        memory_text:await text(v.memory),queries:parseFeedbackJSON(await text(v.questions)),
        reference:v.reference?parseFeedbackJSON(await text(v.reference)):null,reader_mode:v['reader-mode']??'standard'};
      const packet={...buildCheck(contract,value),dependencies:await hashes()},files={'prepared.private.json':packet};
      for(const arm of ARMS) {
        files[arm+'.request.private.json']=packet.requests[arm];files[arm+'.request.private.md']=packet.requests[arm].prompt+'\n';
      }
      await save(out,files);
      console.log(JSON.stringify({status:'prepared',questions:value.queries.length,arms:ARMS,
        reference_in_requests:false,independent_fidelity_verified:false,model_calls_by_check:0,network_requests_by_check:0}));return 0;
    }
    const packet=await loadPrepared(resolve(v.prepared),contract),responses={};
    for(const arm of ARMS)if(v[arm+'-answer']) {
      try {responses[arm]={raw:await text(v[arm+'-answer'],200000)};}
      catch(error){responses[arm]={read_error:error instanceof IntakeError?error.code:'unreadable_input'};}
    }
    const {summary,review}=evaluateCheck(contract,packet,responses);
    await save(out,{'summary.json':summary,'review.private.json':review});
    console.log(JSON.stringify(summary,null,2));
    return ARMS.every(arm=>review.arms[arm].status==='valid')?0:2;
  }catch(error) {
    console.error(JSON.stringify({status:'check_failed',reason:error instanceof IntakeError?error.code:'invalid_input_or_local_io',
      model_calls_by_check:0,network_requests_by_check:0}));return 2;
  }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))process.exitCode=await main();
