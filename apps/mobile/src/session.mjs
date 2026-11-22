import {pocketRequest} from './extraction.mjs';
import {sourcesFrom,validateSources,validateAnswer,makeBundle,parseJSON,HEADER,length,hash,canonical} from '../../../web/dist/core.mjs';
import {validatePrompt} from '../../../packages/harnesses/index.mjs';

const BUDGETS=[768,1000,1536,1600,2400,4000];
export class Session {
  constructor(){this.reset();}
  reset(){this.prepared=null;this.answer=null;this.body='';this.portable=null;this.origin='user_provided';}
  prepare(raw,kind,budget){
    if(!BUDGETS.includes(budget))throw Error('请选择支持的字符预算。');
    const sources=sourcesFrom(raw,kind);
    this.reset();this.prepared={sources,kind,budget};
    return pocketRequest(sources,budget);
  }
  request(){if(!this.prepared)throw Error('请先整理来源。');return pocketRequest(this.prepared.sources,this.prepared.budget);}
  importAnswer(raw){
    if(!this.prepared)throw Error('请先整理来源。');
    const answer=validateAnswer(parseJSON(raw),this.prepared.sources,this.prepared.budget);
    this.answer=answer;this.body=answer.prompt;this.portable=null;return answer;
  }
  async bundle(){
    if(this.portable)return {portable:this.portable,profile:null};
    if(!this.prepared||!this.answer)throw Error('请先导入提炼结果，或已有的 portable.json。');
    if(length(HEADER+this.body+'\n')>this.prepared.budget)throw Error('完整 prompt 超过当前预算；不会替你截断。');
    return makeBundle(this.answer,this.prepared.sources,this.body);
  }
  archive(){
    if(!this.prepared||!this.answer)throw Error('当前没有可保存的来源和提炼结果。');
    return {schema_version:1,artifact_type:'runaway_mobile_archive',origin:this.origin,prepared:this.prepared,answer:this.answer,edited_prompt:this.body};
  }
  async restore(raw){
    // An archive includes both the original source and the validated result,
    // so it can exceed the model-result cap even when each input was valid.
    if(typeof raw!=='string'||new TextEncoder().encode(raw).length>2000000)throw Error('档案超过 2 MB，请选用较小的档案。');
    let value;try{value=JSON.parse(raw);}catch{throw Error('档案不是完整 JSON。');}
    if(!value||typeof value!=='object'||Array.isArray(value))throw Error('不是支持的档案。');
    if(value.artifact_type==='portable_expression'){
      const {id,...base}=value;
      if(value.schema_version!==1||typeof id!=='string'||id!==await hash(canonical(base)))throw Error('portable.json 校验失败。');
      validatePrompt(value.text);this.reset();this.origin='unknown';this.portable=value;this.body=value.text;return {kind:'portable'};
    }
    if(!['runaway_mobile_archive','browser_session'].includes(value.artifact_type)||value.schema_version!==1||
       !value.prepared||!BUDGETS.includes(value.prepared.budget))throw Error('不是支持的私有档案。');
    const p=value.prepared;
    // Validate into a temporary session so a failed import never erases work.
    const next=new Session();
    if(!['experience','resume','trajectory'].includes(p.kind))throw Error('档案中的材料类型不正确。');
    next.prepared={sources:validateSources(p.sources),kind:p.kind,budget:p.budget};
    next.importAnswer(JSON.stringify(value.answer));
    next.body=value.edited_prompt??value.answer.prompt;
    next.origin=value.origin==='fictional_demo'||value.session?.demo===true?'fictional_demo':'user_provided';
    await next.bundle();
    Object.assign(this,next);return {kind:'archive'};
  }
}
