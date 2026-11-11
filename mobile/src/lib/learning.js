/** Lesson presentation and submission contracts; the server owns grading and rewards. */
const object = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
const list = value => Array.isArray(value) ? value : [];
const text = value => typeof value === 'string' ? value : '';
const id = value => typeof value === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(value) ? value : '';
function plainText(value) {
 return text(value).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '').replace(/<\/?(?:p|div|h[1-6]|li|br)[^>]*>/gi, '\n').replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").trim();
}
function lessonExercises(lesson) {
 const content = object(lesson.content);
 return list(lesson.exercises ?? content.exercises).map(object).filter(item => id(item.id)).map(item => ({
  id: item.id, title: plainText(item.title) || 'Упражнение', description: plainText(item.description || item.content),
  instructions: Array.isArray(item.instructions) ? item.instructions.map(plainText).filter(Boolean).join('\n') : plainText(item.instructions),
  type: text(item.type), options: list(item.options).filter(option => typeof option === 'string' && option.trim()),
 }));
}
function lessonQuiz(lesson) {
 const raw = object(lesson.quiz ?? object(lesson.content).quiz);
 const questions = list(raw.questions);
 if (!questions.length) return null;
 const normalized = questions.map(value => {
  const question = object(value);
  return { id: id(question.id), prompt: plainText(question.question), type: question.type || 'multiple_choice', options: list(question.options).filter(option => typeof option === 'string' && option.trim()) };
 });
 const ids = new Set(normalized.map(question => question.id));
 const supported = !!id(lesson.id) && (!raw.id || !!id(raw.id)) && normalized.length <= 100 && ids.size === normalized.length && normalized.every(question => question.id && question.prompt && (question.type === 'text' || (['multiple_choice', 'true_false'].includes(question.type) && question.options.length >= 2 && new Set(question.options).size === question.options.length)));
 return { id: id(raw.id) || lesson.id, title: plainText(raw.title) || 'Проверка знаний', description: plainText(raw.description), questions: normalized, supported,
  passingScore: typeof raw.passing_score === 'number' && raw.passing_score >= 0 && raw.passing_score <= 100 ? raw.passing_score : null };
}
function lessonFiles(value) {
 if (!Array.isArray(value?.files)) throw new Error('Не удалось прочитать список материалов. Попробуйте обновить.');
 return value.files.map(object).filter(file => id(file.id)).map(file => ({
  id: file.id, name: text(file.original_name || file.original_filename || file.filename) || 'Материал урока',
  type: text(file.mime_type || file.file_type), extension: text(file.extension).replace(/^\./, '').toUpperCase(),
  section: text(file.section || file.lesson_section), size: typeof file.file_size === 'number' && file.file_size >= 0 ? file.file_size : null,
 }));
}
function exerciseResponses(value) {
 if (!value || !value.exercise_responses || typeof value.exercise_responses !== 'object' || Array.isArray(value.exercise_responses)) throw new Error('Не удалось прочитать сохранённые ответы.');
 return Object.fromEntries(Object.entries(value.exercise_responses).map(([key, raw]) => {
  const row = object(raw);
  return [key, { attachments: Array.isArray(row.attachment_ids) ? row.attachment_ids.filter(item=>typeof item==='string'&&/^[a-f0-9]{64}$/.test(item)) : [], id: text(row.id), text: text(row.response_text), reviewed: row.reviewed === true, comment: text(row.admin_comment), submittedAt: text(row.submitted_at) }];
 }));
}
function quizResult(value) {
 const row = object(value);
 if (!id(row.attempt_id || row.id) || typeof row.score !== 'number' || !Number.isFinite(row.score) || row.score < 0 || row.score > 100 || typeof row.passed !== 'boolean') throw new Error('Сервер не подтвердил результат теста. Повторите запрос.');
 return { id: row.attempt_id || row.id, score: row.score, passed: row.passed, attemptedAt: text(row.attempted_at), submissionId: text(row.submission_id) };
}
function quizAttempts(value) {
 if (!Array.isArray(value?.attempts)) throw new Error('Не удалось прочитать историю теста.');
 return value.attempts.map(quizResult);
}
function lessonProgress(value) {
 const row = object(value);
 if (typeof row.completion_percentage !== 'number' || !Number.isFinite(row.completion_percentage) || row.completion_percentage < 0 || row.completion_percentage > 100) throw new Error('Сервер не передал учебный прогресс. Попробуйте обновить.');
 return { percentage: row.completion_percentage, completed: row.is_completed === true, theoryRead: row.theory_read === true, exercisesCompleted: typeof row.exercises_completed === 'number' ? row.exercises_completed : null, quizPassed: row.quiz_passed === true, challengeCompleted: row.challenge_completed === true };
}
function quizPayload(lessonId, quiz, answers, submissionId) {
 if (!id(lessonId) || !quiz?.supported || !id(quiz.id) || !/^[\da-f]{8}-[\da-f]{4}-4[\da-f]{3}-[89ab][\da-f]{3}-[\da-f]{12}$/i.test(submissionId)) throw new Error('Не удалось подготовить тест к отправке.');
 const result = {};
 for (const question of quiz.questions) {
  const answer = text(answers[question.id]);
  if (!answer.trim() || answer.length > 4000 || (question.type !== 'text' && !question.options.includes(answer))) throw new Error('Ответьте на все вопросы теста.');
  result[question.id] = answer;
 }
 return { lesson_id: lessonId, quiz_id: quiz.id, answers: result, submission_id: submissionId };
}
function exercisePayload(lessonId, exercise, answer) {
 const response = text(answer).trim();
 if (!id(lessonId) || !id(exercise?.id) || !response || response.length > 10000) throw new Error('Введите ответ длиной от 1 до 10 000 символов.');
 if (exercise.type === 'multiple_choice' && exercise.options.length && !exercise.options.includes(response)) throw new Error('Выберите один из вариантов ответа.');
 return { lesson_id: lessonId, exercise_id: exercise.id, response_text: response };
}
function safeLearningUrl(value) {
 try { const url = new URL(value); if (url.protocol === 'https:' && !url.username && !url.password) return url.toString(); } catch { /* Invalid or relative URLs are not launchable media. */ }
 throw new Error('Для этого материала пока нет безопасной ссылки. Попробуйте позже.');
}
function submissionId() {
 if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
 // This is only a deduplication identifier, never an authentication secret.
 return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, character => {
  const random = Math.floor(Math.random() * 16);
  return (character === 'x' ? random : (random & 3) | 8).toString(16);
 });
}
function singleFlight() {
 let pending = null;
 return operation => {
  if (pending) return pending;
  pending = Promise.resolve().then(operation).finally(() => { pending = null; });
  return pending;
 };
}
function quizSubmission() {
 let pending = null;
 const run = singleFlight();
 return {
  hasPending: () => pending !== null,
  reset: () => { pending = null; },
  submit: (api, lessonId, quiz, answers) => run(async () => {
   if (!pending) pending = quizPayload(lessonId, quiz, answers, submissionId());
   try {
    const receipt = quizResult(await api.request('/student/quiz-attempt', {method:'POST', body:pending}));
    pending = null;
    return receipt;
   } catch (error) {
    if (error?.status >= 400 && error?.status < 500 && error?.status !== 409) pending = null;
    throw error;
   }
  }),
 };
}
module.exports = { quizSubmission, plainText, lessonExercises, lessonQuiz, lessonFiles, exerciseResponses, quizResult, quizAttempts, lessonProgress, quizPayload, exercisePayload, safeLearningUrl, submissionId, singleFlight };
