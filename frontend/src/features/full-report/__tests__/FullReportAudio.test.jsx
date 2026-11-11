import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import Audio from '../FullReportAudio';
import { api } from '../../../services/api';
jest.mock('../../../services/api', () => ({ api: { request: jest.fn() } }));
jest.mock('../../../utils/backendUrl', () => ({ getBackendUrl: () => 'https://api.example.invalid' }));
let root, host;
const clip = { id: 'overview', title: 'Ваш разбор', text: 'Персональный текст', status: 'ready', url: 'https://api.example.invalid/api/student/narration-media/signed-ticket' };
const render = async (orderId = 'a'.repeat(64)) => act(async () => root.render(<Audio orderId={orderId} />));
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); api.request.mockReset(); jest.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {}); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); jest.restoreAllMocks(); jest.useRealTimers(); });
test('ready recording uses only protected media on the current server', async () => {
  api.request.mockResolvedValue({ items: [clip] }); await render();
  expect(host.querySelector('audio').src).toBe(clip.url); expect(host.querySelector('audio').autoplay).toBe(false);
  expect(host.textContent).toContain('Персональный текст'); expect(api.request.mock.calls[0][0]).toBe(`/full-reports/${'a'.repeat(64)}/narration`);
});
test('rejects a recording from a different host', async () => {
  api.request.mockResolvedValue({ items: [{ ...clip, url: 'https://attacker.example/api/student/narration-media/ticket' }] }); await render();
  expect(host.querySelector('audio')).toBeNull(); expect(host.textContent).toContain('Адрес аудиозаписи недоступен');
});
test('missing chapter is requested through the owned report access route', async () => {
  api.request.mockResolvedValue({ items: [{ ...clip, status: 'missing', url: null }] }); await render();
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Подготовить')).click());
  expect(api.request.mock.calls.some(([path, options]) => path === `/full-reports/${'a'.repeat(64)}/narration/overview/access` && options?.method === 'POST')).toBe(true);
});
test('analysis 503 automatically recovers within 30 seconds when audio becomes available', async () => {
  jest.useFakeTimers(); api.request.mockRejectedValueOnce(new Error('Смысловой разбор готовится')).mockResolvedValue({ items: [clip] });
  await render(); expect(host.querySelector('audio')).toBeNull();
  await act(async () => { jest.advanceTimersByTime(30000); });
  expect(host.querySelector('audio').src).toBe(clip.url); expect(api.request).toHaveBeenCalledTimes(2);
});
test('pending audio polls and preserves the player URL once ready', async () => {
  jest.useFakeTimers(); api.request.mockResolvedValueOnce({ items: [{ ...clip, status: 'preparing', url: null }] }).mockResolvedValue({ items: [clip] });
  await render(); await act(async () => { jest.advanceTimersByTime(30000); }); const player = host.querySelector('audio');
  api.request.mockResolvedValue({ items: [{ ...clip, url: clip.url + '-renewed' }] });
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Обновить')).click());
  expect(host.querySelector('audio')).toBe(player); expect(player.src).toBe(clip.url);
});
test('failed report audio retries the current owned paid snapshot without a new purchase', async () => {
  api.request.mockResolvedValue({ items: [{ ...clip, status: 'review', url: null }] }); await render();
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Повторить')).click());
  expect(api.request.mock.calls.some(([path, options]) => path === `/full-reports/${'a'.repeat(64)}/video` && options?.method === 'POST' && Object.keys(options.body).length === 0)).toBe(true);
  expect(api.request.mock.calls.some(([path]) => path.includes('checkout'))).toBe(false);
});
test('while the voice is recorded the buyer sees preparation, and a dropped poll is not shown as an error', async () => {
  const dropped = Object.assign(new Error('Не удалось связаться с NumerOM. Проверьте соединение или попробуйте позже.'), { status: 0, code: 'network' });
  api.request.mockResolvedValueOnce({ items: [] }); await render();
  expect(host.textContent).toContain('Озвучка готовится'); expect(host.querySelector('.fr-error')).toBeNull();
  api.request.mockRejectedValueOnce(dropped);
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Обновить') || button.textContent.includes('Подготовить') || button.textContent.includes('Проверить'))?.click());
  expect(host.querySelector('.fr-error')).toBeNull(); expect(host.textContent).toContain('Связь ненадолго прервалась');
});
test('switching orders clears ready audio even when the new report returns 503', async () => {
  api.request.mockResolvedValueOnce({ items: [clip] }); await render(); expect(host.querySelector('audio')).not.toBeNull();
  api.request.mockRejectedValueOnce(new Error('Новый разбор готовится')); await render('b'.repeat(64));
  expect(host.querySelector('audio')).toBeNull(); expect(host.querySelector('select')).toBeNull();
  expect(host.textContent).not.toContain(clip.text); expect(host.textContent).toContain('Новый разбор готовится');
});
test('a late previous-order response cannot populate the new report or its URL cache', async () => {
  let finish; api.request.mockReturnValueOnce(new Promise(resolve => { finish = resolve; })); await render();
  api.request.mockRejectedValueOnce(new Error('Новый разбор готовится')); await render('b'.repeat(64));
  await act(async () => finish({ items: [clip] })); expect(host.querySelector('audio')).toBeNull(); expect(host.textContent).not.toContain(clip.text);
  const current = { ...clip, url: clip.url + '-current' }; api.request.mockResolvedValue({ items: [current] });
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Обновить')).click());
  expect(host.querySelector('audio').src).toBe(current.url);
});
