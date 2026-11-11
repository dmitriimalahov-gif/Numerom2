const {serverDate}=require('./serverDate');
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p=value=>`<p>${esc(value)}</p>`;
const steps=values=>`<ol>${values.map(value=>`<li>${esc(value)}</li>`).join('')}</ol>`;
function bars(rows,max){return `<table>${rows.map(row=>`<tr><th>${esc(row.label)}</th><td><div class="track"><div class="bar" style="width:${Math.max(0,Math.min(100,row.value/max*100))}%"></div></div></td><td>${esc(row.value)}</td></tr>`).join('')}</table>`;}
function document(title,created,body,extraStyles=''){
 const stamp=serverDate(created);return `<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"><title>${esc(title)} · NumerOM</title><style>@page{size:A4;margin:16mm}*{box-sizing:border-box}body{max-width:760px;margin:auto;padding:24px;color:#20364e;background:white;font:15px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}h1,h2,h3{color:#183b62;line-height:1.3}h1{font-size:28px}h2{margin-top:28px;font-size:21px}h3{font-size:17px}p,li{white-space:pre-wrap;overflow-wrap:anywhere}header,footer{border-bottom:1px solid #d3dedb;padding:12px 0}footer{border-top:1px solid #d3dedb;border-bottom:0;font-size:12px;color:#61758b;margin-top:28px}.meta{color:#61758b;font-size:12px}.value{font-size:36px}article{break-inside:avoid-page}table{width:100%;border-collapse:collapse;table-layout:fixed}th{text-align:left;font-weight:500;width:34%;overflow-wrap:anywhere}td{padding:7px}td:last-child{width:48px;text-align:right}.track{height:12px;background:#eaf1f5;border-radius:6px;overflow:hidden}.bar{height:12px;background:#28705e;print-color-adjust:exact;-webkit-print-color-adjust:exact}.symbols{padding:12px;background:#eaf1f5;border-radius:10px}@media print{body{padding:0;font-size:11pt}h1,h2,h3{break-after:avoid}}@media(max-width:400px){body{padding:14px}}${extraStyles}</style></head><body><header><b>NumerOM</b><h1>${esc(title)}</h1>${stamp?`<p class="meta">Сохранён ${esc(stamp.toLocaleString('ru-RU',{timeZone:'UTC'}))} UTC</p>`:''}</header>${body}<footer>Документ создан из сохранённого результата. Экспорт не запускает новый расчёт и не списывает баллы.</footer></body></html>`;
}
function toolReportDocument(receipt){
 const r=receipt.results;if(!r?.items?.length)throw Error('Откройте сохранённый расчёт.');
 const body=p(r.summary)+r.items.map(item=>{
 const rows=Array.from({length:9},(_,i)=>({label:`Число ${i+1}`,value:item.tokens.filter(t=>t.value===i+1).length}));
 return `<article><h2>${esc(item.label)} · ${esc(item.number)}</h2>${p(item.source)}<h3>${esc(item.title)}</h3>${p(item.interpretation)}<h3>На что обратить внимание</h3>${p(item.focus)}<h3>Как получено число</h3><p class="symbols">${item.tokens.map(t=>`${esc(t.symbol)} → ${esc(t.value)}`).join(' · ')}</p>${steps(item.steps)}<h3>Частота значений</h3>${bars(rows,Math.max(1,...rows.map(row=>row.value)))}</article>`;
 }).join('')+`<h2>Метод расчёта</h2>${p(r.method)}`;
 return document(r.title,receipt.created_at,body);
}
function relationshipReportDocument(receipt){
 const r=receipt.results;if(!r?.connections?.length)throw Error('Откройте сохранённый разбор.');
 const members=[r.main,...r.people];
 const body=`<h2>Участники</h2>${members.map(person=>`<article><h3>${esc(person.name)} · ${esc(person.number)}</h3>${p(person.birth_date)}${steps(person.steps)}</article>`).join('')}<h2>Индексы ${r.kind==='pair'?'пары':'группы'}</h2>${bars(r.connections.map(item=>({label:`${r.main.name} + ${item.name}`,value:item.score})),10)}${r.kind==='group'?p(`Средний индекс группы: ${r.average} / 10`):''}${p(r.note)}${r.connections.map(item=>`<article><h2>${esc(r.main.name)} и ${esc(item.name)}</h2><h3>${esc(item.title)}</h3>${p(item.interpretation)}<h3>На что обратить внимание</h3>${p(item.focus)}${p(item.formula)}</article>`).join('')}<h2>Метод расчёта</h2>${p(r.method)}`;
 return document(r.kind==='pair'?'Совместимость пары':'Совместимость группы',receipt.created_at,body);
}
module.exports={toolReportDocument,relationshipReportDocument,document,bars,esc,p};
