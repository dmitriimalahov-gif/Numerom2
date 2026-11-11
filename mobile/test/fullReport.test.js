const test=require('node:test');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {validBirthDate,checkoutUrl,fullReportCatalog,fullReportOrder,fullReportHtml,fullReportSchemesHtml,fullReportFileName,chartValues,positionParagraphs}=require('../../packages/full-report');
const fixture=require('../../docs/artifacts/full-report-fixture.json').report;
const order={order_id:'a'.repeat(64),status:'paid',mode:'test',amount_total:666,currency:'eur',birth_date:fixture.birth_date,as_of_date:fixture.as_of_date,report:fixture};
test('contextual reading replaces generic meaning in screen text and PDF, preserving calculation',()=>{
 const changed=structuredClone(order),section=changed.report.sections[0];
 section.position_readings=[{ref:`${section.id}:0`,value_index:0,definition:'Внутреннее желание начать.',boundary:'2026',horizon:'year',insight:'Самостоятельный выбор полезно сверять со своим интересом.',attention:'Чужие ожидания могут заслонить собственный замысел.',practice:'Наметьте этапы на год и ежемесячно сверяйте результат.'}];
 const text=positionParagraphs(section,0).join(' ');
 assert.match(text,/этапы на год/);assert.ok(!text.includes(section.values[0].meaning));
 const doc=new JSDOM(fullReportHtml(changed)).window.document;
 assert.ok(doc.body.textContent.includes(section.position_readings[0].insight));
 assert.ok(doc.body.textContent.includes(section.steps[0]));
 section.position_readings[0].value_index=999;
 assert.throws(()=>fullReportOrder(changed));
});
test('dates must exist and cannot be future; leap day retained',()=>{
 assert.equal(validBirthDate('29.02.2000'),true);assert.equal(validBirthDate('29.02.2001'),false);assert.equal(validBirthDate('01.01.1899'),false);assert.equal(validBirthDate('01.01.2099'),false);
});
test('checkout allows exact Stripe host without credentials, alternate port or suffix',()=>{
 assert.equal(checkoutUrl('https://checkout.stripe.com/c/pay/cs_test_xyz'),'https://checkout.stripe.com/c/pay/cs_test_xyz');
 for(const u of ['http://checkout.stripe.com/a','https://checkout.stripe.com.attacker.test/a','https://u@checkout.stripe.com/a','javascript:alert(1)','https://checkout.stripe.com:8443/a'])assert.equal(checkoutUrl(u),null);
});
test('catalog and receipt fail closed on amount, mode, status and snapshot mismatch',()=>{
 assert.equal(fullReportCatalog({amount_total:666,currency:'eur',mode:'test',enabled:true,clients:['mobile']}).enabled,true);
 assert.throws(()=>fullReportCatalog({amount_total:66,currency:'eur',mode:'test'}));
 for(const change of [{amount_total:667},{currency:'usd'},{mode:'unknown'},{status:'pending'},{birth_date:'11.01.1982'},{as_of_date:'2099-01-01'}])assert.throws(()=>fullReportOrder({...order,...change}));
 assert.equal(fullReportOrder(order).report,fixture);
});
test('PDF includes all actual sections, ninecells,100year values, methods and no live claim for sandbox',()=>{
 const doc=new JSDOM(fullReportHtml(order)).window.document;
 const content=doc.body.textContent;
 assert.match(content,/Тестовый отчёт/);assert.equal(doc.querySelectorAll('svg [data-cell]').length>=9,true);
 for(const section of fixture.sections){assert.ok(content.includes(section.title));for(const v of section.values)assert.ok(content.includes(v.label),v.label);for(const step of section.steps)assert.ok(content.includes(step));}
 const series=fixture.sections.filter(s=>s.chart?.type==='series');assert.ok(series.some(s=>s.chart.items.length===100));
 assert.equal(doc.querySelectorAll('script,iframe,img').length,0);
});
test('report export escapes markup in text and chart labels',()=>{
 const report=JSON.parse(JSON.stringify(fixture));report.summary[0]='<script>alert("x")</script>';
 report.sections[0].chart={type:'bars',items:[{label:'<img src=x onerror=alert(1)>',value:3}]};
 const doc=new JSDOM(fullReportHtml({...order,report})).window.document;
 assert.equal(doc.querySelectorAll('script,img').length,0);assert.ok(doc.body.textContent.includes('<script>'));
 assert.deepEqual(chartValues({items:[{label:'bad',value:Infinity},{label:'zero',value:0}]}),[{label:'zero',value:0}]);
});
test('no unpaid export even if client tries to attach a report',()=>{
 assert.throws(()=>fullReportHtml({...order,status:'pending'}));assert.throws(()=>fullReportHtml({...order,report:undefined}));
});

test('saved files and the purchase list name the person and the birth date',()=>{
 const named={...order,person:'Иван Петров'};
 assert.equal(fullReportFileName(named),`${order.birth_date} Иван Петров — полный разбор`);
 assert.equal(fullReportFileName(named,'schemes'),`${order.birth_date} Иван Петров — схемы и графики`);
 assert.equal(fullReportFileName(order),`${order.birth_date} — полный разбор`,'a report without profile data keeps the date');
 const full=new JSDOM(fullReportHtml(named)).window.document,brief=new JSDOM(fullReportSchemesHtml(named)).window.document;
 assert.equal(full.title,fullReportFileName(named));assert.equal(brief.title,fullReportFileName(named,'schemes'));
 assert.match(full.querySelector('header').textContent,/Иван Петров/);
 assert.equal(fullReportOrder(named).person,'Иван Петров');
 for(const person of [5,'x'.repeat(121)])assert.throws(()=>fullReportOrder({...order,person}));
 assert.match(new JSDOM(fullReportHtml({...order,person:'<b>Иван</b>'})).window.document.title,/<b>Иван<\/b>/,'the name stays text');
});
