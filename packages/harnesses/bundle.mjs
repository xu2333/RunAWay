import {getAdapter, makeExport} from './index.mjs';
import {zipFiles} from './zip.mjs';

export const SOURCE_FILES = ['index.mjs','codex.mjs','claude-code.mjs','antigravity.mjs','install.mjs'];
export async function makeBundle(target, text, sourceFiles) {
  if (!sourceFiles || SOURCE_FILES.some(name => typeof sourceFiles[name] !== 'string' || !sourceFiles[name].trim()))
    throw Error('Local installer source is missing.');
  const adapter = getAdapter(target), manifest = await makeExport(target, text);
  const instructions = `RunAWay → ${adapter.label}\n\n` +
    `1. Unzip into a temporary folder. Do not unzip over your project.\n` +
    `2. Inspect ${adapter.path} before installing. This archive contains your prompt; keep it private.\n` +
    `3. With Node 22+, run: node install.mjs --project "/path/to/your/project" --dry-run\n` +
    `4. To install: node install.mjs --project "/path/to/your/project"\n` +
    `5. ${adapter.note}\n\n` +
    `Remove later using this same installer with --remove. It preserves unrelated instructions\n` +
    `and refuses to overwrite an edited RunAWay block. No model calls or network access.\n` +
    `File formatting is checked; actual harness loading and personal fidelity are not verified.\n` +
    `Existing Python 'runaway attach' installations use a separate state format: detach those first.\n` +
    `Documentation: ${adapter.documentation}\n`;
  return {manifest, bytes: zipFiles([
    ...manifest.files.map(f => ({name:f.path, text:f.content})),
    {name:'runaway-export.json', text:JSON.stringify(manifest,null,2)+'\n'},
    {name:'install.mjs', text:"import {runCLI} from './harnesses/install.mjs';\nawait runCLI(new URL('.',import.meta.url));\n"},
    ...SOURCE_FILES.map(name => ({name:'harnesses/'+name,text:sourceFiles[name]})),
    {name:'READ-ME.txt', text:instructions},
  ])};
}
