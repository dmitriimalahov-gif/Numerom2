const test=require('node:test'),assert=require('node:assert/strict');
const {createRecoveryRequest}=require('../src/lib/recoveryRequest');
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
test('resend keeps the confirmed address, waits a minute, and sends one new request',async()=>{
 let time=1000;const sent=[];
 const c=createRecoveryRequest({now:()=>time,request:async email=>{sent.push(email);return {message:'Проверьте почту и спам.'};}});
 await c.submit(' test@example.invalid ');assert.deepEqual(sent,['test@example.invalid']);assert.equal(c.getSnapshot().sentTo,'test@example.invalid');
 assert.equal(c.remainingSeconds(),60);time+=59999;await c.submit('test@example.invalid');assert.equal(sent.length,1);assert.equal(c.remainingSeconds(),1);
 time++;assert.equal(c.remainingSeconds(),0);await c.submit('test@example.invalid');assert.equal(sent.length,2);assert.equal(c.remainingSeconds(),60);
});
test('an address typo can be corrected without reloading, preserving the request cooldown',async()=>{
 let time=0;const sent=[];const c=createRecoveryRequest({now:()=>time,request:async email=>{sent.push(email);return {message:'Если аккаунт существует, письмо отправится.'};}});
 await c.submit('typo@example.invalid');c.changeAddress();assert.equal(c.getSnapshot().message,'');assert.equal(c.getSnapshot().sentTo,'');
 await c.submit('correct@example.invalid');assert.equal(sent.length,1);
 time=60000;await c.submit('correct@example.invalid');assert.deepEqual(sent,['typo@example.invalid','correct@example.invalid']);assert.equal(c.getSnapshot().sentTo,'correct@example.invalid');
});
test('rapid taps do not send duplicate email requests and a lost response allows a later retry',async()=>{
 let time=0,calls=0;const gate=deferred();
 const c=createRecoveryRequest({now:()=>time,request:async()=>{calls++;if(calls===1)return gate.promise;return {message:'Проверьте почту.'};}});
 const first=c.submit('test@example.invalid');await c.submit('test@example.invalid');assert.equal(calls,1);
 gate.reject(Error('Нет соединения'));await first;assert.equal(c.getSnapshot().busy,false);assert.equal(c.remainingSeconds(),60);assert.match(c.getSnapshot().error,/Нет соединения/);
 time=60000;await c.submit('test@example.invalid');assert.equal(calls,2);assert.equal(c.getSnapshot().error,'');
});
test('invalid email never reaches server and a configured service failure does not hide retry',async()=>{
 let calls=0;const c=createRecoveryRequest({request:async()=>{calls++;throw Object.assign(Error('unavailable'),{status:503});}});
 await c.submit('wrong');assert.equal(calls,0);await c.submit('test@example.invalid');assert.equal(calls,1);assert.equal(c.remainingSeconds(),0);assert.match(c.getSnapshot().error,/временно недоступно/);
});
