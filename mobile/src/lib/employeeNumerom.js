const {numberKnowledge}=require('./numberKnowledge');
const {numberReflection}=require('./reflectionKnowledge');

const note='Трактовки NumerOM описывают символические сильные стороны для самопознания. Рабочие навыки подтверждаются опытом; эти числа не определяют должность или состав команды.';
const contexts={soul:'Внутренняя мотивация и привычные стремления.',mind:'Способ осмысления информации и принятия решений.',destiny:'Общая тема пути и личного развития.',name:'Самовыражение через имя и фамилию.'};
// The same two alphabets, Ё position and master-number rule as domain/number_tools.py.
const alphabets=['ABCDEFGHIJKLMNOPQRSTUVWXYZ','АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'];
const letters=Object.fromEntries(alphabets.flatMap(alphabet=>[...alphabet].map((letter,index)=>[letter,index%9+1])));
const nameMethod='Метод раздела «Имя, адрес и автомобиль»: отдельные циклы 1–9 для русского и латинского алфавитов; Ё = 7. Пробелы, дефисы и апострофы не учитываются. Мастер-числа 11, 22 и 33 сохраняются.';
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function reduce(value,masters=[]){
 const steps=[];
 while(value>9&&!masters.includes(value)){const digits=[...String(value)].map(Number);value=digits.reduce((a,b)=>a+b,0);steps.push(`${digits.join(' + ')} = ${value}`);}
 return {value,steps};
}
function employeeNumerom(identity){
 // Deferred because the portrait validates identity through the business contract.
 const portrait=require('./symbolicPortrait').symbolicPortrait(identity);
 const indicators=portrait.numbers.map(n=>({key:n.key,title:n.title,value:n.value,base:n.base,master:n.master,formula:n.formula,context:contexts[n.key]}));
 const notes=portrait.dateNote?[portrait.dateNote]:[];
 const fullName=`${portrait.name} ${portrait.surname}`;
 if(/^[A-Za-zА-Яа-яЁё '\-’]+$/.test(fullName)&&[portrait.name,portrait.surname].every(part=>/[A-Za-zА-Яа-яЁё]/.test(part))){
  const tokens=[...fullName.toUpperCase()].filter(c=>letters[c]).map(c=>({letter:c,value:letters[c]}));
  const total=tokens.reduce((sum,t)=>sum+t.value,0),reduced=reduce(total,[11,22,33]);
  indicators.push({key:'name',title:'Число имени и фамилии',value:reduced.value,base:reduce(reduced.value).value,master:reduced.value>9,
   formula:[tokens.map(t=>`${t.letter}(${t.value})`).join(' + ')+` = ${total}`,...reduced.steps].join(' → '),context:contexts.name});
 }else notes.push('Число имени пока недоступно: метод поддерживает русские и латинские буквы. Написание не заменяется автоматически.');
 const themes=[...new Set(indicators.map(n=>n.base))].map(digit=>{
  const knowledge=numberKnowledge(digit),reflection=numberReflection(digit);
  return {digit,planet:knowledge.planet,title:knowledge.title,summary:knowledge.summary,
   strength:knowledge.segments[1],practice:reflection.practice,question:reflection.questions[0],
   indicators:indicators.filter(n=>n.base===digit).map(n=>`${n.title} ${n.value}${n.master?` (база ${n.base})`:''}`),
   sources:reflection.sources.map(source=>`${source.title} — ${source.locator}`)};
 });
 return {version:1,birthDate:portrait.birthDate,note,nameMethod,indicators,themes,notes};
}
function employeeNumeromHtml(result,{compact=false}={}){
 const e=esc;
 const indicators=result.indicators.map(n=>`<tr><td><strong>${e(n.title)}</strong><br>${e(n.context)}</td><td><strong>${n.value}</strong>${n.master?`<br>Мастер-число · база ${n.base}`:''}</td><td>${e(n.formula)}</td></tr>`).join('');
 const themes=result.themes.map(t=>`<section class="numerom-theme"><h5>${t.digit} · ${e(t.planet)} · ${e(t.title)}</h5><p><strong>${e(t.summary)}</strong><br><span class="muted">${e(t.indicators.join('; '))}</span></p>${compact?'':`<p>${e(t.strength)}</p><p><strong>Вопрос к своему опыту:</strong> ${e(t.question)}</p>`}<p><strong>Практика:</strong> ${e(t.practice)}</p>${compact?'':`<p class="muted">Источник: ${e(t.sources.join('; '))}.</p>`}</section>`).join('');
 return `<section class="employee-numerom"><h3>Ключевые показатели NumerOM</h3><p class="muted">${e(result.note)}</p>${indicators?`<table style="width:100%;border-collapse:collapse;table-layout:fixed"><thead><tr><th>Показатель</th><th style="width:90px">Число</th><th>Как рассчитано</th></tr></thead><tbody>${indicators}</tbody></table>`:''}${result.indicators.some(n=>n.key==='name')?`<p class="muted">${e(result.nameMethod)}</p>`:''}${result.notes.map(n=>`<p>${e(n)}</p>`).join('')}<h4>Сильные стороны в символике чисел</h4>${themes||'<p>Добавьте дату рождения или имя в поддерживаемом алфавите.</p>'}</section>`;
}
module.exports={employeeNumerom,employeeNumeromHtml};
