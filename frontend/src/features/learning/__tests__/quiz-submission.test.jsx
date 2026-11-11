import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import useQuizSubmission from '../useQuizSubmission';
let root, host;
beforeAll(() => { Object.defineProperty(globalThis, 'crypto', { configurable: true, value: require('crypto').webcrypto }); });
const lesson = { id: 'lesson-1', quiz: { id: 'quiz-1' } };
const answer = { 'question-1': 'Первый ответ' };
function Quiz() { const submission = useQuizSubmission(); const [result, setResult] = React.useState(null); return <><button disabled={submission.submitting} onClick={async () => { const value = await submission.submit(lesson, answer); if (value) setResult(value); }}>Отправить</button><p role="alert">{submission.error}</p>{result && <p>Сервер: {result.score}, {result.passed ? 'пройден' : 'не пройден'}</p>}</>; }
const click = async () => { await act(async () => { host.querySelector('button').dispatchEvent(new MouseEvent('click', { bubbles: true })); }); };
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; localStorage.setItem('token', 'synthetic'); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); global.fetch = jest.fn(); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); });
test('failed quiz submissions keep the answers and identity, show no invented success, and use only the server result', async () => {
  global.fetch.mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({}) }).mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ score: 25, passed: false, points_earned: 0, attempt_id: 'attempt' }) });
  await act(async () => root.render(<Quiz />)); await click();
  expect(host.textContent).not.toContain('Сервер:'); expect(host.textContent).toContain('Сервер временно недоступен');
  await click();
  const [first, second] = global.fetch.mock.calls.map(([, options]) => JSON.parse(options.body));
  expect(first).toEqual(second);
  expect(Object.keys(first).sort()).toEqual(['answers', 'lesson_id', 'quiz_id', 'submission_id']);
  expect(first.answers).toEqual(answer); expect(first.submission_id).toMatch(/^[0-9a-f-]{36}$/);
  expect(host.textContent).toContain('Сервер: 25, не пройден');
});
test('a second click while the quiz is saving cannot send another attempt', async () => {
  let resolve; global.fetch.mockImplementation(() => new Promise(yes => { resolve = yes; }));
  await act(async () => root.render(<Quiz />)); await click(); await click();
  expect(global.fetch).toHaveBeenCalledTimes(1);
  await act(async () => resolve({ ok: true, status: 200, json: async () => ({ score: 100, passed: true }) }));
});
