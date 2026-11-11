const fail = () => { throw Error('Сервер вернул неполный расчёт совместимости. Обновите историю.'); };
const text = value => typeof value === 'string' && value.length > 0;
const price = value => Number.isInteger(value) && value >= 0 && value <= 1000000;
function relationshipCatalog(value) {
  if (!value || !['pair','group'].every(key => value[key] === null || price(value[key]))) fail();
  return {pair:value.pair, group:value.group};
}
function relationshipReceipt(value) {
  const r=value?.results;
  const member=p=>p && text(p.name) && text(p.birth_date) && [1,2,3,4,5,6,7,8,9,11,22,33].includes(p.number) && Array.isArray(p.steps) && p.steps.every(text);
  if (!value || !text(value.id) || !text(value.request_id) || !price(value.cost) || !Number.isFinite(Date.parse(value.created_at)) ||
      !r || r.version!==1 || !['pair','group'].includes(r.kind) || !member(r.main) || !Array.isArray(r.people) ||
      r.people.length<1 || r.people.length>5 || r.kind==='pair'&&r.people.length!==1 || !r.people.every(member) ||
      !Array.isArray(r.connections) || r.connections.length!==r.people.length || !r.connections.every(c=>
        c && Number.isInteger(c.score) && c.score>=1 && c.score<=10 && ['name','title','interpretation','focus','formula'].every(k=>text(c[k]))) ||
      typeof r.average!=='number' || !Number.isFinite(r.average) || r.average<1 || r.average>10 || !text(r.method) || !text(r.note)) fail();
  return value;
}
function validateDraft(draft) {
 const {validateBirthDate}=require('./index');
 const members=[draft.main,...(draft.people || [])];
 if(!['pair','group'].includes(draft.kind) || members.length<2 || members.length>6 || draft.kind==='pair'&&members.length!==2 ||
   members.some(p=>!p || !text(p.name?.trim()) || p.name.trim().length>80 || !validateBirthDate(p.birth_date)))return 'Укажите имена и существующие даты: ДД.ММ.ГГГГ.';
 return '';
}
function createRelationshipController(options) {
 return require('./paid-calculations').createPaidCalculationController(options,{parseCatalog:relationshipCatalog,parseReceipt:relationshipReceipt,validateDraft});
}
module.exports={relationshipReceipt,relationshipCatalog,createRelationshipController};
