const {test}=require('node:test');
const assert=require('node:assert/strict');
const {clientUrls}=require('../src/lib/config');
test('empty Expo extra objects do not become API addresses',()=>{
 assert.deepEqual(clientUrls({apiUrl:{},siteUrl:{}},'web'),{backendUrl:'http://127.0.0.1:8000',websiteUrl:'http://127.0.0.1:5128'});
 assert.deepEqual(clientUrls({},'android'),{backendUrl:'http://10.0.2.2:8000',websiteUrl:null});
});
test('configured HTTPS server is used unchanged on a physical phone',()=>{
 assert.deepEqual(clientUrls({apiUrl:'https://api.example.org',siteUrl:'https://example.org'},'ios'),{backendUrl:'https://api.example.org',websiteUrl:'https://example.org'});
});
test('public builds never offer a localhost website link',()=>{
 assert.equal(clientUrls({production:true,apiUrl:'https://api.example.org'},'web').websiteUrl,null);
});
