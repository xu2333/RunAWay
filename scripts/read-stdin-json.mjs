// Buffer bytes before UTF-8 decoding: a stream chunk can split one character.
export async function readJsonUtf8(stream){
 const chunks=[];for await(const chunk of stream)chunks.push(Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk));
 const text=new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks));
 return JSON.parse(text);
}
