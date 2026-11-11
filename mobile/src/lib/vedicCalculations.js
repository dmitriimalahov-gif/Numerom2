const {createPaidCalculationController}=require('../../../packages/api-client/paid-calculations');
const kinds={schedule:1,daily:1,weekly:7,monthly:30,quarterly:90};
const titles={schedule:'Ведическое время',daily:'День',weekly:'7 дней',monthly:'30 дней',quarterly:'90 дней'};
const keys=['surya','chandra','guru','rahu','budha','shukra','ketu','shani','mangal'];
const fail=()=>{throw Error('Маршрут получен не полностью. Проверьте сохранённые расчёты.');};
const price=v=>Number.isInteger(v)&&v>=0&&v<=1000000;
const iso=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&Number.isFinite(Date.parse(value+'T12:00:00Z'))&&new Date(value+'T12:00:00Z').toISOString().slice(0,10)===value;
function vedicCatalog(value){if(!value||Object.keys(kinds).some(k=>value[k]!==null&&!price(value[k])))fail();return Object.fromEntries(Object.keys(kinds).map(k=>[k,value[k]]));}
function validateDraft(v){
 if(!v||!Object.hasOwn(kinds,v.kind)||!iso(v.date)||v.date<'1900-01-01'||new Date(Date.parse(v.date+'T12:00:00Z')+(kinds[v.kind]-1)*86400000).getUTCFullYear()>2099)return 'Проверьте дату начала: ГГГГ-ММ-ДД (1900–2099).';
 if(typeof v.city!=='string'||v.city.trim().length<2||v.city.trim().length>120||/[\x00-\x1F]/.test(v.city)||! /\p{L}/u.test(v.city))return 'Укажите город и страну.';
 if(v.location!==undefined&&(!v.location||!Number.isFinite(v.location.latitude)||Math.abs(v.location.latitude)>90||!Number.isFinite(v.location.longitude)||Math.abs(v.location.longitude)>180))return 'Проверьте геолокацию или введите город вручную.';
 if(v.birth_date){const m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(v.birth_date);if(!m||!iso(`${m[3]}-${m[2]}-${m[1]}`)||Number(m[3])<1900||Date.parse(`${m[3]}-${m[2]}-${m[1]}T00:00:00Z`)>Date.now())return 'Проверьте дату рождения: ДД.ММ.ГГГГ.';}
 else if(v.kind!=='schedule')return 'Укажите дату рождения для персонального маршрута.';
 return '';
}
function vedicReceipt(value){
 const r=value?.results;
 if(!value||! /^[a-f0-9]{64}$/.test(value.id)||! /^[a-f0-9-]{36}$/i.test(value.request_id)||!Number.isFinite(Date.parse(value.created_at))||!price(value.cost)||r?.version!==1||!Object.hasOwn(kinds,r.kind)||!iso(r.start_date)||!iso(r.end_date)||!Array.isArray(r.days)||r.days.length!==kinds[r.kind]||r.narration_id!==`vedic-${r.kind}`)fail();
 for(const k of ['title','city','timezone','meaning','method','focus'])if(typeof r[k]!=='string'||!r[k])fail();
 for(let i=0;i<r.days.length;i++){
  const d=r.days[i],expected=new Date(Date.parse(r.start_date+'T12:00:00Z')+i*86400000).toISOString().slice(0,10);
  if(d.date!==expected||!Array.isArray(d.energies)||!Array.isArray(d.hours)||!Array.isArray(d.periods)||typeof d.sunrise!=='string'||typeof d.sunset!=='string')fail();
  if(r.kind==='schedule'){if(d.energies.length!==0||d.average!==null)fail();}
  else if(d.energies.length!==9||d.energies.some((e,index)=>e.key!==keys[index]||e.digit!==index+1||typeof e.title!=='string'||!Number.isFinite(e.value)||e.value<0||e.value>100)||!Number.isFinite(d.average)||Math.abs(d.average-d.energies.reduce((sum,e)=>sum+e.value,0)/9)>.011)fail();
  if(d.hours.length!==(kinds[r.kind]===1?24:0)||d.hours.some(h=>!Number.isInteger(h.hour)||!keys.includes(h.planet)||!['day','night'].includes(h.period)||typeof h.start!=='string'||typeof h.end!=='string'||typeof h.title!=='string'))fail();
  if(d.periods.some(p=>['id','title','start','end','meaning'].some(k=>typeof p[k]!=='string')))fail();
 }
 if(r.days.at(-1).date!==r.end_date)fail();
 return value;
}
function createVedicController(options){return createPaidCalculationController(options,{parseCatalog:vedicCatalog,parseReceipt:vedicReceipt,validateDraft,historyLimit:5});}
function routeGeometry(days){const left=25,top=14,width=290,height=118;return days.map((d,i)=>({x:left+(days.length===1?width/2:i*width/(days.length-1)),y:top+height*(1-d.average/100),value:d.average,date:d.date}));}
module.exports={kinds,titles,vedicCatalog,vedicReceipt,validateDraft,createVedicController,routeGeometry};
