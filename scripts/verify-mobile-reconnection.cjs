// Live, disposable-account drill. Run only when an intentional tunnel restart
// is being tested; credentials stay in the ignored runtime folder.
const fs=require('node:fs'),path=require('node:path');
const {createEndpointResolver}=require('../mobile/src/lib/runtimeEndpoint');
const {createApiClient,createSessionController}=require('../packages/api-client');
const root=path.resolve(__dirname,'..'),output=path.join(root,'artifacts/server-recovery-20261022');
const qa=JSON.parse(fs.readFileSync(path.join(root,'backend/private/runtime/recovery-qa.json'),'utf8'));
const trust=require('../mobile/src/lib/endpointTrust.json'),bundled=require('../mobile/public/runtime-config.json');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 let cached=null,token=null,session,logins=0;
 const endpoints=createEndpointResolver({...trust,bundled,storage:{get:async()=>cached,set:async value=>{cached=value;}}});
 const api=createApiClient({baseUrl:bundled.api,getBaseUrl:endpoints.ready,onConnectionFailure:endpoints.recover,
  getToken:()=>session.getToken(),fetchImpl:(url,options)=>{if(url.endsWith('/auth/login'))logins++;return fetch(url,options);}});
 session=createSessionController({api,storage:{get:async()=>token,set:async value=>{token=value;},remove:async()=>{token=null;}}});
 await session.signIn(qa.email,qa.password);
 const before=endpoints.current(),started=Date.now();
 if(session.getSnapshot().user?.id!==qa.id)throw Error('Unexpected test identity');
 fs.writeFileSync(path.join(output,'client-before.json'),JSON.stringify({before,signed_in:true,started},null,2));
 console.log('Signed in; waiting for supervised tunnel rotation.');
 while(Date.now()-started<300000){
  await wait(10000);await endpoints.refresh();
  if(endpoints.current()===before)continue;
  await session.restore();
  if(session.getSnapshot().status!=='signedIn')continue;
  const result={passed:session.getSnapshot().user?.id===qa.id&&logins===1,before,after:endpoints.current(),
   login_requests:logins,restored_without_password:true,elapsed_seconds:Math.round((Date.now()-started)/1000)};
  fs.writeFileSync(path.join(output,'live-reconnection.json'),JSON.stringify(result,null,2));
  if(!result.passed)throw Error('Session recovery did not preserve identity');
  console.log(JSON.stringify(result));return;
 }
 throw Error('Endpoint rotation was not observed before the drill deadline');
})().catch(error=>{console.error(error.message);process.exitCode=1;});
