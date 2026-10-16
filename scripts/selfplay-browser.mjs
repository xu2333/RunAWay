// The benchmark calls the same extraction request, validation and bundle code as the UI.
import {makeRequest,validateAnswer,makeBundle} from '../web/dist/core.mjs';
import {readJsonUtf8} from './read-stdin-json.mjs';
const value=await readJsonUtf8(process.stdin);
if(value.operation==='request')process.stdout.write(JSON.stringify({request:makeRequest(value.sources,value.budget)}));
else if(value.operation==='validate'){
  validateAnswer(value.answer,value.sources,value.budget);
  process.stdout.write(JSON.stringify(await makeBundle(value.answer,value.sources)));
}else throw Error('Unknown browser bridge operation');
