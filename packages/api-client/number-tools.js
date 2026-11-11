const fail=()=>{throw Error('Сервер вернул неполный расчёт. Обновите историю.');};
const price=value=>Number.isInteger(value)&&value>=0&&value<=1000000;
const text=value=>typeof value==='string'&&value.length>0;
const numbers=[1,2,3,4,5,6,7,8,9,11,22,33];
const kinds=['name','address','car'];
function toolCatalog(value){
 if(!value || !kinds.every(key=>value[key]===null || price(value[key])))fail();
 return Object.fromEntries(kinds.map(key=>[key,value[key]]));
}
function toolReceipt(value){
 const r=value?.results;
 if(!value || !text(value.id) || !text(value.request_id) || !price(value.cost) || !Number.isFinite(Date.parse(value.created_at)) ||
  !r || r.version!==1 || !kinds.includes(r.kind) || !text(r.title) || !text(r.summary) || !text(r.method) ||
  !Array.isArray(r.items) || r.items.length<1 || r.items.length>3 || r.kind!=='address'&&r.items.length!==1 ||
  !r.items.every(item=>item && ['key','label','source','title','interpretation','focus'].every(k=>text(item[k])) &&
   numbers.includes(item.number) && item.narration_id===`tool-${r.kind}-${item.number}` && Number.isInteger(item.total)&&item.total>0&&
   Array.isArray(item.steps)&&item.steps.length>0&&item.steps.every(text)&&
   Array.isArray(item.tokens)&&item.tokens.length>0&&item.tokens.length<=240&&item.tokens.every(t=>t&&text(t.symbol)&&t.symbol.length===1&&Number.isInteger(t.value)&&t.value>=0&&t.value<=9)&&
   item.total===item.tokens.reduce((sum,t)=>sum+t.value,0)))fail();
 return value;
}
function validateDraft(draft){
 if(!draft || !kinds.includes(draft.kind) || !draft.inputs)return 'Выберите вид расчёта и заполните поля.';
 const fields=draft.inputs,values=Object.values(fields);
 if(values.some(v=>typeof v!=='string'||v.trim().length>120||/[\x00-\x1f]/.test(v)))return 'Проверьте длину и символы полей.';
 const supported=/[A-Za-zА-Яа-яЁё]/;
 if(draft.kind==='name'){
  if(!fields.name?.trim() || ['name','surname'].some(key=>fields[key]?.trim()&&(!/^[A-Za-zА-Яа-яЁё '\-’]+$/.test(fields[key])||!supported.test(fields[key]))))return 'Укажите имя буквами русского или латинского алфавита.';
 }else if(draft.kind==='car'){
  if(!fields.car_number?.trim() || fields.car_number.trim().length>13 || !/^[A-Za-zА-Яа-яЁё0-9 -]+$/.test(fields.car_number) || !/[A-Za-zА-Яа-яЁё1-9]/.test(fields.car_number))return 'Укажите номер до 13 символов: буквы и цифры.';
 }else{
  if(!fields.house_number?.trim() || ['house_number','apartment_number','postal_code'].some(key=>fields[key]?.trim()&&(!/^[A-Za-zА-Яа-яЁё0-9 /-]{1,24}$/.test(fields[key].trim())||!/[1-9]/.test(fields[key]))))return 'Номер дома, квартиры и индекс должны содержать ненулевую цифру.';
 }
 return '';
}
function createToolController(options){
 return require('./paid-calculations').createPaidCalculationController(options,{parseCatalog:toolCatalog,parseReceipt:toolReceipt,validateDraft});
}
module.exports={toolCatalog,toolReceipt,createToolController};
