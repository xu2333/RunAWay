#!/usr/bin/env node
// Read only explicitly selected, voluntary exports. No network or directory crawling.
import {readFile} from 'node:fs/promises';
import {auditSamples} from '../web/dist/presentation.mjs';
const args=process.argv.slice(2);
if(!args.length){console.error('Usage: node scripts/audit-output-samples.mjs sample.json [sample2.json ...]');process.exitCode=2;}
else {
  try {
    const samples=[];
    for(const file of args){const raw=await readFile(file);if(raw.length>20000)throw Error('Sample exceeds 20 KB');samples.push(JSON.parse(raw));}
    console.log(JSON.stringify(await auditSamples(samples),null,2));
  } catch(error){console.error('Output audit failed: '+error.message);process.exitCode=1;}
}
