const TIMEOUT_MS = 20_000;
const WEB_OPTIONS = {enableHighAccuracy: false, maximumAge: 60_000, timeout: TIMEOUT_MS};
const MESSAGES = {
  denied: 'Доступ к геолокации запрещён. Разрешите его в настройках приложения или сайта либо укажите город вручную.',
  unsupported: 'Геолокация недоступна на этом устройстве или в этом браузере. Укажите город вручную.',
  timeout: 'Не удалось определить местоположение вовремя. Попробуйте ещё раз или укажите город вручную.',
  unavailable: 'Местоположение сейчас недоступно. Проверьте, включена ли геолокация, или укажите город вручную.',
};

class DeviceLocationError extends Error {
  constructor(code, message = MESSAGES[code]) {
    super(message);
    this.name = 'DeviceLocationError';
    this.code = code;
  }
}

function locationError(error) {
  if (error instanceof DeviceLocationError) return error;
  const code = error?.code;
  const reason = `${code ?? ''} ${typeof error === 'string' ? error : error?.message ?? ''}`;
  if (code === 1 || /denied|permission|unauthori[sz]ed|not authori[sz]ed/i.test(reason)) return new DeviceLocationError('denied');
  if (code === 3 || /timeout|timed out/i.test(reason)) return new DeviceLocationError('timeout');
  if (/unsupported|not supported|ERR_UNAVAILABLE|UnavailabilityError/i.test(reason)) return new DeviceLocationError('unsupported');
  return new DeviceLocationError('unavailable');
}

function coordinates(position) {
  const {latitude, longitude, accuracy} = position?.coords ?? {};
  const timestamp = position?.timestamp;
  if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90 ||
      !Number.isFinite(longitude) || longitude < -180 || longitude > 180 ||
      !Number.isFinite(timestamp) || timestamp < 0) throw new DeviceLocationError('unavailable');
  return {latitude, longitude, accuracy: Number.isFinite(accuracy) && accuracy >= 0 ? accuracy : null, timestamp};
}

function abortError() {
  const error = new DeviceLocationError('unavailable', 'Определение местоположения остановлено.');
  error.name = 'AbortError';
  return error;
}

function checkAbort(signal) {
  if (signal?.aborted) throw abortError();
}

function withSignal(operation, signal) {
  return new Promise((resolve, reject) => {
    try { checkAbort(signal); } catch (error) { reject(error); return; }
    const abort = () => reject(abortError());
    signal?.addEventListener('abort', abort, {once: true});
    Promise.resolve().then(() => { checkAbort(signal); return operation(); }).then(value => {
      signal?.removeEventListener('abort', abort);
      if (signal?.aborted) reject(abortError()); else resolve(value);
    }, error => { signal?.removeEventListener('abort', abort); reject(error); });
  });
}

/** One foreground subscription; terminal errors stop it and late callbacks are ignored. */
function startWatch(register, onPosition, onError, timeoutMs, signal) {
  return new Promise((resolve, reject) => {
    try { checkAbort(signal); } catch (error) { reject(error); return; }
    let active = true;
    let registered = false;
    let received = false;
    let remove;
    let timer;
    const stop = () => {
      if (!active) return;
      active = false;
      clearTimeout(timer);
      signal?.removeEventListener('abort', abort);
      if (remove) remove();
    };
    const fail = error => {
      if (!active) return;
      const failure = locationError(error);
      stop();
      if (registered) onError(failure);
      else reject(failure);
    };
    const deliver = raw => {
      if (!active) return;
      let value;
      try { value = coordinates(raw); } catch (error) { fail(error); return; }
      received = true;
      if (registered) clearTimeout(timer);
      onPosition(value);
    };
    const abort = () => fail(abortError());
    signal?.addEventListener('abort', abort, {once: true});
    timer = setTimeout(() => fail(new DeviceLocationError('timeout')), timeoutMs);
    Promise.resolve().then(() => { checkAbort(signal); return register(deliver, fail); }).then(cleanup => {
      remove = cleanup;
      // Registration can finish after a timeout or an early native error.
      if (!active) { remove(); return; }
      registered = true;
      if (received) clearTimeout(timer);
      resolve(stop);
    }, fail);
  });
}

function firstPosition(register, timeoutMs, signal) {
  return new Promise((resolve, reject) => {
    let stop;
    let complete = false;
    const finish = (error, value) => {
      if (complete) return;
      complete = true;
      if (stop) stop();
      if (error) reject(error); else resolve(value);
    };
    startWatch(register, value => finish(null, value), error => finish(error), timeoutMs, signal)
      .then(cleanup => { stop = cleanup; if (complete) stop(); }, error => finish(error));
  });
}

function createWebLocationAdapter(environment, {timeoutMs = TIMEOUT_MS} = {}) {
  const prepare = signal => {
    checkAbort(signal);
    const {secureContext, geolocation} = environment();
    if (!secureContext) throw new DeviceLocationError('unsupported', 'Геолокация доступна только на защищённом сайте HTTPS. Укажите город вручную.');
    if (!geolocation?.watchPosition || !geolocation?.clearWatch) throw new DeviceLocationError('unsupported');
    return (success, failure) => {
      const id = geolocation.watchPosition(success, failure, {...WEB_OPTIONS, timeout: timeoutMs});
      return () => geolocation.clearWatch(id);
    };
  };
  return {
    async locate(signal) { return firstPosition(prepare(signal), timeoutMs, signal); },
    async watchLocation(onPosition, onError, signal) { return startWatch(prepare(signal), onPosition, onError, timeoutMs, signal); },
  };
}

function createNativeLocationAdapter(location, {timeoutMs = TIMEOUT_MS} = {}) {
  const prepare = async signal => {
    try {
      checkAbort(signal);
      if (!location?.watchPositionAsync || !location?.requestForegroundPermissionsAsync) throw new DeviceLocationError('unsupported');
      if (!await withSignal(() => location.hasServicesEnabledAsync(), signal)) throw new DeviceLocationError('unavailable');
      let permission = await withSignal(() => location.getForegroundPermissionsAsync(), signal);
      if (!permission.granted && permission.canAskAgain !== false) permission = await withSignal(() => location.requestForegroundPermissionsAsync(), signal);
      checkAbort(signal);
      if (!permission.granted) throw new DeviceLocationError('denied');
      return async (success, failure) => {
        checkAbort(signal);
        const subscription = await location.watchPositionAsync({
          accuracy: location.Accuracy.Balanced,
          distanceInterval: 250,
          timeInterval: 30_000,
          mayShowUserSettingsDialog: false,
        }, success, failure);
        return () => subscription.remove();
      };
    } catch (error) { throw locationError(error); }
  };
  return {
    async locate(signal) { return firstPosition(await prepare(signal), timeoutMs, signal); },
    async watchLocation(onPosition, onError, signal) { return startWatch(await prepare(signal), onPosition, onError, timeoutMs, signal); },
  };
}

module.exports = {DeviceLocationError, coordinates, createWebLocationAdapter, createNativeLocationAdapter};
