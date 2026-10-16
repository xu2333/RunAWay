// Validate only. Never normalize, delete or guess damaged historical characters.
export function requireIntact(value,label='文本'){
 if(typeof value!=='string')throw Error(`${label}必须是文本。`);
 let index=0;for(const char of value){const code=char.codePointAt(0);if(code===0xfffd||(code>=0xd800&&code<=0xdfff))throw Error(`${label}含损坏字符（位置 ${index}）。请恢复原文后重新导入，不要猜测替换文字。`);index++;}
 return value;
}
export function requireIntactTree(value,label='结果'){
 if(typeof value==='string')requireIntact(value,label);
 else if(Array.isArray(value))value.forEach((v,i)=>requireIntactTree(v,`${label}[${i}]`));
 else if(value&&typeof value==='object')for(const [k,v] of Object.entries(value))requireIntactTree(v,`${label}.${k}`);
 return value;
}
