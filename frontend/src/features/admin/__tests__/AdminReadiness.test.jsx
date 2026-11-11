import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { AuthProvider } from '../../../components/AuthContext';
jest.mock('axios', () => ({ defaults: { headers: { common: {} } } }));
global.TextEncoder = require('util').TextEncoder;
const { MemoryRouter, Routes, Route } = require('react-router-dom');
const AdminWorkspace = require('../AdminWorkspace').default;

let root, host;
const actor = { id: 'admin', is_admin: true, is_super_admin: true };
const reply = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
const deferred = () => { let resolve; const promise = new Promise(yes => { resolve = yes; }); return { promise, resolve }; };
const button = text => [...document.querySelectorAll('button')].find(node => node.textContent.trim() === text);
const click = async element => { expect(element).toBeTruthy(); await act(async () => { element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); }); };
const setValue = async (element, value) => { await act(async () => { const prototype = element.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, value); element.dispatchEvent(new Event(element.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true })); }); };
const baseFetch = url => {
  if (url.endsWith('/user/profile-v2')) return Promise.resolve(reply(actor));
  if (url.endsWith('/admin/consultations')) return Promise.resolve(reply([]));
  if (url.endsWith('/admin/users')) return Promise.resolve(reply({ users: [{ id: 'member', email: 'member@example.invalid', full_name: 'Ученик' }] }));
  if (url.endsWith('-config')) return Promise.resolve(reply({ config: {} }));
  throw new Error(`Unexpected request: ${url}`);
};
const render = async section => { await act(async () => { root.render(<AuthProvider><MemoryRouter initialEntries={[`/dashboard/admin/${section}`]}><Routes><Route path="/dashboard/admin/*" element={<AdminWorkspace />} /></Routes></MemoryRouter></AuthProvider>); }); };
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true; localStorage.setItem('token', 'synthetic-test-token');
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  global.fetch = jest.fn(baseFetch); jest.spyOn(console, 'log').mockImplementation(() => {});
  jest.spyOn(window, 'alert').mockImplementation(() => {}); jest.spyOn(window, 'confirm').mockReturnValue(true);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); jest.restoreAllMocks(); });

test('a free consultation keeps zero cost and submits only once while saving', async () => {
  const pending = deferred();
  global.fetch.mockImplementation((url, options) => url.endsWith('/admin/consultations') && options?.method === 'POST' ? pending.promise : baseFetch(url));
  await render('consultations');
  await click([...host.querySelectorAll('button')].find(node => node.textContent.includes('Создать консультацию')));
  await setValue(host.querySelector('input[placeholder="Введите название консультации"]'), 'Тестовая консультация');
  await setValue(host.querySelector('select'), 'member');
  const cost = host.querySelector('input[type="number"]'); await setValue(cost, '0');
  expect(cost.value).toBe('0');
  const save = button('Создать консультацию'); await click(save); await click(save);
  const calls = global.fetch.mock.calls.filter(([url, options]) => url.endsWith('/admin/consultations') && options?.method === 'POST');
  expect(calls).toHaveLength(1); expect(JSON.parse(calls[0][1].body).cost_credits).toBe(0);
  expect(button('Отмена').disabled).toBe(true);
  await act(async () => { pending.resolve(reply({ detail: 'Сохранение недоступно' }, 503)); });
  expect(document.body.textContent).toContain('Сервер временно недоступен');
  expect(host.querySelector('input[placeholder="Введите название консультации"]').value).toBe('Тестовая консультация');
});

test('settings show a load error and keep zero values after retry', async () => {
  let failing = true;
  global.fetch.mockImplementation(url => url.endsWith('/learning-points-config') ? Promise.resolve(failing ? reply({ detail: 'Unavailable' }, 503) : reply({ config: { video_points_per_minute: 0 } })) : baseFetch(url));
  await render('settings');
  expect(host.textContent).toContain('Сервер временно недоступен');
  expect(global.fetch.mock.calls.some(([url]) => url.includes('/scoring-config'))).toBe(false);
  failing = false;
  const panel = host.querySelector('[data-admin-config="learning-points-config"]');
  await click([...panel.querySelectorAll('button')].find(node => node.textContent.includes('Загрузить конфигурацию')));
  expect(panel.querySelector('input[type="number"]').value).toBe('0');
  expect(host.querySelectorAll('[data-admin-config="credits-deduction-config"]')).toHaveLength(1);
});

test('a settings save preserves the draft on failure, prevents duplicate writes and can retry', async () => {
  const pending = deferred(); let fail = true;
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/learning-points-config') && options?.method === 'PUT') return fail ? pending.promise : Promise.resolve(reply({ config: JSON.parse(options.body) }));
    if (url.endsWith('/learning-points-config')) return Promise.resolve(reply({ config: { video_points_per_minute: 1 } }));
    return baseFetch(url);
  });
  await render('settings'); const panel = host.querySelector('[data-admin-config="learning-points-config"]');
  const amount = panel.querySelector('input[type="number"]'); await setValue(amount, '0');
  const save = [...panel.querySelectorAll('button')].find(node => node.textContent.includes('Сохранить настройки'));
  await click(save); await click(save);
  expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(1);
  expect(amount.closest('fieldset').disabled).toBe(true);
  await act(async () => pending.resolve(reply({}, 503)));
  expect(panel.textContent).toContain('Сервер временно недоступен'); expect(amount.value).toBe('0');
  fail = false; await click(save);
  expect(panel.textContent).toContain('Настройки сохранены'); expect(amount.value).toBe('0');
});

test('lesson editing preserves the draft after failure and blocks double save and close', async () => {
  const pending = deferred(); let fail = true;
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/admin/lessons-v2/lesson') && options?.method === 'PUT') return fail ? pending.promise : Promise.resolve(reply({ lesson: JSON.parse(options.body) }));
    if (url.endsWith('/admin/lessons-v2')) return Promise.resolve(reply({ lessons: [{ id: 'lesson', title: 'Исходный урок', level: 1 }] }));
    if (url.endsWith('/admin/analytics/overview')) return Promise.resolve(reply({}));
    if (url.includes('/admin/files?')) return Promise.resolve(reply({ files: [], total: 0 }));
    return baseFetch(url);
  });
  await render('learning'); await click(button('Редактировать'));
  const title = document.querySelector('input[placeholder="Введите название урока"]'); await setValue(title, 'Изменённый урок');
  const save = button('Сохранить все изменения'); await click(save); await click(save);
  expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'PUT')).toHaveLength(1);
  expect(button('Отмена').disabled).toBe(true); await click(button('Отмена'));
  expect(document.querySelector('[role="dialog"]')).toBeTruthy();
  await act(async () => pending.resolve(reply({}, 503)));
  expect(document.body.textContent).toContain('Сервер временно недоступен'); expect(title.value).toBe('Изменённый урок');
  fail = false; await click(button('Сохранить все изменения'));
  expect(document.querySelector('[role="dialog"]')).toBeNull(); expect(host.textContent).toContain('Изменения урока сохранены');
});

test('all five administrative sections navigate to their real read endpoints', async () => {
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/admin/manage/overview')) return Promise.resolve(reply({}));
    if (url.endsWith('/admin/manage/recovery-status')) return Promise.resolve(reply({ configured: false }));
    if (url.includes('/admin/manage/users?')) return Promise.resolve(reply({ users: [], total: 0, page: 1, page_size: 20 }));
    if (url.endsWith('/admin/lessons-v2')) return Promise.resolve(reply({ lessons: [] }));
    if (url.endsWith('/admin/analytics/overview')) return Promise.resolve(reply({}));
    return baseFetch(url, options);
  });
  await render('');
  for (const section of ['users', 'learning', 'consultations', 'settings']) {
    await click(host.querySelector(`a[href="/dashboard/admin/${section}"]`));
    expect(host.querySelector(`a[href="/dashboard/admin/${section}"]`).getAttribute('aria-current')).toBe('page');
  }
  const paths = global.fetch.mock.calls.map(([url]) => new URL(url).pathname);
  for (const path of ['/api/admin/manage/overview', '/api/admin/manage/users', '/api/admin/lessons-v2', '/api/admin/consultations', '/api/admin/learning-points-config']) expect(paths).toContain(path);
  expect(global.fetch.mock.calls.every(([, options]) => !options?.method || options.method === 'GET')).toBe(true);
});

test('consultation attachments preview through the authenticated admin file endpoint', async () => {
  const consultation = { id: 'consultation', title: 'Консультация', assigned_user_id: 'member', cost_credits: 0, pdf_file_id: 'pdf-file', is_active: true };
  URL.createObjectURL = jest.fn(() => 'blob:consultation-preview'); URL.revokeObjectURL = jest.fn();
  global.fetch.mockImplementation(url => {
    if (url.endsWith('/admin/consultations/files/pdf-file')) return Promise.resolve({ ok: true, blob: async () => new Blob(['pdf'], { type: 'application/pdf' }) });
    if (url.endsWith('/admin/consultations')) return Promise.resolve(reply([consultation]));
    return baseFetch(url);
  });
  await render('consultations'); await click(button('Открыть PDF'));
  const call = global.fetch.mock.calls.find(([url]) => url.endsWith('/admin/consultations/files/pdf-file'));
  expect(call[1].headers.Authorization).toBe('Bearer synthetic-test-token');
  expect(document.querySelector('iframe').src).toBe('blob:consultation-preview');
  expect(global.fetch.mock.calls.some(([url]) => url.includes('/consultations/pdf/'))).toBe(false);
  await click(button('Закрыть')); expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:consultation-preview');
});

test('consultation update uses the saved record and failed deletion remains retryable', async () => {
  let consultation = { id: 'consultation', title: 'Консультация', assigned_user_id: 'member', cost_credits: 0, is_active: true };
  const pending = deferred();
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/admin/consultations/consultation') && options?.method === 'PUT') { consultation = { ...consultation, ...JSON.parse(options.body) }; return Promise.resolve(reply(consultation)); }
    if (url.endsWith('/admin/consultations/consultation') && options?.method === 'DELETE') return pending.promise;
    if (url.endsWith('/admin/consultations')) return Promise.resolve(reply([consultation]));
    return baseFetch(url);
  });
  await render('consultations'); await click(host.querySelector('[title="Редактировать консультацию"]'));
  await setValue(host.querySelector('input[placeholder="Введите название консультации"]'), 'Обновлённая консультация');
  await click(host.querySelector('#consultation-active'));
  await click(button('Сохранить изменения')); expect(host.textContent).toContain('Консультация сохранена'); expect(host.textContent).toContain('Обновлённая консультация'); expect(consultation.is_active).toBe(false);
  const remove = host.querySelector('[title="Удалить консультацию"]'); await click(remove); await click(remove);
  expect(global.fetch.mock.calls.filter(([, options]) => options?.method === 'DELETE')).toHaveLength(1);
  await act(async () => pending.resolve(reply({}, 503)));
  expect(host.textContent).toContain('Сервер временно недоступен'); expect(host.textContent).toContain('Обновлённая консультация');
  expect(host.querySelector('[title="Удалить консультацию"]').disabled).toBe(false);
});
