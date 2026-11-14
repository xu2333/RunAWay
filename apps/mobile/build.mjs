import {build} from 'esbuild';
import {readFile,mkdir,copyFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {SOURCE_FILES} from '../../packages/harnesses/bundle.mjs';

const root = fileURLToPath(new URL('.',import.meta.url));
const sources = {};
for (const name of SOURCE_FILES) sources[name] = await readFile(new URL('../../packages/harnesses/'+name,import.meta.url),'utf8');
await rm(path.join(root,'dist'),{recursive:true,force:true});
await mkdir(path.join(root,'dist'),{recursive:true});
await build({entryPoints:[path.join(root,'src/app.mjs')],outfile:path.join(root,'dist/app.js'),
  bundle:true,format:'esm',platform:'browser',target:['safari15','chrome100'],
  define:{RUNAWAY_HARNESS_SOURCES:JSON.stringify(sources)},logLevel:'warning'});
for(const name of ['index.html','style.css']) await copyFile(path.join(root,'src',name),path.join(root,'dist',name));
await copyFile(path.join(root,'assets/icon.svg'),path.join(root,'dist/icon.svg'));
console.log('Bundled local mobile assets. No server, credentials, analytics or model calls.');
