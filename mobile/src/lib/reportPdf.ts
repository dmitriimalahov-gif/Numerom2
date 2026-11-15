/** Server-made PDF of a self-contained report snapshot. The session registers its API client here. */
type Request=(path:string,options:{method:string;body:unknown;timeoutMs:number})=>Promise<unknown>;
export type ReportFile={url:string;filename:string;until:number};
let request:Request|null=null;
export function registerReportPdf(next:Request|null){request=next;}
export async function reportPdfUrl(html:string,filename?:string,orderId?:string):Promise<ReportFile>{
 if(!request)throw new Error('Войдите в аккаунт, чтобы сохранить PDF.');
 // Chrome on the server may need up to a minute and a half for a long report while a video renders.
 const body={...(filename?{filename}:{}),...(orderId?{order_id:orderId}:{}),html};
 const result=await request('/report-pdf',{method:'POST',body,timeoutMs:120000}) as {url?:unknown;filename?:unknown;expires_in?:unknown}|null;
 const url=result?.url;
 if(typeof url!=='string'||!/^(https:\/\/|http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\/)/.test(url))throw new Error('Сервер не вернул ссылку на PDF. Повторите попытку.');
 const seconds=typeof result?.expires_in==='number'&&result.expires_in>0?result.expires_in:3600;
 // A minute of margin so a tap near the end never opens an expired link.
 return {url,filename:typeof result?.filename==='string'?result.filename:`${filename||'NumerOM-report'}.pdf`,until:Date.now()+Math.max(0,seconds-60)*1000};
}
