'use strict';
const {sectionDiagram,diagramSvg}=require('./schematics');
const ORDER=/^[a-f0-9]{64}$/;
const statuses=new Set(['creating','pending','processing','paid','expired','failed']);
const text=value=>typeof value==='string'?value:'';
const array=value=>Array.isArray(value)?value:[];
function validBirthDate(value,now=new Date()){
 const m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(value||'');if(!m)return false;
 const [d,mo,y]=m.slice(1).map(Number),date=new Date(Date.UTC(y,mo-1,d));
 return y>=1900&&date.getUTCFullYear()===y&&date.getUTCMonth()===mo-1&&date.getUTCDate()===d&&date.getTime()<=now.getTime();
}
function checkoutUrl(value){
 try{const u=new URL(value);return u.protocol==='https:'&&u.hostname==='checkout.stripe.com'&&!u.port&&!u.username&&!u.password?u.href:null;}catch{return null;}
}
function starsCheckoutUrl(value){
 try{const u=new URL(value);return u.protocol==='https:'&&u.hostname==='t.me'&&!u.port&&!u.username&&!u.password&&u.pathname.startsWith('/$')?u.href:null;}catch{return null;}
}
function validPrice(raw,allowDisabled=false){
 return raw?.payment_provider==='telegram'?raw.currency==='XTR'&&Number.isInteger(raw.amount_total)&&raw.amount_total>=(allowDisabled&&raw.enabled===false?0:1)&&raw.amount_total<=100000:raw?.amount_total===666&&raw?.currency==='eur';
}
function fullReportCatalog(raw){
 if(!raw||!validPrice(raw,true)||!['live','test'].includes(raw.mode))throw new Error('Не удалось подтвердить стоимость услуги. Обновите страницу.');
 return {...raw,title:text(raw.title)||'Полный разбор по дате рождения',enabled:raw.enabled===true,clients:array(raw.clients).filter(v=>v==='web'||v==='mobile'||v==='telegram'),includes:array(raw.includes).filter(v=>typeof v==='string'),message:text(raw.message)};
}
function chartValues(chart){
 return array(chart?.items).filter(i=>i&&typeof i.label==='string'&&typeof i.value==='number'&&Number.isFinite(i.value)&&i.value>=0).map(i=>({label:i.label,value:i.value}));
}
function fullReportOrder(raw){
 if(!raw||!ORDER.test(raw.order_id)||!validPrice(raw)||!statuses.has(raw.status)||!['live','test'].includes(raw.mode)||!validBirthDate(raw.birth_date))throw new Error('Не удалось прочитать заказ. Обновите историю разборов.');
 const paymentUrl=raw.payment_provider==='telegram'?starsCheckoutUrl:checkoutUrl;
 if(raw.url&&!paymentUrl(raw.url))throw new Error('Ссылка оплаты не подтверждена. Обновите заказ.');
 if(raw.person!==undefined&&(typeof raw.person!=='string'||raw.person.length>120))throw new Error('Не удалось прочитать заказ. Обновите историю разборов.');
 if(raw.report){
  const r=raw.report;
  if(raw.status!=='paid'||r.version!==1||r.birth_date!==raw.birth_date||r.as_of_date!==raw.as_of_date||!Array.isArray(r.sections)||!Array.isArray(r.summary))throw new Error('Сохранённый отчёт не подтверждён. Повторите загрузку.');
  if(!r.summary.every(v=>typeof v==='string')||!Array.isArray(r.excluded)||!r.excluded.every(v=>v&&typeof v.title==='string'&&typeof v.reason==='string')||!Array.isArray(r.narration)||!r.narration.every(v=>v&&typeof v.id==='string'&&typeof v.title==='string'&&typeof v.text==='string'&&typeof v.hash==='string'))throw new Error('Текст или озвучка отчёта получены не полностью. Повторите загрузку.');
  if(r.highlights!==undefined&&!(Array.isArray(r.highlights)&&r.highlights.every(g=>g&&typeof g.title==='string'&&Array.isArray(g.items)&&g.items.every(i=>i&&typeof i.text==='string'&&typeof i.basis==='string'))))throw new Error('Главное в разборе получено не полностью. Повторите загрузку.');
  for(const s of r.sections){
   if(!s||typeof s.id!=='string'||typeof s.title!=='string'||!Array.isArray(s.paragraphs)||!Array.isArray(s.values)||!Array.isArray(s.steps))throw new Error('Раздел отчёта не получен полностью. Повторите загрузку.');
   if(!s.paragraphs.every(v=>typeof v==='string')||!s.steps.every(v=>typeof v==='string')||!s.values.every(v=>v&&typeof v.label==='string'&&typeof v.meaning==='string'&&(v.value===null||typeof v.value==='string'||typeof v.value==='number'&&Number.isFinite(v.value))))throw new Error('Значения отчёта получены не полностью. Повторите загрузку.');
   if(s.position_readings!==undefined&&(!Array.isArray(s.position_readings)||new Set(s.position_readings.map(v=>v?.value_index)).size!==s.position_readings.length||!s.position_readings.every(v=>v&&Number.isInteger(v.value_index)&&v.value_index>=0&&v.value_index<s.values.length&&v.ref===`${s.id}:${v.value_index}`&&['definition','boundary','horizon','insight','attention','practice'].every(k=>typeof v[k]==='string'))))throw new Error('Персональные пояснения получены не полностью. Повторите загрузку.');
  }
 }
 return {...raw,url:raw.url?paymentUrl(raw.url):undefined};
}
// «10.01.1982 Иван Петров — полный разбор»: the saved file and the purchase list say whose report it is.
const KINDS={full:'полный разбор',schemes:'схемы и графики'};
function fullReportFileName(order,kind='full'){
 const person=String(order.person||'').trim();
 return `${order.birth_date}${person?` ${person}`:''} — ${KINDS[kind]||KINDS.full}`;
}
function fullReportStatus(status,reportStatus){
 return {creating:'Открываем оплату',pending:'Ожидает оплаты',processing:'Платёж обрабатывается',paid:reportStatus==='preparing'?'Оплачено · собираем отчёт':'Оплачено',expired:'Время оплаты истекло',failed:'Оплата не завершена'}[status]||'Проверяем заказ';
}
// Reading, PDF and mobile use the same contextual interpretation as narration.
function positionParagraphs(section,index){
 const reading=section.position_readings?.find(item=>item.value_index===index);
 if(!reading)return section.values[index]?.meaning?[section.values[index].meaning]:[];
 return [reading.definition,reading.boundary?`Контекст: ${reading.boundary}`:'',reading.insight,
  `На что обратить внимание: ${reading.attention}`,`Практика: ${reading.practice}`].filter(Boolean);
}
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const STYLE='@page{size:A4;margin:17mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#20364e;max-width:800px;margin:auto;line-height:1.6;font-size:13px;padding:24px}header{border-bottom:3px solid #183b62;padding-bottom:22px;margin-bottom:26px}h1{font-size:29px;line-height:1.2;color:#183b62}h2{font-size:21px;color:#183b62;break-after:avoid}h3{font-size:15px;break-after:avoid}p{margin:10px 0;white-space:pre-line}section{margin:28px 0}table{width:100%;border-collapse:collapse;margin:14px 0}th,td{text-align:left;border-bottom:1px solid #dde5ee;padding:8px;vertical-align:top;overflow-wrap:anywhere}tr{break-inside:avoid}thead{display:table-header-group}.number{font-size:19px;color:#183b62;font-weight:bold;white-space:nowrap}.method{background:#f4f7fb;padding:14px}.muted{color:#61758b}.matrix{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;break-inside:avoid}.matrix div{border:1px solid #dde5ee;padding:12px;display:flex;justify-content:space-between;gap:8px}.matrix strong{font-size:24px}.bar{display:grid;grid-template-columns:140px 1fr 35px;gap:12px;align-items:center;margin:9px 0;break-inside:avoid}.track{height:12px;background:#eaf1f9}.track i{display:block;height:12px;background:#356fa5}svg{width:100%;height:auto;break-inside:avoid}.series-table{font-size:11px}.test{padding:10px;background:#fff5df}.contents{columns:2}footer{margin-top:30px;border-top:1px solid #dde5ee;padding-top:12px;font-size:11px}@media print{body{padding:0}.track,.track i,.method,.test{print-color-adjust:exact;-webkit-print-color-adjust:exact}}';

function chartHtml(chart,table=true){
 const items=chartValues(chart);if(!items.length)return '';
 if(chart.type==='matrix')return `<div class="matrix">${items.map(i=>`<div><span>${esc(i.label)}</span><strong>${esc(i.value)}</strong></div>`).join('')}</div>`;
 if(chart.type==='series'){
  const max=Math.max(9,...items.map(i=>i.value)),x=i=>22+i*616/Math.max(1,items.length-1),y=v=>170-v/max*145;
  const points=items.map((i,n)=>`${x(n).toFixed(2)},${y(i.value).toFixed(2)}`).join(' ');
  const labels=items.filter((_,i)=>i===0||i===items.length-1||i%10===0).map(i=>{const n=items.indexOf(i);return `<text x="${x(n)}" y="193" text-anchor="middle" font-size="9">${esc(i.label)}</text>`;}).join('');
  return `<svg viewBox="0 0 660 205" role="img" aria-label="График значений"><path d="M22 20V170H638" fill="none" stroke="#c5d4e2"/><polyline points="${points}" fill="none" stroke="#356fa5" stroke-width="2"/>${labels}</svg>${table?`<table class="series-table"><thead><tr><th>Период</th><th>Число</th></tr></thead><tbody>${items.map(i=>`<tr><td>${esc(i.label)}</td><td>${i.value}</td></tr>`).join('')}</tbody></table>`:''}`;
 }
 const max=Math.max(1,...items.map(i=>i.value));
 return `<div class="bars">${items.map(i=>`<div class="bar"><span>${esc(i.label)}</span><div class="track"><i style="width:${(i.value/max*100).toFixed(2)}%"></i></div><strong>${i.value}</strong></div>`).join('')}</div>`;
}
function sectionGraphic(report,section){
 const diagram=sectionDiagram(report,section);
 return diagram?`<div class="report-schematic">${diagramSvg(diagram)}</div>`:chartHtml(section.chart);
}
function fullReportHtml(value){
 const order=fullReportOrder(value),r=order.report;if(!r)throw new Error('Отчёт ещё готовится. Повторите экспорт позже.');
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${esc(fullReportFileName(order))}</title><style>${STYLE}
 </style></head><body><header><strong>NumerOM</strong><h1>${esc(r.title)}</h1><p>${order.person?`${esc(order.person)}<br>`:''}Дата рождения: <b>${esc(r.birth_date)}</b><br>Дата расчёта: ${esc(r.as_of_date)}</p><p class="muted">Полный сохранённый разбор · 6,66 € · разовая покупка</p>${order.mode==='test'?'<p class="test">Тестовый отчёт. Оплата выполнена в тестовом режиме Stripe.</p>':''}</header>
 <section><h2>Главное в вашем разборе</h2>${r.summary.map(p=>`<p>${esc(p)}</p>`).join('')}${array(r.highlights).map(g=>`<h3>${esc(g.title)}</h3><ul>${g.items.map(i=>`<li>${esc(i.text)}<br><span class="muted">Основание в расчёте: ${esc(i.basis)}</span></li>`).join('')}</ul>`).join('')}</section>
 <nav><h2>Содержание</h2><ul class="contents">${r.sections.map(s=>`<li>${esc(s.title)}</li>`).join('')}</ul></nav>
 ${r.sections.map(s=>`<section><h2>${esc(s.title)}</h2>${s.paragraphs.map(p=>`<p>${esc(p)}</p>`).join('')}${sectionGraphic(r,s)}${s.values.length?`<table><thead><tr><th>Показатель</th><th>Результат</th><th>Пояснение</th></tr></thead><tbody>${s.values.map((i,n)=>`<tr><td>${esc(i.label)}</td><td class="number">${esc(i.value)}</td><td>${positionParagraphs(s,n).map(p=>`<p>${esc(p)}</p>`).join('')}</td></tr>`).join('')}</tbody></table>`:''}${s.method||s.steps.length?`<div class="method"><h3>Как рассчитано</h3><p>${esc(s.method)}</p>${s.steps.map(step=>`<p>${esc(step)}</p>`).join('')}</div>`:''}</section>`).join('')}
 ${array(r.excluded).length?`<section><h2>Для чего нужны дополнительные данные</h2>${r.excluded.map(i=>`<p><b>${esc(i.title)}.</b> ${esc(i.reason)}</p>`).join('')}</section>`:''}
 <footer>${esc(r.notice||'Интерпретации NumerOM описывают символику чисел и служат материалом для самонаблюдения.')}<p>Версия ${esc(r.version)}. Документ подготовлен из сохранённого отчёта; расчёты не изменялись при экспорте.</p></footer></body></html>`;
}
// «Краткий отчёт»: the same saved report with only its schemes, diagrams and charts — no explanations,
// interpretations, formulas or summary. A section without a graphic keeps a bare grid of its numbers.
function fullReportSchemesHtml(value){
 const order=fullReportOrder(value),r=order.report;if(!r)throw new Error('Отчёт ещё готовится. Повторите экспорт позже.');
 // A scheme carries its own title; charts and number grids get one.
 const graphic=s=>{const diagram=sectionDiagram(r,s);if(diagram)return `<div class="report-schematic">${diagramSvg(diagram)}</div>`;
  const chart=chartHtml(s.chart,false);if(chart)return chart;
  const numbers=s.values.filter(v=>v.value!==null&&v.value!=='');
  return numbers.length?`<div class="matrix">${numbers.map(v=>`<div><span>${esc(v.label)}</span><strong>${esc(v.value)}</strong></div>`).join('')}</div>`:'';};
 const parts=r.sections.map(s=>({s,body:graphic(s),titled:!sectionDiagram(r,s)})).filter(p=>p.body);
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${esc(fullReportFileName(order,'schemes'))}</title><style>${STYLE}.brief section{margin:18px 0;break-inside:avoid}.brief h2{font-size:17px;margin:0 0 8px}.brief .report-schematic svg{max-height:330px}</style></head><body class="brief"><header><strong>NumerOM</strong><h1>Краткий отчёт: схемы и графики</h1><p>${order.person?`${esc(order.person)}<br>`:''}Дата рождения: <b>${esc(r.birth_date)}</b><br>Дата расчёта: ${esc(r.as_of_date)}</p>${order.mode==='test'?'<p class="test">Тестовый отчёт. Оплата выполнена в тестовом режиме Stripe.</p>':''}</header>
 ${parts.map(({s,body,titled})=>`<section>${titled?`<h2>${esc(s.title)}</h2>`:''}${body}</section>`).join('')}
 <footer>Краткая версия полного разбора: только схемы, диаграммы и графики. Пояснения и расшифровки — в полном отчёте.</footer></body></html>`;
}
module.exports={validBirthDate,checkoutUrl,starsCheckoutUrl,fullReportCatalog,fullReportOrder,fullReportStatus,fullReportFileName,chartValues,fullReportHtml,fullReportSchemesHtml,positionParagraphs};
