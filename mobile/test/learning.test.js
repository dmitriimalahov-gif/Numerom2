const {test}=require('node:test');
const assert=require('node:assert/strict');
const {lessonExercises,lessonQuiz,lessonFiles,exerciseResponses,quizResult,quizAttempts,lessonProgress,quizPayload,exercisePayload,safeLearningUrl,submissionId,singleFlight,quizSubmission,plainText}=require('../src/lib/learning');
const fixture={id:'lesson-1',quiz:{id:'quiz-1',title:'Основы',passing_score:70,questions:[{id:'q1',question:'Выберите число',type:'multiple_choice',options:['Один','Два'],correct_answer:'Два'},{id:'q2',question:'Ваше объяснение',type:'text',correct_answer:'Внутренняя проверка'}]},exercises:[{id:'exercise-1',title:'Практика',type:'text',instructions:['Прочитайте','Ответьте']}]};
const requestId='24c54778-9145-4241-a163-925bff508025';
test('quiz payload contains only actual answers and idempotency identity, never grades or rewards',()=>{
 const quiz=lessonQuiz(fixture);
 assert.deepEqual(quizPayload('lesson-1',quiz,{q1:'Два',q2:'Объяснение',foreign:'ignore'},requestId),{lesson_id:'lesson-1',quiz_id:'quiz-1',answers:{q1:'Два',q2:'Объяснение'},submission_id:requestId});
 assert.equal('correct_answer' in quiz.questions[0],false);
 assert.equal(JSON.stringify(quiz).includes('Внутренняя проверка'),false);
});
test('missing, forged or oversized quiz answers cannot be submitted',()=>{
 const quiz=lessonQuiz(fixture);
 for(const answers of [{q1:'Два'},{q1:'Подменённый вариант',q2:'Ответ'},{q1:'Два',q2:'x'.repeat(4001)}])assert.throws(()=>quizPayload('lesson-1',quiz,answers,requestId));
 assert.throws(()=>quizPayload('lesson-1',quiz,{q1:'Два',q2:'Ответ'},'invalid'));
});
test('unsupported or duplicate question IDs disable the full test instead of silently omitting questions',()=>{
 const quiz=structuredClone(fixture);quiz.quiz.questions[1].id='q1';assert.equal(lessonQuiz(quiz).supported,false);
 quiz.quiz.questions[1].id='q2';quiz.quiz.questions[1].type='file_upload';assert.equal(lessonQuiz(quiz).supported,false);
});
test('both published lesson schemas retain exercises and exact answer options',()=>{
 const [exercise]=lessonExercises(fixture);
 assert.equal(exercise.instructions,'Прочитайте\nОтветьте');
 assert.deepEqual(exercisePayload('lesson-1',exercise,'  Текст ответа  '),{lesson_id:'lesson-1',exercise_id:'exercise-1',response_text:'Текст ответа'});
 assert.equal(lessonExercises({id:'l',content:{exercises:fixture.exercises}}).length,1);
 assert.throws(()=>exercisePayload('lesson-1',exercise,'  '));
 assert.throws(()=>exercisePayload('lesson-1',exercise,'x'.repeat(10001)));
 assert.throws(()=>exercisePayload('lesson-1',{...exercise,type:'multiple_choice',options:['A','B']},'C'));
});
test('only server-confirmed results can appear as a saved quiz result',()=>{
 assert.deepEqual(quizResult({attempt_id:'a',score:0,passed:false}),{id:'a',score:0,passed:false,attemptedAt:'',submissionId:''});
 for(const value of [{score:100,passed:true},{id:'a',score:100},{id:'a',score:Infinity,passed:true},{id:'a',score:150,passed:true},null])assert.throws(()=>quizResult(value));
 assert.throws(()=>quizAttempts({}));
 assert.deepEqual(quizAttempts({attempts:[]}),[]);
});
test('unavailable progress is not fabricated as zero or complete',()=>{
 assert.throws(()=>lessonProgress({}));assert.throws(()=>lessonProgress({completion_percentage:NaN}));
 assert.equal(lessonProgress({completion_percentage:0}).percentage,0);
 assert.equal(lessonProgress({completion_percentage:100,is_completed:false}).completed,false);
});
test('review state is based on the server receipt, not positive points or a local text draft',()=>{
 const saved=exerciseResponses({exercise_responses:{a:{id:'r',response_text:'Ответ',reviewed:true,admin_comment:'Уточните вывод',points_earned:0}}});
 assert.deepEqual(saved.a,{attachments:[],id:'r',text:'Ответ',reviewed:true,comment:'Уточните вывод',submittedAt:''});
 assert.throws(()=>exerciseResponses({exercise_responses:[]}));
});
test('material names support both schemas without exposing storage paths',()=>{
 const result=lessonFiles({files:[{id:'f1',original_name:'Метод.pdf',stored_name:'private-name.pdf',mime_type:'application/pdf',file_size:0},{id:'f2',original_filename:'Видео.mp4',file_type:'video'}]});
 assert.equal(result[0].name,'Метод.pdf');assert.equal(result[0].size,0);assert.equal(result[1].name,'Видео.mp4');assert.equal('stored_name' in result[0],false);assert.throws(()=>lessonFiles({}));
});
test('opening media rejects executable, local, credentialed and relative URLs',()=>{
 for(const url of ['javascript:alert(1)','file:///private/file','data:text/html,x','http://localhost:8000/uploads/a','//attacker.invalid/file','https://user:pass@example.invalid/a'])assert.throws(()=>safeLearningUrl(url));
 assert.equal(safeLearningUrl('https://media.example.invalid/a?file_token=scoped'),'https://media.example.invalid/a?file_token=scoped');
});
test('a rapid double tap shares one pending request and a failure can be retried',async()=>{
 const run=singleFlight();let calls=0,release;
 const first=run(()=>{calls++;return new Promise(resolve=>{release=resolve;});});
 const second=run(()=>{calls++;return Promise.resolve('wrong');});
 assert.equal(first,second);await Promise.resolve();assert.equal(calls,1);release('saved');assert.equal(await first,'saved');
 await assert.rejects(run(()=>Promise.reject(new Error('offline'))),/offline/);
 assert.equal(await run(()=>Promise.resolve('retry')),'retry');
});
test('submission identities are UUID v4 and a retained payload is stable across retries',()=>{
 const one=submissionId(),two=submissionId();assert.notEqual(one,two);
 const payload=quizPayload('lesson-1',lessonQuiz(fixture),{q1:'Два',q2:'Ответ'},one);
 assert.match(payload.submission_id,/^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i);
 assert.equal(JSON.parse(JSON.stringify(payload)).submission_id,one);
});
test('lesson markup is rendered as text and script/style content is removed',()=>{
 assert.equal(plainText('<p>Смысл &amp; практика</p><script>secret()</script><style>x{}</style>'),'Смысл & практика');
});

test('a lost quiz response retries the identical submission and answers even if the caller edits its draft',async()=>{
 const state=quizSubmission(),sent=[];
 const api={request:async(path,options)=>{sent.push({path,body:structuredClone(options.body)});if(sent.length===1)throw new Error('connection lost after server saved');return {attempt_id:'saved-attempt',score:50,passed:false};}};
 await assert.rejects(state.submit(api,'lesson-1',lessonQuiz(fixture),{q1:'Два',q2:'Первый ответ'}));
 assert.equal(state.hasPending(),true);
 const result=await state.submit(api,'lesson-1',lessonQuiz(fixture),{q1:'Один',q2:'Изменённый ответ'});
 assert.deepEqual(sent[1],sent[0]);assert.equal(result.id,'saved-attempt');assert.equal(state.hasPending(),false);
});
test('quiz validation rejection permits correction while malformed success retains a retryable attempt',async()=>{
 const state=quizSubmission(),quiz=lessonQuiz(fixture),answers={q1:'Два',q2:'Ответ'};
 await assert.rejects(state.submit({request:async()=>{throw Object.assign(new Error('invalid'),{status:422});}},'lesson-1',quiz,answers));
 assert.equal(state.hasPending(),false);
 await assert.rejects(state.submit({request:async()=>({message:'ok'})},'lesson-1',quiz,answers));
 assert.equal(state.hasPending(),true);
});

test('only submitted attachment identities survive the learning response adapter',()=>{
 const key='a'.repeat(64);
 const receipt=exerciseResponses({exercise_responses:{ex:{id:'r',response_text:'Ответ',attachment_ids:[key,'../../private'],attachment_files:[{stored:'private-path'}]}}});
 assert.deepEqual(receipt.ex.attachments,[key]);assert.equal(receipt.ex.attachment_files,undefined);
});
