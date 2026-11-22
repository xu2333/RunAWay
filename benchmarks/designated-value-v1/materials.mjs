// Offline: render exact requests or produce the validated portable card from a model response.
import {readFile} from 'node:fs/promises';
import {Session} from '../../apps/mobile/src/session.mjs';
import {makeRequest} from '../../web/dist/core.mjs';

const source = await readFile(new URL('./source.txt', import.meta.url), 'utf8');
const session = new Session();
const candidate = session.prepare(source, 'trajectory', 768);
const original = makeRequest(session.prepared.sources, 768);
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
