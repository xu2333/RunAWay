#!/usr/bin/env node
import {open,readFile,mkdir,writeFile,lstat} from 'node:fs/promises';
import {constants} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {analyzeFeedback,parseFeedbackJSON,IntakeError} from './feedback_intake_core.mjs';

const ROOT=dirname(dirname(fileURLToPath(import.meta.url)));
const MAX_FILE=2000000,MAX_TOTAL=32000000;
function argumentsFor(argv) {
  if(argv.length===1&&argv[0]==='--help')return null;
  if(argv.shift()!=='summarize')throw new IntakeError('invalid_arguments');
  const inputs=[];let out;
  while(argv.length) {
    const key=argv.shift(),value=argv.shift();
    if(!value)throw new IntakeError('invalid_arguments');
    if(key==='--input')inputs.push(value);
    else if(key==='--out'&&!out)out=value;
    else throw new IntakeError('invalid_arguments');
  }
  if(!inputs.length||inputs.length>256||!out)throw new IntakeError('invalid_arguments');
  return {inputs,out:resolve(out)};
}
async function selectedFile(path,remaining) {
  let file,count=0;
  try {
    file=await open(path,constants.O_RDONLY|constants.O_NONBLOCK);const stat=await file.stat();
    if(!stat.isFile())throw new IntakeError('not_regular_file');
    if(stat.size>MAX_FILE)throw new IntakeError('input_too_large');
    if(stat.size>remaining||remaining<=0)throw new IntakeError('byte_budget_exhausted');
    const limit=Math.min(MAX_FILE,remaining),buffer=Buffer.alloc(limit+1);
    while(count<buffer.length) {
      const {bytesRead}=await file.read(buffer,count,buffer.length-count,null);
      if(!bytesRead)break;count+=bytesRead;
    }
    if(count>limit)throw new IntakeError(limit===MAX_FILE?'input_too_large':'byte_budget_exhausted');
    let text;try{text=new TextDecoder('utf-8',{fatal:true}).decode(buffer.subarray(0,count));}
    catch {return {read_error:'invalid_json',bytes:count};}
    try{return {value:parseFeedbackJSON(text),bytes:count};}
    catch(error){return {read_error:error instanceof IntakeError?error.code:'invalid_json',bytes:count};}
  }catch(error){return {read_error:error instanceof IntakeError?error.code:'unreadable_input',bytes:count};}
  finally {await file?.close();}
}

export async function main(argv=process.argv.slice(2)) {
  try {
    const args=argumentsFor([...argv]);
    if(args===null) {
      console.log('node scripts/choice_feedback.mjs summarize --input selected.json [--input another.json] --out new-review-directory');
      return 0;
    }
    try {await lstat(args.out);throw new IntakeError('output_exists');}
    catch(error){if(error.code!=='ENOENT')throw error;}
    const contract=JSON.parse(await readFile(resolve(ROOT,'web/dist/choice-contract.json'),'utf8'));
    const entries=[];let readBytes=0;
    for(const [index,path]of args.inputs.entries()) {
      const result=await selectedFile(path,MAX_TOTAL-readBytes);readBytes+=result.bytes;
      entries.push({file_index:index,...(result.read_error?{read_error:result.read_error}:{value:result.value})});
    }
    const {summary,review}=analyzeFeedback(entries,contract);
    review.selected_files=args.inputs.map((path,file_index)=>({file_index,path:resolve(path)}));
    await mkdir(dirname(args.out),{recursive:true,mode:0o700});
    await mkdir(args.out,{mode:0o700});
    await writeFile(resolve(args.out,'summary.json'),JSON.stringify(summary,null,2)+'\n',{flag:'wx',mode:0o600});
    await writeFile(resolve(args.out,'review.private.json'),JSON.stringify(review,null,2)+'\n',{flag:'wx',mode:0o600});
    console.log(JSON.stringify(summary,null,2));
    return summary.totals.rejected_files?2:0;
  }catch(error) {
    console.error(JSON.stringify({status:'intake_failed',reason:error instanceof IntakeError?error.code:'local_io_error',
      model_calls_by_intake:0,network_requests_by_intake:0}));
    return 2;
  }
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))process.exitCode=await main();
