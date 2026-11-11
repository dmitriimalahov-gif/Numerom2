const test=require('node:test'),assert=require('node:assert/strict');
const {createBiometricVault}=require('../src/lib/biometricVault');
function store(initial=null){let value=initial;return {get:async()=>value,set:async v=>{value=v;},remove:async()=>{value=null;},peek:()=>value};}
function setup(){const plain=store('token'),protectedStore=store(),flag=store();return {plain,protectedStore,flag,vault:createBiometricVault({plain,protectedStore,flag,available:()=>true})};}
test('enabled vault has no plain token and cannot restore without OS confirmation',async()=>{
 const x=setup();await x.vault.enable('token');assert.equal(x.plain.peek(),null);await assert.rejects(x.vault.get(),e=>e.code==='biometric_locked');assert.equal(await x.vault.get(true),'token');
});
test('cancel and changed biometric enrollment never release a token',async()=>{
 const x=setup();await x.vault.enable('token');x.protectedStore.get=async()=>{throw Error('cancel');};await assert.rejects(x.vault.get(true),e=>e.code==='biometric_locked');assert.equal(await x.vault.enabled(),true);
 x.protectedStore.get=async()=>null;assert.equal(await x.vault.get(true),null);assert.equal(await x.vault.enabled(),false);assert.equal(x.plain.peek(),null);
});
test('account change during opt-in cannot retain the previous account',async()=>{
 const x=setup();let current=true;x.protectedStore.get=async()=>{current=false;return 'token';};await assert.rejects(x.vault.enable('token',()=>current));assert.equal(x.protectedStore.peek(),null);assert.equal(await x.vault.enabled(),false);
});
test('sign out removes both credentials and opt-in after an in-flight enable',async()=>{
 const x=setup();const enabling=x.vault.enable('token');const removing=x.vault.remove();await Promise.all([enabling,removing]);assert.equal(await x.vault.get(),null);assert.equal(x.protectedStore.peek(),null);assert.equal(await x.vault.enabled(),false);
});
test('failed opt-out does not leave an unprotected copy of a locked token',async()=>{
 const x=setup();await x.vault.enable('token');x.flag.remove=async()=>{throw Error('write failed');};
 await assert.rejects(x.vault.disable());assert.equal(x.plain.peek(),null);assert.equal(x.protectedStore.peek(),'token');
 await assert.rejects(x.vault.get(),e=>e.code==='biometric_locked');
});
