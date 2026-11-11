/**
 * Headless Chromium on this macOS host can expose a visible page while its
 * display-link never fires requestAnimationFrame. Remotion then waits forever
 * even though React has registered the composition and committed its layout.
 *
 * Keep native scheduling first, with a bounded fallback in server renders only.
 * This schedules readiness callbacks, not video time: all visual motion uses
 * Remotion's explicit frame number. Remotion still waits for image decoding and
 * captures the browser's rendered DOM for every requested frame.
 */
export function installFrameScheduler(scope, delay = 40) {
  if (!scope || typeof scope.remotion_puppeteerTimeout !== 'number'
    || typeof scope.requestAnimationFrame !== 'function') return () => {};
  const request = scope.requestAnimationFrame.bind(scope);
  const cancel = scope.cancelAnimationFrame.bind(scope);
  const pending = new Map();
  scope.requestAnimationFrame = (callback) => {
    let id;
    const finish = (time) => {
      const timer = pending.get(id);
      if (timer === undefined) return;
      pending.delete(id);
      scope.clearTimeout(timer);
      cancel(id);
      callback(time);
    };
    id = request(finish);
    pending.set(id, scope.setTimeout(() => finish(scope.performance.now()), delay));
    return id;
  };
  scope.cancelAnimationFrame = (id) => {
    const timer = pending.get(id);
    if (timer !== undefined) {scope.clearTimeout(timer); pending.delete(id);}
    cancel(id);
  };
  return () => {
    for (const [id, timer] of pending) {scope.clearTimeout(timer); cancel(id);}
    pending.clear();
    scope.requestAnimationFrame = request;
    scope.cancelAnimationFrame = cancel;
  };
}

if (typeof window !== 'undefined') installFrameScheduler(window);
