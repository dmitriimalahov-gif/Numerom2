import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { AuthProvider } from '../../../components/AuthContext';

jest.mock('axios', () => ({ defaults: { headers: { common: {} } } }));
global.TextEncoder = require('util').TextEncoder;
const { MemoryRouter, Routes, Route } = require('react-router-dom');
const AdminWorkspace = require('../AdminWorkspace').default;

let root, host;
const admin = { id: 'admin-1', email: 'admin@example.invalid', is_admin: true, is_super_admin: true };
const member = { id: 'member-1', email: 'anna@example.invalid', full_name: 'Анна Петрова', credits_remaining: 12, is_admin: false, is_super_admin: false, is_disabled: false };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
const deferred = () => { let resolve; const promise = new Promise(yes => { resolve = yes; }); return { promise, resolve }; };
const button = text => [...document.querySelectorAll('button')].find(node => node.textContent.trim() === text);
const click = async node => { expect(node).toBeTruthy(); await act(async () => { node.dispatchEvent(new MouseEvent('click', { bubbles: true })); }); };
const input = async (id, value) => { const node = document.getElementById(id); await act(async () => { Object.getOwnPropertyDescriptor(node.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value').set.call(node, value); node.dispatchEvent(new Event('input', { bubbles: true })); }); };
const render = async (path = '/dashboard/admin/users') => { await act(async () => { root.render(<AuthProvider><MemoryRouter initialEntries={[path]}><Routes><Route path="/dashboard/admin/*" element={<AdminWorkspace />} /></Routes></MemoryRouter></AuthProvider>); }); };
const defaultFetch = async url => {
  if (url.endsWith('/user/profile-v2')) return response(admin);
  if (url.includes('/manage/users?')) return response({ users: [member], total: 1, page: 1, page_size: 20 });
  if (url.endsWith('/manage/users/member-1')) return response({ user: member, admin_history: [] });
  throw new Error(`Unexpected request: ${url}`);
};
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  localStorage.clear(); localStorage.setItem('token', 'test-only');
  global.fetch = jest.fn(defaultFetch);
  jest.spyOn(console, 'log').mockImplementation(() => {});
});
afterEach(async () => { await act(async () => { root.unmount(); }); host.remove(); localStorage.clear(); jest.restoreAllMocks(); });

test('a member opening an admin URL is denied before any administrative request', async () => {
  global.fetch.mockImplementation(async url => url.endsWith('/user/profile-v2') ? response(member) : defaultFetch(url));
  await render();
  expect(host.textContent).toContain('Доступ ограничен');
  expect(global.fetch.mock.calls.some(([url]) => url.includes('/admin/'))).toBe(false);
});

test('credits show before and after, wait for confirmation, and submit once while saving', async () => {
  const pending = deferred();
  let creditSent = false;
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/credits')) { creditSent = true; return pending.promise; }
    if (creditSent && url.endsWith('/manage/users/member-1')) return Promise.resolve(response({ user: { ...member, credits_remaining: 20 }, admin_history: [] }));
    return defaultFetch(url);
  });
  await render();
  await click(button('Открыть Анна Петрова'));
  await input('admin-credit-amount', '8');
  await input('admin-credit-reason', 'Коррекция оплаты');
  await click(button('Проверить изменение'));
  expect(document.body.textContent).toContain('Было12');
  expect(document.body.textContent).toContain('Станет20');
  expect(global.fetch.mock.calls.some(([url]) => url.endsWith('/credits'))).toBe(false);
  await click(button('Подтвердить начисление'));
  const confirmButton = button('Сохраняем…');
  expect(confirmButton.disabled).toBe(true);
  await click(confirmButton);
  const calls = global.fetch.mock.calls.filter(([url]) => url.endsWith('/credits'));
  expect(calls).toHaveLength(1);
  expect(JSON.parse(calls[0][1].body)).toEqual({ amount: 8, expected_balance: 12, reason: 'Коррекция оплаты' });
  await act(async () => { pending.resolve(response({ user: { ...member, credits_remaining: 20 } })); });
  expect(document.body.textContent).toContain('Кредиты обновлены');
  expect(document.querySelector('[data-testid="current-balance"]').textContent).toBe('20');
});

test('a stale credit balance reloads the profile and requires a fresh confirmation', async () => {
  let changed = false;
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/credits')) { changed = true; return Promise.resolve(response({ detail: 'Balance changed' }, 409)); }
    if (changed && url.endsWith('/manage/users/member-1')) return Promise.resolve(response({ user: { ...member, credits_remaining: 7 }, admin_history: [] }));
    return defaultFetch(url);
  });
  await render(); await click(button('Открыть Анна Петрова'));
  await input('admin-credit-amount', '8'); await input('admin-credit-reason', 'Коррекция оплаты');
  await click(button('Проверить изменение')); await click(button('Подтвердить начисление'));
  expect(document.body.textContent).toContain('Данные обновлены');
  expect(document.querySelector('[data-testid="current-balance"]').textContent).toBe('7');
  expect(button('Подтвердить начисление')).toBeUndefined();
  expect(global.fetch.mock.calls.filter(([url]) => url.endsWith('/credits'))).toHaveLength(1);
  await click(button('Проверить изменение'));
  expect(document.body.textContent).toContain('Было7');
  expect(document.body.textContent).toContain('Станет15');
});

test('an old search response cannot overwrite the current search', async () => {
  const first = deferred(); const second = deferred();
  global.fetch.mockImplementation(url => {
    if (url.includes('/manage/users?') && new URL(url).searchParams.get('q') === 'Первая') return first.promise;
    if (url.includes('/manage/users?') && new URL(url).searchParams.get('q') === 'Вторая') return second.promise;
    return defaultFetch(url);
  });
  await render(); await input('admin-user-search', 'Первая'); await click(button('Найти'));
  await input('admin-user-search', 'Вторая'); await click(button('Найти'));
  await act(async () => { second.resolve(response({ users: [{ ...member, full_name: 'Вторая ученица' }], total: 1, page: 1, page_size: 20 })); });
  await act(async () => { first.resolve(response({ users: [{ ...member, full_name: 'Первая ученица' }], total: 1, page: 1, page_size: 20 })); });
  expect(host.textContent).toContain('Вторая ученица'); expect(host.textContent).not.toContain('Первая ученица');
});

test('an ordinary admin can close member access but cannot assign an admin role', async () => {
  let accessChanged = false;
  global.fetch.mockImplementation((url, options) => {
    if (url.endsWith('/user/profile-v2')) return Promise.resolve(response({ ...admin, is_super_admin: false }));
    if (url.endsWith('/access')) { accessChanged = true; return Promise.resolve(response({ user: { ...member, is_disabled: true } })); }
    if (accessChanged && url.endsWith('/manage/users/member-1')) return Promise.resolve(response({ user: { ...member, is_disabled: true }, admin_history: [] }));
    return defaultFetch(url);
  });
  await render(); await click(button('Открыть Анна Петрова'));
  expect(document.body.textContent).not.toContain('Права администратора');
  await click(document.querySelector('.nm-admin-access-options input[type="checkbox"]'));
  await input('admin-access-reason', 'По просьбе пользователя'); await click(button('Проверить доступ'));
  expect(global.fetch.mock.calls.some(([url]) => url.endsWith('/access'))).toBe(false);
  await click(button('Подтвердить доступ'));
  const call = global.fetch.mock.calls.find(([url]) => url.endsWith('/access'));
  expect(JSON.parse(call[1].body)).toEqual({ is_disabled: true, reason: 'По просьбе пользователя' });
  expect(document.body.textContent).toContain('Доступ обновлён');
});

test('missing overview counts stay unavailable and a real zero is displayed', async () => {
  global.fetch.mockImplementation(url => url.endsWith('/manage/overview') ? Promise.resolve(response({ users_total: 0, lessons_total: 4 })) : defaultFetch(url));
  await render('/dashboard/admin');
  const counts = [...host.querySelectorAll('.nm-admin-overview dd')].map(node => node.textContent);
  expect(counts).toEqual(['0', '—', '—', '4', '—']);
});

test('overview explains when recovery mail is not configured', async () => {
  global.fetch.mockImplementation(url => {
    if (url.endsWith('/manage/overview')) return Promise.resolve(response({ users_total: 0 }));
    if (url.endsWith('/manage/recovery-status')) return Promise.resolve(response({ configured: false }));
    return defaultFetch(url);
  });
  await render('/dashboard/admin');
  expect(host.textContent).toContain('Почта не настроена');
  expect(host.textContent).toContain('Восстановление пароля по почте пока недоступно');
});
