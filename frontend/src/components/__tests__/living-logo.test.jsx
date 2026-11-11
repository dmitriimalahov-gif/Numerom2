import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { Brand } from '../NumeromIdentity';

let host, root, media;
const render = async element => { await act(async () => root.render(element)); };
const finish = async () => { await act(async () => jest.advanceTimersByTime(4400)); };
const click = async element => { await act(async () => element.dispatchEvent(new MouseEvent('click', { bubbles: true }))); };
// React schedules its own act work: inspect only the animation's timers.
const expectNoAwakeningTimers = () => {
  setTimeout.mock.calls.forEach(([, delay], index) => {
    if (delay === 4400) expect(clearTimeout).toHaveBeenCalledWith(setTimeout.mock.results[index].value);
  });
};

beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  jest.useFakeTimers('legacy');
  media = { matches: false, addEventListener: jest.fn(), removeEventListener: jest.fn() };
  window.matchMedia = jest.fn(() => media);
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  jest.useRealTimers();
  delete window.IntersectionObserver;
  jest.restoreAllMocks();
});

test('awakens once, settles, and replays with a new planetary palette', async () => {
  await render(<Brand />);
  const brand = host.querySelector('.nm-brand');
  expect(brand.dataset.awake).toBe('true');
  expect(host.querySelector('[role="img"]').getAttribute('aria-label')).toBe('NumerOM — Numbers Reveal');
  expect(host.querySelector('img').getAttribute('src')).toContain('/images/brand/numerom-logo.svg');
  await finish();
  expect(brand.dataset.awake).toBe('false');
  expectNoAwakeningTimers();
  await click(host.querySelector('button'));
  expect(brand.dataset.awake).toBe('true');
  expect(brand.dataset.palette).toBe('1');
  await click(host.querySelector('button'));
  expect(brand.dataset.palette).toBe('1');
  await finish();
  expect(brand.dataset.awake).toBe('false');
});

test('a linked logo retains one control and replays on keyboard focus without hijacking navigation', async () => {
  const navigate = jest.fn();
  await render(<a href="#home" onClick={navigate}><Brand /></a>);
  expect(host.querySelector('button')).toBeNull();
  await finish();
  await act(async () => host.querySelector('a').focus());
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('true');
  await click(host.querySelector('a'));
  expect(navigate).toHaveBeenCalledTimes(1);
  expect(host.querySelector('a').getAttribute('href')).toBe('#home');
});

test('reduced motion removes the replay control and cancels an active awakening immediately', async () => {
  await render(<Brand />);
  media.matches = true;
  const change = media.addEventListener.mock.calls.find(([event]) => event === 'change')[1];
  await act(async () => change());
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('false');
  expect(host.querySelector('button')).toBeNull();
  expectNoAwakeningTimers();
});

test('a compact logo remains static and has no extra tab stop', async () => {
  await render(<Brand compact />);
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('false');
  expect(host.querySelector('button')).toBeNull();
  expectNoAwakeningTimers();
});

test('an offscreen logo waits for visibility before playing its only introduction', async () => {
  let notify;
  const disconnect = jest.fn();
  window.IntersectionObserver = jest.fn(callback => {
    notify = callback;
    return { observe: jest.fn(), disconnect };
  });
  await render(<Brand />);
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('false');
  await act(async () => notify([{ isIntersecting: true }]));
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('true');
  expect(disconnect).toHaveBeenCalledTimes(1);
  await finish();
  expectNoAwakeningTimers();
});

test('switching away settles the artwork and unmount releases timers and preference listeners', async () => {
  await render(<Brand />);
  jest.spyOn(document, 'hidden', 'get').mockReturnValue(true);
  await act(async () => document.dispatchEvent(new Event('visibilitychange')));
  expect(host.querySelector('.nm-brand').dataset.awake).toBe('false');
  expectNoAwakeningTimers();
  await act(async () => root.render(null));
  expect(media.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function));
  expectNoAwakeningTimers();
});
