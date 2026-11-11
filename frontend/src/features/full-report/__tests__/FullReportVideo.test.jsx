import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import Video from '../FullReportVideo';
import { api } from '../../../services/api';
import { useAuth } from '../../../components/AuthContext';
import { videoState, retainVideo, videoPollDelay } from '../../../../../packages/full-report/video-state';
jest.mock('../../../services/api', () => ({ api: { request: jest.fn() } }));
jest.mock('../../../components/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../../../utils/backendUrl', () => ({ getBackendUrl: () => 'https://api.example.invalid' }));
const pending = { status: 'waiting_audio', message: 'Готовим озвучку', audio_ready: 3, audio_total: 8 };
const ready = { ...pending, status: 'ready', audio_ready: 8, expires_in: 1800, url: 'https://api.example.invalid/api/student/report-video/play-first', download_url: 'https://api.example.invalid/api/student/report-video/download-first', chapters: [{ id: 'a', title: 'Личные числа', start_seconds: 0, duration_seconds: 30 }] };
let root, host;
const render = async (id = 'a'.repeat(64)) => act(async () => root.render(<Video orderId={id} />));
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; localStorage.setItem('token', 'owner-token'); useAuth.mockReturnValue({ user: { id: 'owner' } }); api.request.mockReset(); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); jest.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {}); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); localStorage.clear(); jest.restoreAllMocks(); jest.useRealTimers(); });
test('preparation uses only the included report video service, and polls after 30 seconds', async () => {
  jest.useFakeTimers(); api.request.mockResolvedValue(pending); await render();
  expect(host.textContent).toContain('3 из 8'); expect(api.request.mock.calls[0][1].method).toBeUndefined();
  await act(async () => { jest.advanceTimersByTime(30000); }); expect(api.request).toHaveBeenCalledTimes(2);
  await act(async () => host.querySelector('button').click());
  expect(api.request.mock.calls[2][1]).toMatchObject({ method: 'POST', body: {} }); expect(host.textContent).toContain('Дополнительная оплата и баллы не нужны');
});
test('ready video uses controls without autoplay and keeps the same signed URL on refresh', async () => {
  api.request.mockResolvedValue(ready); await render(); const element = host.querySelector('video'); expect(element.controls).toBe(true); expect(element.autoplay).toBe(false); expect(element.getAttribute('playsinline')).not.toBeNull();
  api.request.mockResolvedValue({ ...ready, url: ready.url + '-new', download_url: ready.download_url + '-new' });
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Обновить ссылку')).click());
  expect(host.querySelector('video')).toBe(element); expect(element.src).toBe(ready.url); expect(host.querySelector('a[download]').href).toBe(ready.download_url);
});
test('waiting analysis does not display an audio counter yet', async () => {
  api.request.mockResolvedValue({ ...pending, status: 'waiting_analysis', message: 'Работает локальная нейросеть' }); await render();
  expect(host.textContent).toContain('Работает локальная нейросеть'); expect(host.textContent).not.toContain('Готово аудиоглав');
});
test('failed analysis has an explicit retry without polling or another payment', async () => {
  jest.useFakeTimers(); api.request.mockResolvedValue({ ...pending, status: 'failed', stage: 'analysis', message: 'Разбор не прошёл проверку' });
  await render(); expect(host.textContent).toContain('Разбор не прошёл проверку'); expect(host.textContent).not.toContain('Готово аудиоглав');
  await act(async () => { jest.advanceTimersByTime(30000); }); expect(api.request).toHaveBeenCalledTimes(1);
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Повторить смысловой разбор')).click());
  expect(api.request.mock.calls[1][1]).toMatchObject({ method: 'POST', body: {} });
});
test('late response for an old account and order cannot replace the current video', async () => {
  let resolve; api.request.mockReturnValueOnce(new Promise(value => { resolve = value; })); await render();
  useAuth.mockReturnValue({ user: { id: 'other' } }); localStorage.setItem('token', 'other-token'); api.request.mockResolvedValue({ ...ready, url: ready.url + '-other' }); await render('b'.repeat(64));
  await act(async () => resolve(ready)); expect(host.querySelector('video').src).toBe(ready.url + '-other');
});
test('unexpected origin never reaches the player or download link', async () => {
  api.request.mockResolvedValue({ ...ready, url: 'https://attacker.example/api/student/report-video/ticket' }); await render(); expect(host.querySelector('video')).toBeNull(); expect(host.querySelector('a[download]')).toBeNull(); expect(host.textContent).toContain('Адрес видео не подтверждён');
});
test('an account change before UI rerender blocks download and service mutation', async () => {
  api.request.mockResolvedValue(ready); await render(); localStorage.setItem('token', 'other-token');
  const click = new MouseEvent('click', { bubbles: true, cancelable: true });
  await act(async () => host.querySelector('a[download]').dispatchEvent(click)); expect(click.defaultPrevented).toBe(true);
  await act(async () => [...host.querySelectorAll('button')].find(button => button.textContent.includes('Обновить ссылку')).click()); expect(api.request).toHaveBeenCalledTimes(1);
});
test('URL validation rejects query credentials, paths and refreshes only after its lifetime', () => {
  for (const url of ['http://api.example.invalid/api/student/report-video/a', 'https://api.example.invalid/api/student/report-video/a?token=x', 'https://user@api.example.invalid/api/student/report-video/a', 'https://api.example.invalid/api/student/report-video/a/more']) expect(() => videoState({ ...ready, url }, 'https://api.example.invalid')).toThrow();
  const first = retainVideo(null, videoState(ready, 'https://api.example.invalid'), 1000), next = { ...ready, url: ready.url + '-new' };
  expect(retainVideo(first, next, 2000).url).toBe(first.url); expect(retainVideo(first, next, first.link_until + 1).url).toBe(next.url); expect(videoPollDelay(pending)).toBe(30000);
});
