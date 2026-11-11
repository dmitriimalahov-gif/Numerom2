import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
global.TextEncoder = require('util').TextEncoder;
const { MemoryRouter } = require('react-router-dom');
const Page = require('../FullReportPage').default;
const { useAuth } = require('../../../components/AuthContext');
const { api } = require('../../../services/api');
jest.mock('../../../components/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../../../services/api', () => ({ api: { request: jest.fn() } }));
jest.mock('../../../utils/backendUrl', () => ({ getBackendUrl: () => 'https://api.example.invalid' }));
const catalog = { title: 'Полный разбор', amount_total: 666, currency: 'eur', mode: 'test', enabled: true, clients: ['web'], includes: ['Персональные числа', 'Озвучка'] };
const receipt = { order_id: 'a'.repeat(64), status: 'pending', mode: 'test', birth_date: '12.03.1990', as_of_date: '22.10.2026', amount_total: 666, currency: 'eur' };
const paid = { ...receipt, status: 'paid', report_status: 'ready', report: { version: 1, title: 'Полный разбор', birth_date: receipt.birth_date, as_of_date: receipt.as_of_date, summary: ['Ваше сочетание чисел'], sections: [{ id: 'numbers', title: 'Ваши числа', paragraphs: ['Ваш личный результат'], method: 'Сумма цифр даты', steps: ['1 + 2 = 3'], values: [{ label: 'Число души', value: 3, meaning: 'Смысл числа' }], chart: { type: 'matrix', items: [{ label: 'Характер', value: 1 }] } }], excluded: [{ title: 'Имя', reason: 'Требуется имя' }], narration: [] } };
let root, host;
const render = async (path = '/dashboard/full-report') => act(async () => root.render(<MemoryRouter initialEntries={[path]}><Page /></MemoryRouter>));
const submit = async () => act(async () => host.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
const posts = () => api.request.mock.calls.filter(([path, options]) => options?.method === 'POST' && path !== '/full-reports/preview');
function basicApi(path) {
  if (path === '/full-reports/preview') return Promise.resolve({birth_date:receipt.birth_date,use_profile:true,profile_fingerprint:'c'.repeat(64),available:[{id:'numbers',title:'Персональные числа'}],excluded:[]});
  if (path === '/full-reports/catalog') return Promise.resolve(catalog);
  if (path === '/full-reports/history') return Promise.resolve({ orders: [] });
  if (path.endsWith('/narration')) return Promise.resolve({ items: [] });
  return Promise.resolve(receipt);
}
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  Object.defineProperty(window, 'crypto', { configurable: true, value: { randomUUID: () => '123e4567-e89b-42d3-a456-426614174000' } });
  localStorage.clear(); api.request.mockReset(); api.request.mockImplementation(basicApi);
  useAuth.mockReturnValue({ user: { id: 'owner', birth_date: '12.03.1990' } });
  host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host);
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); jest.restoreAllMocks(); jest.useRealTimers(); });

test('uses the confirmed separate price and never debits credits', async () => {
  await render(); expect(host.textContent).toContain('Баллы не списываются'); expect(host.textContent).toContain('Тестовый режим Stripe');
  await submit(); const [path, options] = posts()[0]; expect(path).toBe('/full-reports/checkout');
  expect(options.body).toMatchObject({ birth_date: '12.03.1990', client: 'web' });
  expect(options.body.request_id).toMatch(/^[a-f0-9-]{36}$/); expect(options.body.amount_total).toBeUndefined();
  expect(host.textContent).toContain('Ожидает оплаты'); expect(host.querySelector('.fr-report')).toBeNull();
});
test('does not infer payment from success URL parameters', async () => {
  await render('/dashboard/full-report?order_id=' + receipt.order_id + '&success=true');
  expect(host.querySelector('.fr-report')).toBeNull(); expect(host.textContent).toContain('Ожидает оплаты'); expect(posts()).toHaveLength(0);
});
test('ambiguous checkout keeps one request id even after remount', async () => {
  api.request.mockImplementation(path => path === '/full-reports/checkout' ? Promise.reject(new Error('Соединение прервано')) : basicApi(path));
  await render(); await submit(); const original = posts()[0][1].body.request_id;
  expect(host.textContent).toContain('Продолжить начатую оплату');
  await act(async () => root.unmount()); root = createRoot(host);
  await render(); await submit(); expect(posts()[1][1].body.request_id).toBe(original);
  expect(host.querySelector('input').disabled).toBe(true);
});
test('rejects unexpected catalog price and does not create checkout', async () => {
  api.request.mockImplementation(path => path === '/full-reports/catalog' ? Promise.resolve({ ...catalog, amount_total: 1000 }) : basicApi(path));
  await render(); await submit(); expect(posts()).toHaveLength(0); expect(host.textContent).toContain('Не удалось подтвердить стоимость');
});
test('paid report exposes personal text, calculation, schemes and protected narration', async () => {
  api.request.mockImplementation(path => path === `/full-reports/${receipt.order_id}` ? Promise.resolve(paid) : basicApi(path));
  await render('/dashboard/full-report?order_id=' + receipt.order_id);
  expect(host.textContent).toContain('Ваш личный результат'); expect(host.textContent).toContain('1 + 2 = 3'); expect(host.querySelector('.fr-matrix')).not.toBeNull();
  expect(api.request.mock.calls.some(([path]) => path === `/full-reports/${receipt.order_id}/narration`)).toBe(true);
  expect([...host.querySelectorAll('button')].some(button => button.textContent.includes('Сохранить PDF'))).toBe(true);
});
test('switching accounts hides the previous report and pending attempt', async () => {
  localStorage.setItem('numerom.full-report.pending.owner', JSON.stringify({ request_id: '123e4567-e89b-42d3-a456-426614174000', birth_date: receipt.birth_date, order_id: receipt.order_id }));
  api.request.mockImplementation(path => path === `/full-reports/${receipt.order_id}` ? Promise.resolve(paid) : basicApi(path));
  await render(); expect(host.textContent).toContain('Ваш личный результат');
  useAuth.mockReturnValue({ user: { id: 'other' } }); await render();
  expect(host.textContent).not.toContain('Ваш личный результат'); expect(host.querySelector('input').value).toBe('');
});
test('storage failure prevents an untracked payment request', async () => {
  await render(); jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Хранилище недоступно'); });
  await submit(); expect(posts()).toHaveLength(0); expect(host.textContent).toContain('Хранилище недоступно');
});
test('unexpected checkout destination is rejected before navigation', async () => {
  api.request.mockImplementation(path => path === '/full-reports/checkout' ? Promise.resolve({ ...receipt, url: 'https://attacker.example/checkout' }) : basicApi(path));
  await render(); await submit(); expect(host.textContent).toContain('Ссылка оплаты не подтверждена'); expect(host.querySelector('.fr-report')).toBeNull();
});
test('paid numeric draft continues polling until local interpretation is ready', async () => {
  jest.useFakeTimers(); let response = { ...paid, report_status: 'preparing' };
  api.request.mockImplementation(path => path === `/full-reports/${receipt.order_id}` ? Promise.resolve(response) : basicApi(path));
  await render('/dashboard/full-report?order_id=' + receipt.order_id);
  expect(host.textContent).toContain('Смысловой разбор по вашим расчётам готовится'); expect(host.textContent).toContain('Ваш личный результат');
  response = { ...paid, report: { ...paid.report, summary: ['Готовая смысловая интерпретация'] } };
  await act(async () => { jest.advanceTimersByTime(30000); });
  expect(host.textContent).toContain('Готовая смысловая интерпретация'); expect(host.textContent).not.toContain('Смысловой разбор по вашим расчётам готовится');
});


test('paid profile extension passes the current revision without another checkout',async()=>{
 const previous={...paid,revision:1,profile_fingerprint:'a'.repeat(64)};
 api.request.mockImplementation(path=>path===`/full-reports/${receipt.order_id}/extend-profile`?Promise.resolve({...paid,revision:2,profile_fingerprint:'c'.repeat(64)}):path===`/full-reports/${receipt.order_id}`?Promise.resolve(previous):basicApi(path));
 await render('/dashboard/full-report?order_id='+receipt.order_id);
 await act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent==='Дополнить разбор без доплаты').click());
 const [path,options]=posts().find(([path])=>path.endsWith('/extend-profile'));
 expect(path).toBe(`/full-reports/${receipt.order_id}/extend-profile`);expect(options.body).toEqual({profile_fingerprint:'c'.repeat(64),expected_revision:1});
 expect(posts().some(([path])=>path==='/full-reports/checkout')).toBe(false);
});

test('changed profile refreshes the fingerprint while preserving the purchase UUID',async()=>{
 let stamp='c',attempts=0;api.request.mockImplementation(path=>{
  if(path==='/full-reports/preview')return Promise.resolve({birth_date:receipt.birth_date,use_profile:true,profile_fingerprint:stamp.repeat(64),available:[],excluded:[]});
  if(path==='/full-reports/checkout'&&attempts++===0){stamp='d';return Promise.reject(Object.assign(new Error('Review profile'),{code:'full_report_profile_changed'}));}
  return basicApi(path);
 });
 await render();await submit();const first=posts()[0][1].body;
 expect(JSON.parse(localStorage.getItem('numerom.full-report.pending.owner')).profile_stale).toBe(true);
 await submit();const second=posts()[1][1].body;
 expect(second.request_id).toBe(first.request_id);expect(second.profile_fingerprint).toBe('d'.repeat(64));expect(second.profile_fingerprint).not.toBe(first.profile_fingerprint);
});

test('idempotent extension returning an archived revision never attaches current narration',async()=>{
 const current={...paid,revision:2,profile_fingerprint:'a'.repeat(64),previous_revisions:[{revision:1}]};
 const archived={...paid,revision:1,is_archived:true,report:{...paid.report,title:'Архивная версия'}};
 api.request.mockImplementation(path=>path===`/full-reports/${receipt.order_id}/extend-profile`?Promise.resolve(archived):path===`/full-reports/${receipt.order_id}`?Promise.resolve(current):basicApi(path));
 await render('/dashboard/full-report?order_id='+receipt.order_id);
 await act(async()=>[...host.querySelectorAll('button')].find(button=>button.textContent==='Дополнить разбор без доплаты').click());
 expect(host.textContent).toContain('Архивная версия');expect(host.textContent).toContain('Текущая версия 2');expect(host.textContent).toContain('Аудио и видео доступны в текущей версии');
 expect(host.querySelector('.fr-audio')).toBeNull();
});

test('a report picked from the saved list opens at the top of the page with the person named', async () => {
  const saved = { ...paid, person: 'Иван Петров' };
  api.request.mockImplementation(path => path === '/full-reports/history' ? Promise.resolve({ orders: [{ ...receipt, status: 'paid', report_status: 'ready', person: 'Иван Петров' }] })
    : path === `/full-reports/${receipt.order_id}` ? Promise.resolve(saved) : basicApi(path));
  const scrolled = jest.spyOn(window, 'scrollTo').mockImplementation(() => {});
  await render();
  const item = [...host.querySelectorAll('.fr-history button')][0];
  expect(item.textContent).toContain('Иван Петров · 12.03.1990');
  expect(scrolled).not.toHaveBeenCalled();
  await act(async () => item.click());
  await act(async () => new Promise(resolve => setTimeout(resolve, 50)));
  expect(host.textContent).toContain('Ваш личный результат');
  expect(scrolled).toHaveBeenCalledWith(expect.objectContaining({ top: 0 }));
});
