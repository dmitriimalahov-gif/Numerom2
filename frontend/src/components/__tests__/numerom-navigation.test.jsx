import React, { act } from 'react';
import { createRoot } from 'react-dom/client';

// React Router 7 needs TextEncoder in the CRA Jest environment.
global.TextEncoder = require('util').TextEncoder;
const { MemoryRouter, Routes, Route } = require('react-router-dom');
const { useAuth } = require('../AuthContext');
const UserDashboard = require('../UserDashboard').default;
const HomeContent = require('../HomeContent').default;
const NumerologyIllustrations = require('../NumerologyIllustrations').default;

jest.mock('../AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../PaymentModal', () => () => null);
jest.mock('../../utils/backendUrl', () => ({ getBackendUrl: () => 'http://localhost:8000' }));

let root, host;
const user = { full_name: 'Тестовый Пользователь', email: 'test@example.invalid', birth_date: '01.01.1990', credits_remaining: 0 };
const click = async element => { await act(async () => { element.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true })); }); };
const render = async element => { await act(async () => { root.render(element); }); };
const dashboard = () => <MemoryRouter initialEntries={['/dashboard/home']}><Routes><Route path="/dashboard" element={<UserDashboard />}><Route path="home" element={<HomeContent />} /><Route path="learning-v2" element={<h1>Учебный кабинет</h1>} /><Route path="visual-guide" element={<NumerologyIllustrations />} /></Route></Routes></MemoryRouter>;

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
  localStorage.setItem('token', 'test-only');
  useAuth.mockReturnValue({ user, isAuthenticated: true, isInitialized: true, loading: false, logout: jest.fn() });
  global.fetch = jest.fn().mockImplementation(async url => ({ ok: true, json: async () => url.endsWith('/consultations') ? [] : ({ earned_points: 0, purchased_points: 0, admin_points: 0, exercise_review_points: 0 }) }));
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); document.documentElement.classList.remove('dark'); jest.clearAllMocks(); });

test('learning action reaches the existing learning-v2 route', async () => {
  await render(dashboard());
  const link = [...host.querySelectorAll('a')].find(el => el.textContent.includes('Перейти к обучению'));
  await click(link);
  expect(host.querySelector('main').textContent).toContain('Учебный кабинет');
  expect(host.querySelector('a[aria-current="page"]').getAttribute('href')).toBe('/dashboard/learning-v2');
});

test('members see learning illustrations but no admin navigation', async () => {
  await render(dashboard());
  expect(host.querySelector('a[href="/dashboard/admin"]')).toBeNull();
  expect(host.querySelector('a[href="/dashboard/admin-v2"]')).toBeNull();
  await click(host.querySelector('a[href="/dashboard/visual-guide"]'));
  expect(host.querySelector('main h1').textContent).toBe('Схемы и примеры');
});

test('administrators see the unified administration entry', async () => {
  useAuth.mockReturnValue({ user: { ...user, is_admin: true }, isAuthenticated: true, isInitialized: true, loading: false });
  await render(dashboard());
  expect(host.querySelector('a[href="/dashboard/admin"]')).not.toBeNull();
  expect(host.querySelector('a[href="/dashboard/admin-v2"]')).toBeNull();
});

test('unavailable points show a retry and recovered zeroes remain visible', async () => {
  global.fetch.mockResolvedValueOnce({ ok: false });
  await render(<MemoryRouter><HomeContent /></MemoryRouter>);
  expect(host.textContent).toContain('Детализация пока недоступна');
  await click([...host.querySelectorAll('button')].find(el => el.textContent === 'Повторить'));
  expect(host.textContent).not.toContain('Детализация пока недоступна');
  expect([...host.querySelectorAll('.nm-points-breakdown dd')].map(el => el.textContent)).toEqual(['0', '0', '0', '0']);
});

test('missing birth date directs the user to profile setup', async () => {
  useAuth.mockReturnValue({ user: { ...user, birth_date: null } });
  await render(<MemoryRouter><HomeContent /></MemoryRouter>);
  expect(host.querySelector('.nm-welcome-panel a').getAttribute('href')).toBe('/dashboard/personal-data');
  expect(host.textContent).toContain('Заполнить профиль');
});

test('illustration categories switch and large preview closes', async () => {
  await render(<NumerologyIllustrations />);
  await click([...host.querySelectorAll('button')].find(el => el.textContent === 'Сочетания'));
  expect(host.querySelector('button[aria-pressed="true"]').textContent).toBe('Сочетания');
  await click(host.querySelector('button[aria-label="Увеличить: Сочетание 1–2–3"]'));
  const dialog = document.querySelector('[role="dialog"]');
  expect(dialog.textContent).toContain('Учебная иллюстрация');
  expect(dialog.querySelector('img').getAttribute('src')).toContain('/123W.png');
  await click(dialog.querySelector('button'));
  expect(document.querySelector('[role="dialog"]')).toBeNull();
});
