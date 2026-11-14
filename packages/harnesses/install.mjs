// RunAWay local installer. Executes only after the owner runs it explicitly.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import {getAdapter, BEGIN, END, sha256, validatePrompt} from './index.mjs';

async function read(file) {
  try { return await fs.readFile(file,'utf8'); }
  catch(e) { if(e.code === 'ENOENT') return null; throw e; }
}
async function safe(root, relative) {
  if (path.isAbsolute(relative) || relative.split('/').some(p => !p || p === '.' || p === '..'))
    throw Error('Invalid managed path.');
  let current = root;
  for (const part of relative.split('/')) {
    current = path.join(current,part);
    try { if ((await fs.lstat(current)).isSymbolicLink()) throw Error('Refusing a symlink in a managed path.'); }
    catch(e) { if (e.code !== 'ENOENT') throw e; }
  }
  return current;
}
async function atomic(file,text) {
  if (text === null) { await fs.unlink(file); return; }
  await fs.mkdir(path.dirname(file),{recursive:true,mode:0o700});
  const tmp = file + '.runaway-' + crypto.randomUUID();
  let mode = 0o600;
  try { mode = (await fs.stat(file)).mode & 0o777; } catch(e) { if (e.code !== 'ENOENT') throw e; }
  try { await fs.writeFile(tmp,text,{flag:'wx',mode}); await fs.rename(tmp,file); }
  finally { await fs.unlink(tmp).catch(e => { if (e.code !== 'ENOENT') throw e; }); }
}
function once(text,value) { return text.split(value).length === 2; }

export async function install({bundleDir,project,dryRun=false,remove=false}) {
  const root = path.resolve(project);
  if (!(await fs.lstat(root)).isDirectory()) throw Error('Choose an existing, non-symlink project directory.');
  const manifest = JSON.parse(await fs.readFile(path.join(bundleDir,'runaway-export.json'),'utf8'));
  if (manifest.schema_version !== 1 || manifest.artifact_type !== 'runaway_harness_export' ||
      !Array.isArray(manifest.files) || manifest.files.length !== 1) throw Error('Invalid export manifest.');
  const adapter = getAdapter(manifest.target), file = manifest.files[0];
  if (file.path !== adapter.path || typeof file.content !== 'string' ||
      await sha256(file.content) !== file.sha256 ||
      file.content !== await read(path.join(bundleDir,file.path))) throw Error('Export file checksum or path differs.');
  const start = adapter.preamble + BEGIN + '\n';
  if (!file.content.startsWith(start) || !file.content.endsWith(END+'\n') ||
      !once(file.content,BEGIN) || !once(file.content,END) ||
      new TextEncoder().encode(file.content).length > adapter.maxBytes) throw Error('Invalid instruction envelope.');
  const prompt = file.content.slice(start.length,-(END+'\n').length);
  validatePrompt(prompt);
  // Exports without a final newline get one when rendered. Bind the declared
  // original bytes, while checking that this is the only possible difference.
  if (await sha256(prompt) !== manifest.prompt_sha256 &&
      await sha256(prompt.slice(0,-1)) !== manifest.prompt_sha256) throw Error('Prompt checksum differs.');
  const target = await safe(root,adapter.path);
  const statePath = await safe(root,'.runaway/harness-'+adapter.id+'.json');
  const lockPath = await safe(root,'.runaway/harness-export.lock');
  const stateText = await read(statePath), before = await read(target);
  const old = stateText === null ? null : JSON.parse(stateText);
  if (old && (old.version !== 1 || old.target !== adapter.id || typeof old.segment !== 'string' ||
      typeof old.created !== 'boolean' || await sha256(old.segment) !== old.sha256 ||
      !old.segment.includes(BEGIN) || !old.segment.endsWith(END+'\n') ||
      before === null || !once(before,old.segment) || !once(before,BEGIN) || !once(before,END)))
    throw Error('The managed block or installation record changed. Preserve your edits before updating.');
  if (!old && before !== null && (before.includes(BEGIN) || before.includes(END)))
    throw Error('An untracked RunAWay block already exists. Detach the earlier installation first.');
  if (adapter.id === 'codex' && !remove && (await read(await safe(root,'AGENTS.override.md')))?.trim())
    throw Error('AGENTS.override.md shadows AGENTS.md. Resolve this before installing.');
  if (remove && !old) throw Error('No matching installation record. Nothing was removed.');
  if (!old && before !== null && !adapter.append && !remove)
    throw Error('The dedicated rule file already exists. Preserve it before installing.');
  if (adapter.preamble && old && !before.startsWith(adapter.preamble))
    throw Error('Rule frontmatter changed. Nothing was written.');
  const segment = old ? old.segment.slice(0,old.segment.indexOf(BEGIN)) + file.content.slice(adapter.preamble.length)
    : (adapter.preamble || (before ? '\n\n' : '')) + file.content.slice(adapter.preamble.length);
  // A dedicated rule's activation preamble must also survive when the owner
  // has added unrelated instructions outside our block.
  let after = remove ? before.replace(old.segment,adapter.preamble) : old ? before.replace(old.segment,segment) : (before || '')+segment;
  if (remove && old.created && after === adapter.preamble) after = null;
  if (!remove && Buffer.byteLength(after,'utf8') > adapter.maxBytes)
    throw Error('The combined instruction file exceeds the harness export limit. Nothing was truncated.');
  const next = remove ? null : JSON.stringify({version:1,target:adapter.id,created:old?.created ?? before===null,
    segment,sha256:await sha256(segment)},null,2)+'\n';
  const report = {status:dryRun?'planned':remove?'removed':'installed',target:adapter.id,
    files:[adapter.path,'.runaway/harness-'+adapter.id+'.json'],runtime_load_verified:false};
  if (dryRun) return report;
  await fs.mkdir(path.dirname(lockPath),{recursive:true,mode:0o700});
  const lock = await fs.open(lockPath,'wx',0o600);
  try {
    // Revalidate after the exclusive lock and immediately before writing.
    await safe(root,adapter.path); await safe(root,'.runaway/harness-'+adapter.id+'.json');
    if (await read(target)!==before || await read(statePath)!==stateText) throw Error('Files changed during planning.');
    await atomic(target,after);
    try { await atomic(statePath,next); }
    catch(e) { await atomic(target,before); throw e; }
  } finally { await lock.close(); await fs.unlink(lockPath); }
  return report;
}

export async function runCLI(bundleUrl,args=process.argv.slice(2)) {
  try {
    let project=null,dryRun=false,remove=false;
    for (let i=0;i<args.length;i++) {
      if(args[i]==='--project' && typeof args[i+1]==='string') project=args[++i];
      else if(args[i]==='--dry-run') dryRun=true;
      else if(args[i]==='--remove') remove=true;
      else throw Error('Usage: node install.mjs --project DIR [--dry-run] [--remove]');
    }
    if(!project) throw Error('An explicit --project directory is required.');
    const {fileURLToPath}=await import('node:url');
    console.log(JSON.stringify(await install({bundleDir:fileURLToPath(bundleUrl),project,dryRun,remove}),null,2));
  } catch(e) { console.error(e.message); process.exitCode=1; }
}
