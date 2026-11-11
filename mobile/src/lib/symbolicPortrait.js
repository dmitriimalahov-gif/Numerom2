const {employeeInput}=require('./business');
const {nameSchemes}=require('../../../packages/numerology-core/name-schemes');
const {numberKnowledge}=require('./numberKnowledge');
const {reflectionHtml}=require('./reflectionKnowledge');
const {nameSchematicHtml,schematicStyles}=require('./schematicReportExport');
const note='Символический материал для личного размышления. Числа не используются в рабочем анализе, выборе должности или состава команды.';
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function reduced(seed,masters=[]){
 let value=seed;const steps=[];
 while(value>9&&!masters.includes(value)){const digits=String(value).split('').map(Number);value=digits.reduce((sum,n)=>sum+n,0);steps.push(`${digits.join(' + ')} = ${value}`);}
 return {value,steps};
}
function dateNumber(key,title,seed,formula,masters){
 const result=reduced(seed,masters),base=reduced(result.value).value;
 return {key,title,value:result.value,base,formula:[formula,...result.steps].join(' → '),master:result.value>9,knowledge:numberKnowledge(base)};
}
function symbolicPortrait(value){
 // Deliberately project identity fields before validation: job data never enters this model.
 const source=employeeInput({name:value?.name,surname:value?.surname,birth_date:value?.birth_date});
 const {name,surname,birth_date}=source;const numbers=[];
 if(birth_date){
  const [day,month,year]=birth_date.split('.').map(Number);
  numbers.push(dateNumber('soul','Число души',day,`День рождения: ${day}`,[11,22,33]));
  numbers.push(dateNumber('mind','Число ума',month,`Месяц рождения: ${month}`,[11,22,33]));
  numbers.push(dateNumber('destiny','Число судьбы',day+month+year,`${day} + ${month} + ${year} = ${day+month+year}`,[]));
 }
 return {name,surname,birthDate:birth_date,note,numbers,nameSchemes:nameSchemes({name,surname},birth_date),dateNote:birth_date?'':'Добавьте дату рождения в карточку, чтобы открыть числа даты.'};
}
function symbolicPortraitHtml(value){
 const portrait=symbolicPortrait(value);
 const numberHtml=portrait.numbers.map(n=>`<article><h2>${esc(n.title)} · ${n.value}</h2><p>${esc(n.formula)}</p>${n.master?`<p>Мастер-число ${n.value} сохраняется. Общая трактовка ниже относится к его базовой цифре ${n.base}.</p>`:''}<h3>${esc(n.knowledge?.planet)} · ${esc(n.knowledge?.title)}</h3>${(n.knowledge?.segments||[]).map(text=>`<p>${esc(text)}</p>`).join('')}</article>`).join('');
 const reflections=[...new Set(portrait.numbers.map(n=>n.base))].map(reflectionHtml).join('');
 return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"><title>Личный портрет · ${esc(portrait.name)} ${esc(portrait.surname)}</title><style>@page{size:A4;margin:16mm}*{box-sizing:border-box}body{max-width:760px;margin:auto;padding:24px;font:15px/1.6 Arial,sans-serif;color:#20364e}h1,h2,h3{color:#183b62;line-height:1.3}h2{margin-top:28px}p{white-space:pre-wrap;overflow-wrap:anywhere}article{break-inside:avoid-page}.note{padding:14px;background:#eaf1f9;border-radius:12px}footer{margin-top:28px;color:#61758b;font-size:12px}@media print{body{padding:0}}${schematicStyles}</style></head><body><p>NumerOM · Личный портрет</p><h1>${esc(portrait.name)} ${esc(portrait.surname)}</h1><p>${esc(portrait.birthDate||'Дата рождения не указана')}</p><p class="note">${esc(note)}</p>${numberHtml}${reflections?`<h2>Темы для размышления</h2>${reflections}`:''}${portrait.dateNote?`<p>${esc(portrait.dateNote)}</p>`:''}<h2>Абракадабра имени</h2>${nameSchematicHtml(portrait.nameSchemes,'triangle')}<h2>Человечек имени</h2>${nameSchematicHtml(portrait.nameSchemes,'human')}<footer>Построено по сохранённым имени, фамилии и дате рождения. Тексты — из базы знаний NumerOM. Экспорт бесплатный.</footer></body></html>`;
}
module.exports={symbolicPortrait,symbolicPortraitHtml};
