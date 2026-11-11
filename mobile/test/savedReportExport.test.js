const test=require('node:test'),assert=require('node:assert/strict');
const {toolReportDocument,relationshipReportDocument}=require('../src/lib/savedReportExport');
test('tool PDF includes all items, arithmetic and chart with escaped personal inputs',()=>{
 const html=toolReportDocument({created_at:'2026-10-18T10:00:00Z',results:{title:'Имя',summary:'<script>alert(1)</script>',method:'Сумма букв',items:[{label:'Имя',number:3,source:'<img src=x onerror=alert(1)>',title:'Тройка',interpretation:'Смысл',focus:'Внимание',steps:['1 + 2 = 3'],tokens:[{symbol:'А',value:1},{symbol:'Б',value:2}]},{label:'Фамилия',number:1,source:'А',title:'Единица',interpretation:'Другой смысл',focus:'Инициатива',steps:['1 = 1'],tokens:[{symbol:'А',value:1}]}]}});
 assert.ok(html.includes('Фамилия'));assert.ok(html.includes('1 + 2 = 3'));assert.ok(html.includes('Частота значений'));assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));assert.ok(!html.includes('<img src=x'));assert.ok(html.includes("default-src 'none'"));
});
test('group PDF retains every connection and original score and formula',()=>{
 const html=relationshipReportDocument({created_at:'2026-10-18',results:{kind:'group',main:{name:'Анна',number:1,birth_date:'01.01.1980',steps:['1 + 0 = 1']},people:[{name:'<Борис>',number:2,birth_date:'02.01.1980',steps:['2']}],average:7,note:'Пример',method:'Метод',connections:[{name:'<Борис>',score:7,title:'Тема',interpretation:'Разбор',focus:'Практика',formula:'10 − 3 = 7'}]}});
 assert.ok(html.includes('&lt;Борис&gt;'));assert.ok(html.includes('width:70%'));assert.ok(html.includes('10 − 3 = 7'));assert.ok(html.includes('Средний индекс группы: 7 / 10'));
});
