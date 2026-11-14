import {sourcesFrom,makeRequest,validateAnswer,makeBundle,parseJSON,HEADER,length,hash,canonical} from '../../../web/dist/core.mjs';
import {validatePrompt} from '../../../packages/harnesses/index.mjs';

const BUDGETS=[768,1000,1536,1600,2400,4000];
export class Session {
  constructor(){this.reset();}
  reset(){this.prepared=null;this.answer=null;this.body='';this.portable=null;}
  prepare(raw,kind,budget){
    if(!BUDGETS.includes(budget))throw Error('请选择支持的字符预算。');
    const sources=sourcesFrom(raw,kind);
    this.reset();this.prepared={sources,kind,budget};
    return makeRequest(sources,budget);
  }
  request(){if(!this.prepared)throw Error('请先整理来源。');return makeRequest(this.prepared.sources,this.prepared.budget);}
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
    return {schema_version:1,artifact_type:'runaway_mobile_archive',prepared:this.prepared,answer:this.answer,edited_prompt:this.body};
  }
  async restore(raw){
    const value=parseJSON(raw);
    if(value.artifact_type==='portable_expression'){
      const {id,...base}=value;
      if(value.schema_version!==1||typeof id!=='string'||id!==await hash(canonical(base)))throw Error('portable.json 校验失败。');
      validatePrompt(value.text);this.reset();this.portable=value;this.body=value.text;return {kind:'portable'};
    }
    if(!['runaway_mobile_archive','browser_session'].includes(value.artifact_type)||value.schema_version!==1||
       !value.prepared||!BUDGETS.includes(value.prepared.budget))throw Error('不是支持的私有档案。');
    const p=value.prepared;
    // Validate into a temporary session so a failed import never erases work.
    const next=new Session();
    next.prepare(JSON.stringify(p.sources),'trajectory',p.budget);
    next.importAnswer(JSON.stringify(value.answer));
    next.body=value.edited_prompt??value.answer.prompt;
    await next.bundle();
    Object.assign(this,next);return {kind:'archive'};
  }
}
