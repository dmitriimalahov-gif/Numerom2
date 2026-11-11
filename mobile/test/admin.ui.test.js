const test=require('node:test'),assert=require('node:assert/strict');
const {setup,deferred,ApiError,plain}=require('./adminHarness');
const response={id:'answer-1',revision:4,user_id:'student',lesson_id:'lesson',exercise_id:'exercise',response_text:'Мой ответ',reviewed:false,expected_answer:'snapshot',points_earned:0,student_name:'Анна'};
const report={id:'a'.repeat(64),revision:3};
const preview={fingerprint:'f'.repeat(64),warnings:['Тест добавляется в редакторе'],lesson:{title:'Четвёрка',level:1,order:1,theory:[{title:'Теория',content:'Полный исходный текст'}],exercises:[]}};

test('admin route blocks ordinary users and locked sessions without private requests',async()=>{
 for(const options of [{actor:{is_admin:false}},{status:'locked'}]){const f=await setup('app/admin.tsx',options);try{assert.match(f.text,/доступен администраторам/);assert.equal(f.calls.length,0);}finally{await f.close();}}
});
test('overview exposes mail configuration and all nine mobile sections',async()=>{
 const f=await setup('app/admin.tsx',{handler:url=>url.endsWith('recovery-status')?{configured:false}:{users_total:12}});try{assert.match(f.text,/Отправка писем пока не настроена/);await f.click(/Разделы управления/);for(const title of ['Пользователи','Уроки','Ответы','Дневники','Аналитика','Консультации','Отчёты','Настройки'])assert.ok(f.button(title));await f.actor({is_admin:false});assert.match(f.text,/доступен администраторам/);assert.doesNotMatch(f.text,/Отправка писем/);}finally{await f.close();}
});
test('review validates rewards, requires feedback and retries the identical request after a network loss',async()=>{
 let saves=0;const f=await setup('features/admin/Reviews.tsx',{exportName:'ReviewEditor',props:{item:response,onSaved:async()=>saves++},handler:()=>{throw Error('Связь прервалась');}});try{
  await f.click('Сохранить проверку');assert.equal(f.writes.length,0);assert.match(f.text,/Напишите обратную связь/);
  await f.fill('Обратная связь ученику','Хорошо разобран пример');await f.fill(/Баллы за проверку/,'101');await f.click('Сохранить проверку');assert.equal(f.writes.length,0);assert.match(f.text,/от 0 до 100/);
  await f.fill(/Баллы за проверку/,'25');await f.click('Сохранить проверку');assert.equal(f.writes.length,1);assert.equal(f.field('Обратная связь ученику').disabled,true);
  const body=plain(f.writes[0].request.body);assert.equal(body.points_earned,25);assert.equal(body.expected_answer,'snapshot');assert.equal(body.revision,4);assert.match(body.request_id,/^00000000-0000-4000-8000-/);
  f.setHandler(()=>({points_awarded:25}));await f.click('Проверить сохранение');assert.deepEqual(plain(f.writes[1].request.body),body);assert.equal(saves,1);
 }finally{await f.close();}
});
test('review conflict cannot overwrite until the latest record is loaded',async()=>{
 let reloads=0;const f=await setup('features/admin/Reviews.tsx',{exportName:'ReviewEditor',props:{item:response,onSaved:async()=>reloads++},handler:()=>{throw new ApiError('Ответ уже проверен',409);}});try{await f.fill('Обратная связь ученику','Комментарий');await f.click('Сохранить проверку');assert.equal(f.button('Сохранить проверку').disabled,true);assert.equal(f.button('Проверить сохранение'),undefined);await f.click('Отбросить правку и загрузить актуальное');assert.equal(reloads,1);assert.equal(f.writes.length,1);}finally{await f.close();}
});
test('an old administrator response and new account cannot trigger a mutation callback',async()=>{
 const waiting=deferred();let saved=0;const f=await setup('features/admin/Reviews.tsx',{exportName:'ReviewEditor',props:{item:response,onSaved:async()=>saved++},handler:()=>waiting.promise});try{await f.fill('Обратная связь ученику','Комментарий');await f.click('Сохранить проверку');await f.actor({id:'another-admin'},{commit:false});await f.flush(()=>waiting.resolve({}));assert.equal(saved,0);}finally{await f.close();}
});
test('search switches pages and ignores the older response',async()=>{
 const waiting=deferred();const f=await setup('features/admin/Reviews.tsx',{handler:url=>url.includes('q=%D0%90%D0%BD%D0%BD%D0%B0')?{responses:[{...response,response_text:'Свежий ответ'}],total:1,page:1,page_size:25}:waiting.promise});try{await f.fill('Поиск по ученику или ответу','Анна');await f.click('Найти');assert.match(f.text,/Свежий ответ/);await f.flush(()=>waiting.resolve({responses:[{...response,response_text:'Старый ответ'}],total:1,page:1,page_size:25}));assert.doesNotMatch(f.text,/Старый ответ/);assert.match(f.calls[1].url,/reviewed=pending/);}finally{await f.close();}
});
test('settings use server labels, numeric bounds, decimal commas and booleans',async()=>{
 const value={revision:7,values:{weight:0.5,enabled:false,count:2,unknown:999},fields:{weight:{type:'number',min:0,max:1,label:'Вес личного дня'},enabled:{type:'boolean',label:'Учитывать день'},count:{type:'integer',min:1,max:10,label:'Дней в периоде'}}};let saved=0;
 const f=await setup('features/admin/Settings.tsx',{exportName:'SettingsForm',props:{kind:'planetary-energy',value,reload:async()=>saved++}});try{assert.doesNotMatch(f.text,/unknown|weight/);await f.fill('Причина изменения','Уточнение модели');await f.fill('Вес личного дня','1,1');await f.click('Сохранить настройки');assert.equal(f.writes.length,0);await f.fill('Вес личного дня','0,75');await f.click('Учитывать деньНет');await f.click('Сохранить настройки');assert.deepEqual(plain(f.writes[0].request.body.values),{weight:0.75,enabled:true,count:2});assert.equal(saved,1);}finally{await f.close();}
});
test('settings provide all five groups and reload a conflict into a fresh editor',async()=>{
 let conflict=true;const value={revision:1,values:{cost:1},fields:{cost:{type:'integer',min:0,max:100,label:'Стоимость расчёта'}}};
 const f=await setup('features/admin/Settings.tsx',{handler:(url,req)=>{if(req.method)throw new ApiError('Изменено другим администратором',409);return {...value,revision:conflict?1:2};}});try{for(const title of ['Награды за обучение','Стоимость функций','Telegram Stars','Динамика планет','Маршрут на месяц'])assert.ok(f.button(title));await f.fill('Причина изменения','Причина');await f.click('Сохранить настройки');assert.equal(f.button('Сохранить настройки').disabled,true);conflict=false;await f.click('Отбросить правку и загрузить актуальное');assert.equal(f.button('Сохранить настройки').disabled,false);assert.equal(f.field('Причина изменения').value,'');}finally{await f.close();}
});
test('Stars editor saves integer prices, permits disabling and explains existing invoices',async()=>{
 const value={revision:3,values:{one_time:10,full_report:40},fields:{one_time:{type:'integer',min:0,max:100000,label:'Стартовый пакет · 10 баллов'},full_report:{type:'integer',min:0,max:100000,label:'Полный персональный разбор'}}};
 const f=await setup('features/admin/Settings.tsx',{exportName:'SettingsForm',props:{kind:'telegram-stars',value,reload:async()=>{}}});try{assert.match(f.text,/0 — отключить новые покупки/);assert.match(f.text,/счета сохраняют прежнюю сумму/);await f.fill('Причина изменения','Новые цены');await f.fill(/Полный персональный разбор/,'25,5');await f.click('Сохранить настройки');assert.equal(f.writes.length,0);await f.fill(/Полный персональный разбор/,'75');await f.fill(/Стартовый пакет · 10 баллов/,'0');await f.click('Сохранить настройки');assert.equal(f.writes[0].url,'/admin/mobile/settings/telegram-stars');assert.deepEqual(plain(f.writes[0].request.body.values),{one_time:0,full_report:75});assert.equal(f.writes[0].request.body.revision,3);}finally{await f.close();}
});
test('TXT preview does not create a lesson, changed text invalidates preview, confirm preserves exact text',async()=>{
 const f=await setup('features/admin/ImportLesson.tsx',{props:{onSaved:async()=>{}},handler:url=>url.endsWith('/preview')?preview:{id:'lesson'}});try{const text='Четвёрка\n\nАвторский текст.';await f.fill('Текст урока',text);await f.click('Подготовить предварительный разбор');assert.equal(f.writes.filter(c=>!c.url.endsWith('/preview')).length,0);assert.match(f.text,/Полный исходный текст/);await f.fill('Текст урока',text+' Дополнение.');assert.equal(f.button('Подтвердить и создать черновик'),undefined);await f.click('Подготовить предварительный разбор');await f.click('Подтвердить и создать черновик');assert.equal(f.writes.length,2);await f.fill('Причина изменения','Добавление авторского урока');await f.click('Подтвердить и создать черновик');const saved=f.writes[2];assert.equal(saved.url,'/admin/mobile/lessons/import');assert.equal(saved.request.body.text,text+' Дополнение.');assert.equal(saved.request.body.fingerprint,preview.fingerprint);assert.equal(saved.request.body.revision,0);}finally{await f.close();}
});
test('late TXT preview and file reads cannot expose data after account switch or text change',async()=>{
 const waiting=deferred();const f=await setup('features/admin/ImportLesson.tsx',{props:{onSaved:async()=>{}},handler:()=>waiting.promise});try{await f.fill('Текст урока','Первый урок');await f.click('Подготовить предварительный разбор');await f.fill('Текст урока','Другой урок');await f.flush(()=>waiting.resolve(preview));assert.equal(f.button('Подтвердить и создать черновик'),undefined);
 const pick=deferred();f.setPicker(()=>pick.promise);await f.click('Выбрать TXT');await f.actor({id:'other'},{commit:false});await f.flush(()=>pick.resolve({canceled:false,assets:[{name:'lesson.txt',size:12,uri:'file:///example'}]}));assert.equal(f.field('Текст урока').value,'Другой урок');}finally{await f.close();}
});
test('TXT rejects oversized files before reading or sending content',async()=>{
 const f=await setup('features/admin/ImportLesson.tsx',{props:{onSaved:async()=>{}},picker:()=>({canceled:false,assets:[{name:'large.txt',size:2*1024*1024,uri:'file:///large'}]})});try{await f.click('Выбрать TXT');assert.match(f.text,/не должен превышать 1 МБ/);assert.equal(f.writes.length,0);}finally{await f.close();}
});
test('archive requires explicit confirmation and a reason, and sends no delete',async()=>{
 const f=await setup('features/admin/Archive.tsx',{props:{kind:'lessons',id:'lesson',revision:8,reload:async()=>{}}});try{await f.click('Перенести в архив');assert.equal(f.writes.length,0);await f.click('Подтвердить архивирование');assert.equal(f.writes.length,0);await f.fill('Причина изменения','Заменён новым уроком');await f.click('Подтвердить архивирование');assert.equal(f.writes[0].url,'/admin/mobile/lessons/lesson/archive');assert.equal(f.writes[0].request.method,'POST');assert.equal(f.writes[0].request.body.revision,8);}finally{await f.close();}
});
test('archived lessons are read-only, keep the theory and have no material mutation controls',async()=>{
 const f=await setup('features/admin/Content.tsx',{exportName:'Lessons',handler:()=>({lessons:[{id:'lesson',revision:2,title:'Сохранённый урок',level:1,order:1,is_archived:true,is_active:false,theory:[{id:'part',title:'Часть',content:'Исходная теория'}]}],total:1,page:1,page_size:20})});try{await f.click('Просмотреть: Сохранённый урок');assert.match(f.text,/Исходная теория/);assert.equal(f.button('Сохранить урок'),undefined);assert.equal(f.button('Перенести в архив'),undefined);assert.equal(f.writes.length,0);}finally{await f.close();}
});
test('report retry uses expected revision and the same UUID after rate limiting, without another charge',async()=>{
 let attempt=0;const f=await setup('features/admin/Reports.tsx',{exportName:'ReportRetry',props:{item:report,reload:async()=>{}},handler:()=>{if(!attempt++)throw new ApiError('Подождите минуту',429);return {queued:true};}});try{await f.click('Подтвердить повтор подготовки');assert.equal(f.writes.length,0);await f.fill('Причина изменения','Повтор после остановки сервера');await f.click('Подтвердить повтор подготовки');assert.match(f.text,/Подождите минуту/);await f.click('Проверить сохранение');assert.deepEqual(plain(f.writes[0].request.body),plain(f.writes[1].request.body));assert.equal(f.writes[0].request.body.expected_revision,3);assert.equal(f.writes[0].request.body.revision,undefined);assert.ok(f.writes.every(c=>c.url===`/admin/mobile/reports/${report.id}/retry`));}finally{await f.close();}
});
test('challenge notes show real day text and analytics expose pending reviews',async()=>{
 const f=await setup('features/admin/Analytics.tsx',{exportName:'ChallengeNotes',handler:()=>({notes:[{id:'note',student_name:'Анна',lesson_title:'Урок 4',attempt_number:2,is_completed:false,completed_days:[1],daily_notes:[{day:1,note:'Мой вывод',updated_at:null}]}],total:1,page:1,page_size:25})});try{await f.click('Читать заметки');assert.match(f.text,/День 1Мой вывод/);assert.equal(f.writes.length,0);}finally{await f.close();}
 const a=await setup('features/admin/Analytics.tsx',{exportName:'Analytics',handler:()=>({summary:{pending_reviews:4},lessons:[]})});try{assert.match(a.text,/Ожидают проверки: 4/);}finally{await a.close();}
});

test('saved review with pending award remains recoverable with exactly the same request',async()=>{
 let awards=0,saves=0;const f=await setup('features/admin/Reviews.tsx',{exportName:'ReviewEditor',props:{item:response,onSaved:async()=>saves++},handler:()=>({award_pending:awards++===0})});try{await f.fill('Обратная связь ученику','Проверено');await f.fill(/Баллы за проверку/,'40');await f.click('Сохранить проверку');assert.match(f.text,/Проверка сохранена. Начисление баллов ожидает/);assert.equal(saves,0);await f.click('Проверить сохранение');assert.deepEqual(plain(f.writes[0].request.body),plain(f.writes[1].request.body));assert.equal(saves,1);}finally{await f.close();}
});
test('a late private list is discarded when administrator privileges disappear',async()=>{
 const waiting=deferred(),f=await setup('features/admin/Reviews.tsx',{handler:()=>waiting.promise});try{await f.actor({is_admin:false},{commit:false});await f.flush(()=>waiting.resolve({responses:[{...response,response_text:'Приватный текст'}],total:1,page:1,page_size:25}));assert.doesNotMatch(f.text,/Приватный текст/);}finally{await f.close();}
});
test('review attachments never open after unmount or after an account change',async()=>{
 for(const boundary of ['unmount','account']){const waiting=deferred(),f=await setup('features/admin/Reviews.tsx',{exportName:'ReviewEditor',props:{item:{...response,attachments:[{id:'file',name:'Ответ.pdf'}]},onSaved:async()=>{}},handler:()=>waiting.promise});try{await f.click('Открыть Ответ.pdf');if(boundary==='unmount')await f.unmount();else await f.actor({id:'other'},{commit:false});await f.flush(()=>waiting.resolve({url:'https://api.example.test/api/student/exercise-attachment-media/token'}));assert.deepEqual(f.links,[]);}finally{await f.close();}}
});
test('list pagination searches on the server and archived consultations cannot be edited',async()=>{
 const item={id:'consultation',revision:2,title:'Разбор',cost_credits:100,is_archived:true,is_active:false,description:'Сохранённая консультация'};
 const f=await setup('features/admin/Content.tsx',{exportName:'Consultations',handler:url=>({consultations:[item],total:41,page:url.includes('page=2')?2:1,page_size:20})});try{await f.click('Следующая страница');assert.match(f.calls.at(-1).url,/page=2/);await f.fill('Поиск консультаций','Разбор');await f.click('Найти');assert.match(f.calls.at(-1).url,/page=1/);assert.match(f.calls.at(-1).url,/q=%D0%A0%D0%B0%D0%B7%D0%B1%D0%BE%D1%80/);await f.click('Просмотреть: Разбор');assert.match(f.text,/Сохранённая консультация/);assert.equal(f.button('Сохранить консультацию'),undefined);}finally{await f.close();}
});
