/** Shared HTTP and session boundaries. No browser, React or native dependencies. */
function resolveBackendUrl(configured, location) {
  if (configured && configured.trim()) {
    const value = configured.trim().replace(/\/+$/, '').replace(/\/api$/i, '');
    let url;
    try { url = new URL(value); } catch { throw new Error('Укажите полный HTTP(S) адрес сервера'); }
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error('Укажите HTTP(S) адрес сервера без пароля, параметров и якоря');
    return value;
  }
  if (!location) return 'http://localhost:8000';
  const { protocol, hostname, port } = location;
  const host = hostname.includes(':') && !hostname.startsWith('[') ? `[${hostname}]` : hostname;
  const devPorts = ['3000', '5173', '4173', '4174', '5128', '5129'];
  const target = devPorts.includes(port) ? (port === '5129' ? '8002' : '8000') : port;
  return `${protocol}//${host}${target ? `:${target}` : ''}`;
}
class ApiError extends Error {
  constructor(message, status = 0, code = 'http') { super(message); this.name = 'ApiError'; this.status = status; this.code = code; }
}
function validateBirthDate(value) {
  if (!/^\d{2}\.\d{2}\.\d{4}$/.test(value)) return false;
  const [day, month, year] = value.split('.').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return year >= 1900 && date <= new Date() && date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day;
}
function createApiClient({ baseUrl, getBaseUrl, onConnectionFailure, getToken = () => null, fetchImpl = (...args) => fetch(...args), timeoutMs = 15000, onUnauthorized = () => {}, onInsufficientCredits = () => {} }) {
  async function request(path, { method = 'GET', body, signal, auth = true, timeoutMs: requestTimeoutMs = timeoutMs } = {}, retried = false) {
    if (!path.startsWith('/') || path.startsWith('//')) throw new Error('API path must be relative');
    const token = auth ? getToken() : null;
    const origin = resolveBackendUrl(getBaseUrl ? await getBaseUrl() : baseUrl);
    if (auth && token !== getToken()) throw new ApiError('Запрос отменён', 0, 'cancelled');
    const root = `${origin}/api`;
    const controller = new AbortController();
    let timedOut = false;
    let interrupt;
    const interrupted = new Promise((_, reject) => { interrupt = reject; });
    const abort = () => { controller.abort(); interrupt(new ApiError('Запрос отменён', 0, 'cancelled')); };
    if (signal?.aborted) throw new ApiError('Запрос отменён', 0, 'cancelled');
    signal?.addEventListener('abort', abort, { once: true });
    // A request may wait up to 2 minutes: the server renders a long report's PDF for up to 90 s.
    const timer = setTimeout(() => { timedOut = true; controller.abort(); interrupt(new ApiError('Сервер не ответил вовремя', 0, 'timeout')); }, Number.isFinite(requestTimeoutMs) && requestTimeoutMs > 0 ? Math.min(requestTimeoutMs,120000) : timeoutMs);
    try {
      const {response,data} = await Promise.race([(async () => {
       const response = await fetchImpl(`${root}${path}`, {
        method, signal: controller.signal, redirect: 'error',
        headers: { Accept: 'application/json', ...(body !== undefined ? {'Content-Type': 'application/json'} : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        ...(body !== undefined ? {body: JSON.stringify(body)} : {}),
      });
       let data = null;
       try { data = await response.json(); } catch { /* Empty or non-JSON error body. */ }
       return {response,data};
      })(), interrupted]);
      if (!response.ok) {
        if (response.status === 401 && auth && token) await onUnauthorized(token);
        if (response.status === 402 && token && token === getToken()) {
          // UI notification failures must not hide the original payment refusal.
          try { await onInsufficientCredits(token); } catch {}
        }
        const detail = data?.detail;
        const message = response.status >= 500 ? 'Сервер временно недоступен. Попробуйте позже.' : Array.isArray(detail) ? detail.map(item => item.msg).join('. ') : typeof detail === 'string' ? detail : typeof detail?.message === 'string' ? detail.message : 'Не удалось выполнить запрос';
        const code = ['full_report_profile_changed','full_report_attempt_frozen'].includes(detail?.code) ? detail.code : undefined;
        const failure = new ApiError(message, response.status, code);
        if (code === 'full_report_attempt_frozen' && /^[a-f0-9]{64}$/.test(detail?.order_id || '')) failure.orderId = detail.order_id;
        throw failure;
      }
      if (data === null && response.status !== 204) throw new ApiError('Некорректный ответ сервера', response.status, 'response');
      return data;
    } catch (error) {
      const failure = error instanceof ApiError ? error : new ApiError(timedOut ? 'Сервер не ответил вовремя' : controller.signal.aborted ? 'Запрос отменён' : 'Не удалось связаться с NumerOM. Проверьте соединение или попробуйте позже.', 0, timedOut ? 'timeout' : controller.signal.aborted ? 'cancelled' : 'network');
      if (!retried && !signal?.aborted && onConnectionFailure &&
          (failure.status >= 500 || ['network','timeout'].includes(failure.code))) {
        clearTimeout(timer);
        let changed = false;
        try { changed = await onConnectionFailure(origin); } catch {}
        // Never repeat a charge, registration or upload after an ambiguous reply.
        if (changed && method === 'GET' && (!auth || token === getToken()))
          return request(path, {method,body,signal,auth,timeoutMs:requestTimeoutMs}, true);
      }
      throw failure;
    } finally {
      clearTimeout(timer); signal?.removeEventListener('abort', abort);
    }
  }
  return {
    request,
    login: (email, password) => request('/auth/login', { method: 'POST', body: {email: email.trim(), password}, auth: false }),
    requestPasswordReset: email => request('/auth/forgot-password', { method: 'POST', body: {email: email.trim()}, auth: false }),
    resetPassword: (token, password) => request('/auth/reset-password', { method: 'POST', body: {token, password}, auth: false }),
    register: body => request('/auth/register', { method: 'POST', body, auth: false }),
    profile: () => request('/user/profile-v2'),
    updateProfile: body => request('/user/profile-v2', { method: 'PATCH', body }),
    lessons: () => request('/learning-v2/lessons'),
    lesson: id => request(`/learning-v2/lessons/${encodeURIComponent(id)}`),
    calculationCosts: () => request('/numerology/costs'),
    toolCatalog: () => request('/numerology/tools/catalog'),
    toolHistory: () => request('/numerology/tools/history'),
    calculateTool: body => request('/numerology/tools', {method:'POST',body}),
    relationshipCatalog: () => request('/numerology/relationships/catalog'),
    relationshipHistory: () => request('/numerology/relationships/history'),
    calculateRelationships: body => request('/numerology/relationships', {method:'POST',body}),
    latestPersonalNumbers: () => request('/numerology/personal-numbers/latest'),
    personalNumbers: birthDate => validateBirthDate(birthDate) ? request(`/numerology/personal-numbers?birth_date=${encodeURIComponent(birthDate)}`, { method: 'POST' }) : Promise.reject(new ApiError('Введите существующую дату: ДД.ММ.ГГГГ', 422, 'validation')),
  };
}
function createSessionController({ api, storage }) {
  let token = null, epoch = 0, storageQueue = Promise.resolve();
  let state = { status: 'loading', user: null, error: null };
  const listeners = new Set();
  const publish = next => { state = next; listeners.forEach(listener => listener()); };
  const persist = operation => { const next = storageQueue.then(operation, operation); storageQueue = next.catch(() => {}); return next; };
  async function signOut() {
    const version = ++epoch; token = null; publish({status: 'signedOut', user: null, error: null});
    try { await persist(() => storage.remove()); } catch { if (version === epoch) publish({...state, needsSignOutRetry: true, error: 'Не удалось удалить сохранённый вход. Повторите выход.'}); throw new Error('Не удалось удалить сохранённый вход'); }
  }
  async function authenticate(method, args) {
    const version = ++epoch;
    try {
      const result = await (typeof method==='function'?method(...args):api[method](...args));
      if (!result?.access_token || !result.user?.id) throw new ApiError('Некорректный ответ входа', 200, 'response');
      if (version !== epoch) return;
      await persist(() => version === epoch ? storage.set(result.access_token) : undefined);
      if (version !== epoch) return;
      token = result.access_token;
      publish({status: 'signedIn', user: result.user, error: null});
    } catch (error) {
      if (version === epoch) { token = null; publish({status: 'signedOut', user: null, error: error.message}); }
      throw error;
    }
  }
  async function restore(unlock = false) {
    const version = ++epoch;
    publish({status: 'loading', user: null, error: null});
    try {
      const stored = await persist(() => storage.get(unlock));
      if (version !== epoch) return;
      token = stored;
      if (!token) { publish({status: 'signedOut', user: null, error: null}); return; }
      const user = await api.profile();
      if (version === epoch) publish({status: 'signedIn', user, error: null});
    } catch (error) {
      if (version !== epoch) return;
      if (error.status === 401) await signOut();
      else { token = null; publish({status: error.code === 'biometric_locked' ? 'locked' : 'unavailable', user: null, error: error.message}); }
    }
  }
  return {
    getToken: () => token, getSnapshot: () => state,
    subscribe: listener => { listeners.add(listener); return () => listeners.delete(listener); },
    lock: () => { ++epoch; token = null; publish({status:'locked',user:null,error:null}); },
    restore, signOut, signInWith: loader => authenticate(loader, []), signIn: (email, password) => authenticate('login', [email, password]),
    signUp: data => authenticate('register', [data]),
    invalidate: async rejectedToken => { if (token && token === rejectedToken) await signOut(); },
    refresh: async () => {
      const version = epoch;
      const user = await api.profile();
      if (version === epoch && token) publish({status:'signedIn', user, error:null});
    },
  };
}
module.exports = { resolveBackendUrl, createApiClient, ApiError, createSessionController, validateBirthDate, ...require('./payments'), ...require('./relationships'), ...require('./number-tools') };
