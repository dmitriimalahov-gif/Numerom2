const {createPaidCalculationController}=require('../../../packages/api-client/paid-calculations');
const fail=()=>{throw Error('Не удалось прочитать опрос. Обновите страницу.');};
function assessmentCatalog(value){
 if(!value||!(value.assessment===null||Number.isInteger(value.assessment)&&value.assessment>=0&&value.assessment<=1000000)||!Array.isArray(value.questions)||value.questions.length!==10)fail();
 const ids=new Set();
 for(const q of value.questions){
  if(!q||! /^(?:[1-9]|10)$/.test(q.id)||ids.has(q.id)||typeof q.question!=='string'||!Array.isArray(q.options)||q.options.length!==9)fail();ids.add(q.id);
  if(new Set(q.options.map(o=>o.id)).size!==9||q.options.some(o=>!o||! /^[a-f0-9]{20}$/.test(o.id)||typeof o.text!=='string'))fail();
 }
 return {assessment:value.assessment,title:value.title,description:value.description,questions:value.questions};
}
function assessmentReceipt(value){
 const r=value?.results;
 if(!value||! /^[a-f0-9]{64}$/.test(value.id)||typeof value.request_id!=='string'||!Number.isFinite(Date.parse(value.created_at))||!Number.isInteger(value.cost)||value.cost<0||!r||r.version!==1||r.kind!=='assessment'||!Number.isInteger(r.number)||r.number<1||r.number>9||typeof r.interpretation!=='string'||typeof r.focus!=='string'||r.narration_id!==`assessment-result-${r.number}`)fail();
 if(!Array.isArray(r.frequencies)||r.frequencies.length!==9||r.frequencies.some((f,i)=>f.number!==i+1||!Number.isInteger(f.count)||f.count<0||f.count>10)||r.frequencies.reduce((s,f)=>s+f.count,0)!==10||!Array.isArray(r.answers)||r.answers.length!==10)fail();
 if(!Array.isArray(r.leaders)||!r.leaders.includes(r.number)||r.leaders.some(n=>!Number.isInteger(n)||n<1||n>9)||typeof r.theme!=='string'||typeof r.method!=='string'||!Number.isInteger(r.total))fail();
 for(const a of r.answers)if(typeof a.question!=='string'||typeof a.answer!=='string'||!Number.isInteger(a.number)||a.number<1||a.number>9)fail();
 return value;
}
function validateDraft(draft){
 if(draft?.kind!=='assessment'||!draft.answers||typeof draft.answers!=='object'||Array.isArray(draft.answers)||Object.keys(draft.answers).length!==10||Object.entries(draft.answers).some(([k,v])=>! /^(?:[1-9]|10)$/.test(k)||typeof v!=='string'||! /^[a-f0-9]{20}$/.test(v)))return 'Ответьте на все десять вопросов.';
 return '';
}
function createAssessmentController(options){return createPaidCalculationController(options,{parseCatalog:assessmentCatalog,parseReceipt:assessmentReceipt,validateDraft});}
module.exports={assessmentCatalog,assessmentReceipt,createAssessmentController};
