// Offline: render exact requests or produce the validated portable card from a model response.
import {readFile} from 'node:fs/promises';
import {Session} from '../../apps/mobile/src/session.mjs';
import {makeRequest} from '../../web/dist/core.mjs';

const source = await readFile(new URL('./source.txt', import.meta.url), 'utf8');
const session = new Session();
session.prepare(source, 'trajectory', 768);
const original = makeRequest(session.prepared.sources, 768);
// Preserve the single-instruction candidate used in this frozen comparison.
const candidate = '如果用户明确指定了一个会改变执行结果的非私密短值，在对应判断和随身 prompt 正文中原样保留它，并写清它适用于什么情境、条件变化时怎样处理。泛称不能代替这个值。只保留执行所需的最小片段；私人身份信息、凭证和原句仍应省去。材料没指定的值不要补。\n\n' + original;
const task = '请给一个尚未标日期的档案盒起名，只回复盒名。不要使用工具。';
const [command, file] = process.argv.slice(2);
if (command === 'requests') {
  console.log(JSON.stringify({original, candidate, task}, null, 2));
} else if (command === 'portable' && file) {
  session.importAnswer(await readFile(file, 'utf8'));
  console.log(JSON.stringify((await session.bundle()).portable));
} else {
  throw Error('Use requests or portable <answer.json>.');
}
