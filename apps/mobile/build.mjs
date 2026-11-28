import {build} from 'esbuild';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,copyFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {SOURCE_FILES} from '../../packages/harnesses/bundle.mjs';

const root = fileURLToPath(new URL('.',import.meta.url));
const sources = {};
for (const name of SOURCE_FILES) sources[name] = await readFile(new URL('../../packages/harnesses/'+name,import.meta.url),'utf8');
await rm(path.join(root,'dist'),{recursive:true,force:true});
await mkdir(path.join(root,'dist'),{recursive:true});
await build({entryPoints:[path.join(root,'src/app.mjs')],outfile:path.join(root,'dist/app.js'),
  bundle:true,format:'esm',platform:'browser',target:['safari15.4','chrome100'],
  define:{RUNAWAY_HARNESS_SOURCES:JSON.stringify(sources)},logLevel:'warning'});
// Keep an updated page from running a previous release's cached event handlers.
const script = await readFile(path.join(root,'dist/app.js'));
const version = createHash('sha256').update(script).digest('hex').slice(0,16);
const html = await readFile(path.join(root,'src/index.html'),'utf8');
await writeFile(path.join(root,'dist/index.html'),html.replace('src="./app.js"',`src="./app.js?v=${version}"`));
await copyFile(path.join(root,'src/style.css'),path.join(root,'dist/style.css'));
await copyFile(path.join(root,'assets/icon.svg'),path.join(root,'dist/icon.svg'));
console.log('Bundled local mobile assets. No server, credentials, analytics or model calls.');
