const {nameSchemes}=require('../../../packages/numerology-core/name-schemes');
const core=require('../../../packages/numerology-core/comprehensive');
const knowledge=require('../../../packages/comprehensive-knowledge/ru.json');
const {serverDate}=require('./serverDate');
function comprehensiveReport(result){
 const birth=result?.report?.birthDate,m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(birth||''),stamp=serverDate(result?.createdAt);
 if(!m||!stamp)return null;
 const [day,month,year]=m.slice(1).map(Number),date=new Date(Date.UTC(year,month-1,day));
 if(date.getUTCFullYear()!==year||date.getUTCMonth()+1!==month||date.getUTCDate()!==day)return null;
 const fractal=core.calculateBehaviorFractal(birth);if(!fractal)return null;
 const base=Object.fromEntries(result.report.numbers.map(item=>[item.key,item.value]));
 // Tasks use actual saved personal values; never invent absent soul/mind/destiny numbers.
 const tasks=core.calculateTaskNumbers(base.soul,base.mind,base.destiny,fractal.digit3);
 const stampISO=stamp.toISOString().slice(0,10),target=new Date(stamp.getUTCFullYear(),stamp.getUTCMonth(),stamp.getUTCDate(),12);
 const individual=core.calculateIndividualNumbers(birth,target,base.destiny);
 const cycles=core.calculateShadowsPeaksChallenges(birth);
 return {birthDate:birth,targetDate:stampISO,fractal,tasks,individual,cycles,nameSchemes:nameSchemes(result.report.profileParts,birth),knowledge:knowledge.items};
}
module.exports={comprehensiveReport};
