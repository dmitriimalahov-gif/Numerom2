const {createPaidCalculationController}=require('@numerom/api-client/paid-calculations');
const {savedPersonalResult}=require('./personalReport');
const {validateBirthDate}=require('@numerom/api-client');
function parseReceipt(raw){
 const birth_date=raw?.birth_date||raw?.results?.report?.birth_date;
 const view=savedPersonalResult({calculation:{...raw,birth_date}});
 if(!view)throw Error('Результат не получен.');
 return {...raw,birth_date,view};
}
function createPersonalPaidController(options){
 return createPaidCalculationController(options,{historyLimit:100,parseReceipt,
  parseCatalog:value=>{if(!Number.isInteger(value?.personal)||value.personal<0)throw Error('Стоимость не получена.');return value;},
  validateDraft:body=>body.kind!=='personal'||!validateBirthDate(body.birth_date)?'Введите существующую дату рождения: ДД.ММ.ГГГГ.':''});
}
module.exports={createPersonalPaidController,parseReceipt};
