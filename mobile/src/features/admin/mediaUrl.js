function privateMediaUrl(value,baseUrl,pattern){
 let url,base;try{url=new URL(value);base=new URL(baseUrl);}catch{throw new Error('Ссылка на файл не прошла проверку.');}
 const local=base.protocol==='http:'&&['127.0.0.1','localhost'].includes(base.hostname);
 if((url.protocol!=='https:'&&!local)||url.origin!==base.origin||url.username||url.password||!pattern.test(url.pathname))throw new Error('Ссылка на файл не прошла проверку.');
 return url.toString();
}
function attachmentUrl(value,baseUrl){return privateMediaUrl(value,baseUrl,/^\/api\/student\/exercise-attachment-media\/[^/]+$/);}
function materialUrl(value,baseUrl){return privateMediaUrl(value,baseUrl,/^\/api\/student\/media\/[^/]+$/);}
function consultationUrl(value,baseUrl){return privateMediaUrl(value,baseUrl,/^\/api\/student\/consultation-media\/[^/]+$/);}
module.exports={attachmentUrl,materialUrl,consultationUrl};
