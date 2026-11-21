// Inspect a file saved by the real native picker. No service or synthetic response replay.
import {readFile,writeFile} from 'node:fs/promises';
import {Session} from './src/session.mjs';
import {createHash} from 'node:crypto';

const args=process.argv.slice(2);
if(args.length!==4||args[0]!=='--archive'||args[2]!=='--out')throw Error('Usage: node check-native-archive.mjs --archive FILE --out REPORT');
const bytes=await readFile(args[1]);
const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
const actual=new Session();await actual.restore(text);
const demo=JSON.parse(await readFile(new URL('../../web/dist/demo.json',import.meta.url),'utf8'));
const expected=new Session();expected.prepare(JSON.stringify(demo.sources),'trajectory',2400);
expected.importAnswer(JSON.stringify(demo.answer));expected.origin='fictional_demo';
const a=await actual.bundle(),e=await expected.bundle();
if(a.portable.id!==e.portable.id||a.profile?.id!==e.profile.id||actual.origin!=='fictional_demo')throw Error('Native archive differs from the untouched bundled demo.');
const report={schema_version:1,artifact_type:'native_fixture_archive_check',status:'passed',
  file_bytes:bytes.length,file_sha256:createHash('sha256').update(bytes).digest('hex'),sources:actual.prepared.sources.sources.length,
  claims:actual.answer.claims.length,profile_id:a.profile.id,portable_id:a.portable.id,
  exact_profile_and_prompt_match:true,fictional_origin_preserved:true,
  scope:'one bundled fictional fixture; file integrity, not personal-choice fidelity',model_calls:0};
await writeFile(args[3],JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(report));
