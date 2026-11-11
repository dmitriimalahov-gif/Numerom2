const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {JSDOM}=require('jsdom'),React=require('react'),{createRoot}=require('react-dom/client'),ts=require('typescript');
const data=require('../src/lib/business');
const employee={id:'employee-id',name:'Анна',surname:'Тестовая',birth_date:'10.01.1982',department:'',role:'',skills:['Excel'],experience:'Сверила отчёт с исходными продажами.',interests:[],hours_per_week:0};
const workspace={id:'workspace',company_name:'Компания',revision:3,employees:[employee],groups:[{id:'task',name:'Сводка продаж',task:'Подготовить проверяемую сводку',required_skills:['Excel','SQL'],target_hours:null,member_ids:[]}],created_at:'2026-10-18T00:00:00Z',updated_at:'2026-10-18T00:00:00Z'};
async function setup(name,props){
 const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost',pretendToBeVisual:true});global.window=dom.window;global.document=dom.window.document;global.IS_REACT_ACT_ENVIRONMENT=true;
 const fields=new Map(),Box=({children})=>React.createElement('div',null,children);
 const deps={react:React,'react/jsx-runtime':require('react/jsx-runtime'),'react-native':{Text:Box,View:Box},'../ui':{s:{},Card:Box,Notice:({message})=>React.createElement('div',{role:'alert'},message),Field:({label,value,onChangeText})=>{fields.set(label,onChangeText);return React.createElement('input',{'aria-label':label,value,readOnly:true});},Button:({title,onPress,busy,disabled})=>React.createElement('button',{onClick:onPress,disabled:busy||disabled},title)},'../../lib/business':data,'../../lib/theme':{colors:{}}};
 const module={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(__dirname,`../src/components/business/${name}.tsx`),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText,{exports:module.exports,require:key=>{assert.ok(key in deps,key);return deps[key];},Error});
 const root=createRoot(document.getElementById('root'));await React.act(async()=>root.render(React.createElement(module.exports[name],props)));
 const button=label=>Array.from(document.querySelectorAll('button')).find(b=>b.textContent.replace(/\s+/g,' ').trim()===label);
 return {get text(){return document.body.textContent;},async change(label,value){assert.ok(fields.has(label),label);await React.act(async()=>fields.get(label)(value));},async click(label){assert.ok(button(label),label);await React.act(async()=>button(label).click());},button,async close(){await React.act(async()=>root.unmount());dom.window.close();delete global.window;delete global.document;delete global.IS_REACT_ACT_ENVIRONMENT;}};
}
test('saved employee editor validates current edits and explicitly saves before analysis',async()=>{
 let saved=0,calculated=[];const f=await setup('EmployeeEditor',{employee,busy:false,onSave:()=>{saved++;},onCalculate:value=>calculated.push(value),onCancel(){}});
 try{
  assert.ok(f.button('Рассчитать анализ'));await f.change('Рабочие навыки · через точку с запятой','SQL; Excel');await f.change('Опыт и примеры выполненных работ','Создала SQL-запрос и проверила итоги.');
  assert.ok(f.button('Сохранить и рассчитать анализ'));await f.click('Сохранить и рассчитать анализ');
  assert.equal(saved,0);assert.equal(calculated.length,1);assert.deepEqual(calculated[0].skills,['SQL','Excel']);assert.equal(calculated[0].experience,'Создала SQL-запрос и проверила итоги.');assert.equal(calculated[0].hours_per_week,0);
  await f.change('Имя','');await f.click('Сохранить и рассчитать анализ');assert.equal(calculated.length,1);assert.ok(document.querySelector('[role="alert"]'));
 }finally{await f.close();}
});
test('employee analysis displays recorded evidence, zero hours and unconfirmed task requirements',async()=>{
 let edited=0,exported=0,closed=0;const f=await setup('EmployeeAnalysis',{analysis:data.businessEmployeeAnalysis(workspace,employee.id),busy:false,onEdit(){edited++;},onExport(){exported++;},onClose(){closed++;}});
 try{
  assert.match(f.text,/Навыки для проверки/);assert.match(f.text,/Сверила отчёт с исходными продажами/);assert.match(f.text,/0 ч\/нед/);assert.match(f.text,/Где есть совпадения с задачами/);assert.match(f.text,/Требования без сведений в карточкеSQL/);assert.match(f.text,/личный вклад/);assert.match(f.text,/10\.01\.1982/);assert.match(f.text,/Ключевые показатели NumerOM/);assert.match(f.text,/Сильные стороны в символике чисел/);assert.match(f.text,/Число имени и фамилии/);
  await f.click('Дополнить карточку');await f.click('Сохранить анализ / PDF');await f.click('К сотрудникам');assert.deepEqual([edited,exported,closed],[1,1,1]);
 }finally{await f.close();}
});
test('identity-only analysis is explicitly incomplete and can return during an in-flight export',async()=>{
 const analysis=data.businessEmployeeAnalysis({...workspace,employees:[{...employee,skills:[],experience:'',hours_per_week:null}]},employee.id);let closed=0;
 const f=await setup('EmployeeAnalysis',{analysis,busy:true,onEdit(){throw Error('disabled');},onExport(){throw Error('disabled');},onClose(){closed++;}});
 try{
  assert.match(f.text,/Недостаточно рабочих данных/);assert.match(f.text,/Навыки пока не указаны/);assert.match(f.text,/Примеры выполненных работ пока не добавлены/);assert.match(f.text,/Совпадений пока нет/);assert.equal(f.button('Дополнить карточку').disabled,true);assert.equal(f.button('Сохранить анализ / PDF').disabled,true);
  await f.click('К сотрудникам');assert.equal(closed,1);
 }finally{await f.close();}
});
