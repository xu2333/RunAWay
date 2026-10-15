// The benchmark calls the same extraction request, validation and bundle code as the UI.
import {makeRequest,validateAnswer,makeBundle} from '../web/dist/core.mjs';
let data='';for await(const chunk of process.stdin)data+=chunk;
const value=JSON.parse(data);
if(value.operation==='request')process.stdout.write(JSON.stringify({request:makeRequest(value.sources,value.budget)}));
else if(value.operation==='validate'){
  validateAnswer(value.answer,value.sources,value.budget);
  process.stdout.write(JSON.stringify(await makeBundle(value.answer,value.sources)));
}else throw Error('Unknown browser bridge operation');
