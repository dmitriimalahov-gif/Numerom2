const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');

const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};
function load(file,deps,globals={}){
 const module={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,'../src/lib',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:module.exports,require:name=>{assert.ok(name in deps,name);return deps[name];},Error,...globals});
 return module.exports.deliverReport;
}
function native({available=async()=>true,generate=async()=>({uri:'file:///synthetic-business.pdf'})}={}){
 const events=[];
 const deliver=load('reportPrint.ts',{
  'expo-print':{printToFileAsync:async options=>{events.push(['generate',options]);return generate();},printAsync:async options=>events.push(['print',options])},
  'expo-sharing':{isAvailableAsync:available,shareAsync:async uri=>events.push(['share',uri])},
  'expo-file-system':{File:class{constructor(...parts){this.uri=parts.join('/');}get exists(){return false;}delete(){events.push(['delete',this.uri]);}async move(){throw new Error('read-only');}},Paths:{cache:'file:///cache'}},
  'react-native':{Linking:{openURL:async()=>{}}},'./reportName':require('./helpers/tsModule')('../src/lib/reportName.ts'),
 });
 return {deliver,events};
}
const LINK={url:'https://api.numerom.test/api/student/report-pdf/signed/a.pdf',filename:'a.pdf',until:Date.now()+600000};
function web({upload=async()=>LINK}={}){
 const events=[],ready=require('./helpers/tsModule')('../src/lib/readyReport.ts');
 const window={open:(...args)=>{events.push(['open',...args]);return {};},location:{assign:url=>events.push(['assign',url])}};
 const deliver=load('reportPrint.web.ts',{'./reportPdf':{reportPdfUrl:html=>{events.push(['upload',html]);return upload(html);}},
  './reportName':require('./helpers/tsModule')('../src/lib/reportName.ts'),'./readyReport':ready},{window});
 return {deliver,events,ready:ready.readyReport};
}
test('business native export aborts after PDF generation on owner or route cancellation and removes file',async()=>{
 const generated=deferred(),h=native({generate:()=>generated.promise});let current=true;
 const work=h.deliver('<p>Private staff data</p>',{isCurrent:()=>current});
 await new Promise(setImmediate);assert.equal(h.events[0][0],'generate');current=false;
 generated.resolve({uri:'file:///synthetic-private.pdf'});
 await assert.rejects(work,/Экспорт отменён/);
 assert.deepEqual(h.events.map(event=>event[0]),['generate','delete']);
 assert.equal(h.events[1][1],'file:///synthetic-private.pdf');
});
test('business native direct print never opens after asynchronous availability check is cancelled',async()=>{
 const availability=deferred(),h=native({available:()=>availability.promise});let current=true;
 const work=h.deliver('<p>Private staff data</p>',{isCurrent:()=>current});current=false;availability.resolve(false);
 await assert.rejects(work,/Экспорт отменён/);assert.deepEqual(h.events,[]);
});
test('business native export checks guard before starting and preserves ordinary callers',async()=>{
 const cancelled=native();await assert.rejects(cancelled.deliver('html',{isCurrent:()=>false}),/Экспорт отменён/);assert.deepEqual(cancelled.events,[]);
 const ordinary=native();await ordinary.deliver('html');assert.deepEqual(ordinary.events.map(event=>event[0]),['generate','share','delete']);
});
test('business web export prepares the PDF inside the app and drops it when the account changes during upload',async()=>{
 const uploaded=deferred(),h=web({upload:()=>uploaded.promise});let current=true;
 const work=h.deliver('<p>Private staff data</p>',{isCurrent:()=>current});
 assert.deepEqual(h.events,[['upload','<p>Private staff data</p>']],'no tab opens while the upload runs');
 current=false;uploaded.resolve(LINK);
 await assert.rejects(work,/Экспорт отменён/);
 assert.equal(h.ready.get(),null,'a cancelled export never offers its PDF');
});
test('business web export checks guard first and offers the server PDF to open with a tap',async()=>{
 const cancelled=web();await assert.rejects(cancelled.deliver('html',{isCurrent:()=>false}),/Экспорт отменён/);assert.deepEqual(cancelled.events,[]);
 const h=web();await h.deliver('<p>Report</p>',{isCurrent:()=>true});
 assert.equal(h.ready.get(),LINK);assert.equal(h.events.filter(event=>event[0]==='open').length,0);
 const failed=web({upload:async()=>{throw new Error('Не удалось собрать PDF. Повторите через минуту.');}});
 await assert.rejects(failed.deliver('<p>Report</p>'),/Не удалось собрать PDF/);assert.equal(failed.ready.get(),null);
});
