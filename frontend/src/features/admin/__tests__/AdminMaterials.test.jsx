import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminFilePreview from '../AdminFilePreview';
import LessonEditModal from '../../../components/LessonEditModal';
let root, host;
const reply = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
const click = async element => { expect(element).toBeTruthy(); await act(async () => { element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 0 })); element.dispatchEvent(new MouseEvent('click', { bubbles: true })); }); };
const button = text => [...document.querySelectorAll('button')].find(node => node.textContent.trim() === text);
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true; localStorage.setItem('token', 'synthetic');
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  global.fetch = jest.fn(); URL.createObjectURL = jest.fn(() => 'blob:local-preview'); URL.revokeObjectURL = jest.fn();
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); });

test('preview fetches protected content with authentication, releases its blob, and never writes student activity', async () => {
  global.fetch.mockResolvedValue({ ok: true, blob: async () => new Blob(['image'], { type: 'image/png' }) });
  await act(async () => root.render(<AdminFilePreview file={{ id: 'file', original_name: 'photo.png', mime_type: 'image/png' }} />));
  expect(global.fetch).toHaveBeenCalledTimes(1);
  expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/download-file\/file$/);
  expect(global.fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer synthetic');
  expect(host.querySelector('img').src).toBe('blob:local-preview');
  await act(async () => root.render(null));
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:local-preview');
});

test('a failed preview can be retried and HTML content is shown as plain text', async () => {
  global.fetch.mockResolvedValueOnce(reply({}, 503)).mockResolvedValueOnce({ ok: true, text: async () => '<script>bad()</script>' });
  await act(async () => root.render(<AdminFilePreview file={{ id: 'text', mime_type: 'text/html' }} />));
  expect(host.textContent).toContain('Сервер временно недоступен');
  await click(button('Повторить загрузку'));
  expect(host.querySelector('pre').textContent).toBe('<script>bad()</script>');
  expect(host.querySelector('iframe, script')).toBeNull();
});

test('lesson upload locks save and close; a failed upload leaves the editor and retry available', async () => {
  let resolve;
  const onSave = jest.fn(); const onClose = jest.fn();
  global.fetch.mockImplementation((url, options) => options?.method === 'POST' ? new Promise(yes => { resolve = yes; }) : Promise.resolve(reply({ files: [] })));
  await act(async () => root.render(<LessonEditModal isOpen lesson={{ id: 'lesson', title: 'Урок', level: 1 }} onSave={onSave} onClose={onClose} />));
  await click(button('Теория'));
  const input = document.querySelector('#upload-theory-docs');
  const file = new File(['lesson'], 'lesson.txt', { type: 'text/plain' });
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); });
  expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(1);
  expect(button('Сохранить все изменения').disabled).toBe(true);
  await click(button('Отмена')); expect(onClose).not.toHaveBeenCalled(); expect(onSave).not.toHaveBeenCalled();
  await act(async () => resolve(reply({}, 503)));
  expect(document.body.textContent).toContain('Загружено 0 из 1. Сервер временно недоступен');
  expect(button('Сохранить все изменения').disabled).toBe(false);
  expect(global.fetch.mock.calls.some(([url]) => url.includes('/student/'))).toBe(false);
});

test('attachments are available in every lesson section and upload to the selected section', async () => {
  global.fetch.mockImplementation((url, options) => Promise.resolve(options?.method === 'POST' ? reply({ file_id: 'uploaded' }) : reply({ files: [] })));
  await act(async () => root.render(<LessonEditModal isOpen lesson={{ id: 'lesson', title: 'Урок', level: 1 }} onSave={jest.fn()} onClose={jest.fn()} />));
  for (const [tab, section] of [['Теория', 'theory'], ['Упражнения', 'exercises'], ['Челлендж', 'challenge'], ['Тест', 'quiz']]) {
    await click(button(tab));
    expect(document.querySelector('section[aria-label="Файлы раздела"]')).toBeTruthy();
    const input = document.getElementById(`upload-${section}-docs`);
    expect(input).toBeTruthy();
    Object.defineProperty(input, 'files', { configurable: true, value: [new File(['test'], 'note.txt', { type: 'text/plain' })] });
    await act(async () => input.dispatchEvent(new Event('change', { bubbles: true })));
    const posts = global.fetch.mock.calls.filter(([, options]) => options?.method === 'POST');
    expect(posts[posts.length - 1][1].body.get('section')).toBe(section);
  }
  expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(4);
});

test('editing the correct answer text keeps the quiz answer valid and a new question gets a unique id', async () => {
  const onSave = jest.fn(); global.fetch.mockResolvedValue(reply({ files: [] }));
  const question = { id: 'q2', question: 'Вопрос', options: ['Верно', 'Неверно'], correct_answer: 'Верно' };
  await act(async () => root.render(<LessonEditModal isOpen lesson={{ id: 'lesson', title: 'Урок', quiz: { id: 'quiz', questions: [question], passing_score: 0 } }} onSave={onSave} onClose={jest.fn()} />));
  await click(button('Тест'));
  const option = document.querySelector('input[placeholder="Вариант 1"]');
  await act(async () => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(option, 'Уточнённый ответ'); option.dispatchEvent(new Event('input', { bubbles: true })); });
  await click(button('Добавить вопрос')); await click(button('Сохранить все изменения'));
  const saved = onSave.mock.calls[0][0];
  expect(saved.quiz.questions[0].correct_answer).toBe('Уточнённый ответ'); expect(saved.quiz.questions[0].options[0]).toBe('Уточнённый ответ');
  expect(new Set(saved.quiz.questions.map(item => item.id)).size).toBe(2); expect(saved.quiz.passing_score).toBe(0);
});
