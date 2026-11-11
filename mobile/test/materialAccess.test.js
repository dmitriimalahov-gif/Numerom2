const test=require('node:test'),assert=require('node:assert/strict');
const {createMaterialAccess}=require('../src/lib/materialAccess');
const {safeLearningUrl}=require('../src/lib/learning');
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
test('leaving the screen aborts the signed-link request and ignores its late URL',async()=>{
 const gate=deferred(),opened=[];let signal;
 const c=createMaterialAccess({openUrl:async url=>opened.push(url),validateUrl:safeLearningUrl});
 const work=c.open('lesson-pdf',value=>{signal=value;return gate.promise;});assert.equal(c.getSnapshot().opening,'lesson-pdf');
 c.cancel();assert.equal(signal.aborted,true);assert.equal(c.getSnapshot().opening,null);
 gate.resolve('https://example.invalid/private-file');await work;assert.deepEqual(opened,[]);assert.equal(c.getSnapshot().error,'');
});
test('a replaced session cannot open a link even before component cleanup',async()=>{
 let account='student-a';const gate=deferred(),opened=[];
 const c=createMaterialAccess({openUrl:async url=>opened.push(url),isCurrent:()=>account==='student-a'});
 const work=c.open('consultation',()=>gate.promise);account='student-b';gate.resolve('https://example.invalid/private-file');await work;
 assert.deepEqual(opened,[]);assert.equal(c.getSnapshot().opening,null);
});
test('late cancelled errors cannot alter a newly requested material',async()=>{
 const first=deferred(),second=deferred(),opened=[];const c=createMaterialAccess({openUrl:async url=>opened.push(url)});
 const a=c.open('first',()=>first.promise);c.cancel();const b=c.open('second',()=>second.promise);
 first.reject(Error('Old request failed'));await a;assert.equal(c.getSnapshot().opening,'second');assert.equal(c.getSnapshot().error,'');
 second.resolve('https://example.invalid/second');await b;assert.deepEqual(opened,['https://example.invalid/second']);assert.equal(c.getSnapshot().opening,null);
});
test('double tap requests and opens one material, and unsafe URLs never launch',async()=>{
 const gate=deferred(),opened=[];let requests=0;
 const c=createMaterialAccess({openUrl:async url=>opened.push(url),validateUrl:safeLearningUrl});
 const first=c.open('file',()=>{requests++;return gate.promise;});await c.open('file',async()=>{requests++;return 'https://example.invalid/duplicate';});
 gate.resolve('https://example.invalid/file');await first;assert.equal(requests,1);assert.deepEqual(opened,['https://example.invalid/file']);
 await c.open('unsafe',async()=>'file:///private');assert.equal(opened.length,1);assert.match(c.getSnapshot().error,/безопасной ссылки/);
});
