const {test}=require('node:test'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {personalReportDocument}=require('../src/lib/reportExport');
const {personalScheme}=require('../src/lib/personalScheme');
const {schemeFixture}=require('./fixtures/personalScheme');
const result=()=>({id:'saved-private-id',source:'saved',createdAt:'2026-10-18T10:15:00Z',report:{birthDate:'10.01.1982',birthWeekday:'Воскресенье',profileName:'Тестовый ученик',incomplete:false,numbers:[{key:'soul',shortTitle:'Душа',title:'Число души',value:1,meaning:'Личный смысл',interpretation:'Точная расшифровка',method:'Серверный метод',steps:['10 → 1'],note:''},{key:'wisdom',shortTitle:'Мудрость',title:'Число мудрости',value:null,meaning:'',interpretation:'',method:'',steps:[],note:'Имя не заполнено'}],scheme:personalScheme(schemeFixture(),'10.01.1982'),planets:{formula:'Точная формула',calculationNumber:3,birthWeekday:'Воскресенье',note:'Серверное примечание',items:['Солнце','Луна','Марс','Меркурий','Юпитер','Венера','Сатурн'].map((name,index)=>({name,value:index,meaning:`Смысл ${name}`}))}}});
test('export is a snapshot of saved numbers, zero cells, formulas, explanations and chart values',()=>{
 const input=result(),before=JSON.stringify(input),document=personalReportDocument(input);
 const dom=new JSDOM(document.html),body=dom.window.document.body;
 assert.equal(JSON.stringify(input),before);assert.equal(document.filename,'NumerOM-10011982.pdf');
 assert.match(body.textContent,/Тестовый ученик/);assert.match(body.textContent,/Точная расшифровка/);assert.match(body.textContent,/Серверный метод/);assert.match(body.textContent,/10 → 1/);
 assert.match(body.textContent,/Число мудрости: —/);assert.match(body.textContent,/Имя не заполнено/);assert.match(body.textContent,/В вашей ячейке: 0/);
 assert.equal(body.querySelectorAll('svg circle').length,7);
 assert.match(body.textContent,/Солнце · Воскресенье: 0 \/ 9/);assert.match(body.textContent,/Сатурн · Суббота: 6 \/ 9/);
 assert.match(body.textContent,/Точная формула/);assert.match(body.textContent,/Сохранён:/);assert.doesNotMatch(document.html,/saved-private-id/);
 dom.window.close();
});
test('all report text is inert HTML, including names, methods, notes, titles and values',()=>{
 const input=result(),payload='<img src="https://attacker.invalid/" onerror="alert(1)"><script>fetch("/token")</script>';
 input.report.profileName=payload;input.report.birthWeekday=payload;input.report.numbers[0].title=payload;input.report.numbers[0].method=payload;input.report.numbers[0].steps=[payload];input.report.numbers[0].note=payload;input.report.planets.items[0].meaning=payload;
 const output=personalReportDocument(input),dom=new JSDOM(output.html),document=dom.window.document;
 assert.equal(document.querySelectorAll('script,img,iframe,object,embed,a,form').length,0);
 assert.ok(document.body.textContent.includes(payload));
 for(const element of document.querySelectorAll('*'))for(const attribute of element.attributes)assert.ok(!attribute.name.startsWith('on'));
 assert.match(document.querySelector('meta[http-equiv="Content-Security-Policy"]').content,/default-src 'none'/);
 dom.window.close();
});
test('incomplete results remain explicitly incomplete and no missing matrix or planet values are manufactured',()=>{
 const input=result();input.report.scheme=null;input.report.planets=null;input.report.incomplete=true;
 const output=personalReportDocument(input);assert.match(output.html,/Часть пояснений не получена/);assert.match(output.html,/Квадрат для этого результата не получен/);assert.doesNotMatch(output.html,/<svg/);
 assert.throws(()=>personalReportDocument(null));
});

test('native export uses only supplied HTML, shares a PDF named after the report and clears the temporary file',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');const calls=[];
 class File{constructor(...parts){this.uri=parts.map(part=>part.uri||part).join('/');}get exists(){return false;}delete(){calls.push(['delete',this.uri]);}async move(target){calls.push(['move',this.uri,target.uri]);}}
 const deps={'expo-print':{printToFileAsync:async options=>{calls.push(['pdf',options]);return {uri:'file:///private/report.pdf'};}},'expo-sharing':{isAvailableAsync:async()=>true,shareAsync:async(...args)=>calls.push(['share',...args])},
  'expo-file-system':{File,Paths:{cache:'file:///cache'}},'react-native':{Linking:{openURL:async()=>{}}},'./reportName':require('./helpers/tsModule')('../src/lib/reportName.ts')};
 const mod={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(require.resolve('../src/lib/reportPrint.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:mod.exports,require:name=>{assert.ok(name in deps,`Unexpected dependency: ${name}`);return deps[name];}});
 await mod.exports.deliverReport('<html><head><title>10.01.1982 Иван Петров — полный разбор</title></head>Снимок отчёта</html>');
 assert.match(calls[0][1].html,/Снимок отчёта/);
 assert.deepEqual(calls[1],['move','file:///private/report.pdf','file:///cache/10.01.1982 Иван Петров — полный разбор.pdf']);
 assert.equal(calls[2][1],'file:///cache/10.01.1982 Иван Петров — полный разбор.pdf');assert.equal(calls[2][2].mimeType,'application/pdf');
 assert.deepEqual(calls[3],['delete','file:///cache/10.01.1982 Иван Петров — полный разбор.pdf']);
});

test('web export uploads only the selected report snapshot, stays in the app and waits for a tap to open it',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');const sent=[],opened=[];
 const ready=require('./helpers/tsModule')('../src/lib/readyReport.ts');
 const window={open:(...args)=>{opened.push(args);return {opener:'app'};},location:{assign:()=>assert.fail('app must stay open')}};
 const mod={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(require.resolve('../src/lib/reportPrint.web.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:mod.exports,require:name=>({
  './reportPdf':{reportPdfUrl:async(html,filename)=>{sent.push([html,filename]);return {url:'https://api.numerom.test/api/student/report-pdf/t/x.pdf',filename:filename+'.pdf',until:Date.now()+60000};}},
  './reportName':require('./helpers/tsModule')('../src/lib/reportName.ts'),'./readyReport':ready}[name]),window,Error});
 await mod.exports.deliverReport('<html><head><title>10.01.1982 Иван Петров — схемы и графики</title></head>Только выбранный отчёт</html>');
 assert.equal(sent.length,1);assert.match(sent[0][0],/Только выбранный отчёт/);assert.equal(sent[0][1],'10.01.1982 Иван Петров — схемы и графики');
 assert.deepEqual(opened,[],'nothing opens before the tap: a new tab would send the app to the background mid-upload');
 assert.equal(ready.readyReport.get().filename,'10.01.1982 Иван Петров — схемы и графики.pdf');
 mod.exports.openReport(ready.readyReport.get().url);
 assert.deepEqual(opened,[['https://api.numerom.test/api/student/report-pdf/t/x.pdf','_blank']]);
});
test('report PDF client posts the snapshot with its file name and accepts only a returned HTTPS link',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');const mod={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(require.resolve('../src/lib/reportPdf.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:mod.exports,Error,Date});
 await assert.rejects(mod.exports.reportPdfUrl('<p>x</p>'),/Войдите/);
 const calls=[];mod.exports.registerReportPdf(async(path,options)=>{calls.push([path,options]);return {url:'https://api.numerom.test/api/student/report-pdf/t/a.pdf',filename:'10.01.1982 Иван.pdf',expires_in:3600};});
 const file=await mod.exports.reportPdfUrl('<p>x</p>','10.01.1982 Иван');
 assert.equal(file.url,'https://api.numerom.test/api/student/report-pdf/t/a.pdf');assert.equal(file.filename,'10.01.1982 Иван.pdf');
 assert.ok(file.until>Date.now()+3500*1000&&file.until<=Date.now()+3540*1000,'a minute of margin before the link expires');
 assert.deepEqual(JSON.parse(JSON.stringify(calls)),[['/report-pdf',{method:'POST',body:{html:'<p>x</p>',filename:'10.01.1982 Иван'},timeoutMs:120000}]]);
 mod.exports.registerReportPdf(async()=>({url:'javascript:alert(1)'}));
 await assert.rejects(mod.exports.reportPdfUrl('<p>x</p>'),/не вернул ссылку/);
});
test('the file takes the page title, never an SVG title, and drops characters a file name cannot hold',()=>{
 const {reportName}=require('./helpers/tsModule')('../src/lib/reportName.ts');
 assert.equal(reportName('<html><head><title>10.01.1982 Иван &amp; Ко — полный разбор</title></head><body><svg><title>Квадрат</title></svg></body></html>'),'10.01.1982 Иван & Ко — полный разбор');
 assert.equal(reportName('<html><head></head><body><svg><title>Квадрат</title></svg></body></html>'),'NumerOM-report');
 assert.equal(reportName('<head><title>../a/b: "c"?</title></head>'),'a b c');
});
