import {readFile} from 'node:fs/promises';
import {Session} from '../../apps/mobile/src/session.mjs';
import {makeRequest} from '../../web/dist/core.mjs';

const read = name => readFile(new URL(name, import.meta.url), 'utf8');
const session = new Session();
const current = session.prepare((await read('source.txt')).trimEnd(), 'trajectory', 768);
const original = makeRequest(session.prepared.sources, 768);
const [command, file] = process.argv.slice(2);
if (command === 'requests') {
  console.log(JSON.stringify({original, current, tasks: JSON.parse(await read('tasks.json'))}, null, 2));
} else if (command === 'portable' && file) {
  session.importAnswer(await readFile(file, 'utf8'));
  console.log(JSON.stringify((await session.bundle()).portable));
} else {
  throw Error('Use requests or portable <answer.json>.');
}
