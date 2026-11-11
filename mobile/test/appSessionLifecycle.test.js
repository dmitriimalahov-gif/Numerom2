const test=require('node:test'),assert=require('node:assert/strict');
const {createSessionController}=require('@numerom/api-client');
const {createBiometricVault}=require('../src/lib/biometricVault');
const {appSessionLifecycle}=require('../src/lib/appSessionLifecycle');
const store=(initial=null)=>{let value=initial;return {get:async()=>value,set:async v=>{value=v;},remove:async()=>{value=null;}};};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function setup(enabled){
 const plain=store('token'),protectedStore=store(),flag=store();let unlocks=0;
 const original=protectedStore.get;protectedStore.get=async()=>{unlocks++;return original();};
 const vault=createBiometricVault({plain,protectedStore,flag,available:()=>true});if(enabled)await vault.enable('token');
 const session=createSessionController({api:{profile:async()=>({id:'one'})},storage:vault});await session.restore(enabled);unlocks=0;
 return {session,vault,handle:appSessionLifecycle(session),unlocks:()=>unlocks};
}
test('quick background and foreground clears bearer synchronously and never bypasses biometric unlock',async()=>{
 const x=await setup(true);x.handle('background');assert.equal(x.session.getToken(),null);assert.equal(x.session.getSnapshot().status,'locked');
 x.handle('active');await tick();assert.equal(x.session.getSnapshot().status,'locked');assert.equal(x.session.getToken(),null);assert.equal(x.unlocks(),0);
 await x.session.restore(true);assert.equal(x.session.getToken(),'token');assert.equal(x.unlocks(),1);
});
test('ordinary native session resumes without OS prompt and signout cannot resurrect it',async()=>{
 const x=await setup(false);x.handle('background');assert.equal(x.session.getToken(),null);x.handle('active');await tick();assert.equal(x.session.getSnapshot().status,'signedIn');assert.equal(x.unlocks(),0);
 x.handle('background');await x.session.signOut();x.handle('active');await tick();assert.equal(x.session.getSnapshot().status,'signedOut');assert.equal(x.session.getToken(),null);
});
test('a biometric flag read failure fails closed after foreground',async()=>{
 const x=await setup(true);x.vault.get=async()=>{throw Error('store unavailable');};x.handle('background');x.handle('active');await tick();assert.equal(x.session.getToken(),null);assert.equal(x.session.getSnapshot().status,'unavailable');
});
