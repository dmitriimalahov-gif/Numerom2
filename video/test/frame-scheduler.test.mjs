import test from 'node:test';
import assert from 'node:assert/strict';
import {installFrameScheduler} from '../src/frame-scheduler.mjs';

function fakeWindow() {
  let next = 0;
  const frames = new Map(), timers = new Map();
  return {frames, timers, scope: {remotion_puppeteerTimeout: 60000, performance: {now: () => 100},
    requestAnimationFrame: (fn) => {frames.set(++next, fn); return next;},
    cancelAnimationFrame: (id) => frames.delete(id),
    setTimeout: (fn) => {timers.set(++next, fn); return next;}, clearTimeout: (id) => timers.delete(id)}};
}
test('normal native animation frame runs once and cancels fallback', () => {
  const {scope, frames, timers} = fakeWindow(); installFrameScheduler(scope);
  const calls = []; const id = scope.requestAnimationFrame((t) => calls.push(t));
  const fallback = [...timers.values()][0]; frames.get(id)(25); fallback();
  assert.deepEqual(calls, [25]); assert.equal(timers.size, 0); assert.equal(frames.size, 0);
});
test('stalled native frame falls back once, without inventing video frame numbers', () => {
  const {scope, frames, timers} = fakeWindow(); installFrameScheduler(scope);
  const calls = []; const id = scope.requestAnimationFrame((t) => calls.push(t));
  const native = frames.get(id); [...timers.values()][0](); native(120);
  assert.deepEqual(calls, [100]); assert.equal(timers.size, 0); assert.equal(frames.size, 0);
});
test('cancellation and disposal prevent both pending callback paths', () => {
  const {scope, frames, timers} = fakeWindow(); const dispose = installFrameScheduler(scope);
  let called = false; const id = scope.requestAnimationFrame(() => {called = true;});
  const native = frames.get(id), fallback = [...timers.values()][0];
  scope.cancelAnimationFrame(id); native(10); fallback(); assert.equal(called, false);
  scope.requestAnimationFrame(() => {called = true;}); dispose();
  assert.equal(frames.size, 0); assert.equal(timers.size, 0);
});
test('browser preview and normal pages retain native scheduling unchanged', () => {
  const {scope} = fakeWindow(); delete scope.remotion_puppeteerTimeout;
  const native = scope.requestAnimationFrame; installFrameScheduler(scope);
  assert.equal(scope.requestAnimationFrame, native);
});
