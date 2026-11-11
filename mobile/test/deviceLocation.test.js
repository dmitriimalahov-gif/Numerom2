const test = require('node:test');
const assert = require('node:assert/strict');
const {DeviceLocationError, coordinates, createWebLocationAdapter, createNativeLocationAdapter} = require('../src/lib/deviceLocationCore');

const position = (latitude = 44.4, longitude = 26.1) => ({coords: {latitude, longitude, accuracy: 150}, timestamp: 1_700_000_000_000});
const tick = () => new Promise(resolve => setImmediate(resolve));
function webFixture() {
  let success, failure, options, removals = 0;
  const geolocation = {
    watchPosition(onPosition, onError, settings) { success = onPosition; failure = onError; options = settings; return 42; },
    clearWatch(id) { assert.equal(id, 42); removals++; },
  };
  return {geolocation, send: value => success(value), fail: value => failure(value), get removals() { return removals; }, get options() { return options; }};
}
function nativeFixture(permission = {granted: true}) {
  let success, failure, options, removals = 0, requests = 0, watches = 0;
  const location = {
    Accuracy: {Balanced: 3},
    async hasServicesEnabledAsync() { return true; },
    async getForegroundPermissionsAsync() { return permission; },
    async requestForegroundPermissionsAsync() { requests++; return permission; },
    async watchPositionAsync(settings, onPosition, onError) {
      watches++; options = settings; success = onPosition; failure = onError;
      return {remove() { removals++; }};
    },
  };
  return {location, send: value => success(value), fail: value => failure(value), get removals() { return removals; }, get requests() { return requests; }, get watches() { return watches; }, get options() { return options; }};
}

test('coordinates reject invalid or coerced values and preserve unknown accuracy as null', () => {
  for (const value of [position(NaN), position(Infinity), position(91), position(-91), position(0, 181), position('44')]) {
    assert.throws(() => coordinates(value), error => error instanceof DeviceLocationError && error.code === 'unavailable');
  }
  assert.throws(() => coordinates({...position(), timestamp: Infinity}), {code: 'unavailable'});
  assert.equal(coordinates({...position(), coords: {...position().coords, accuracy: -1}}).accuracy, null);
  assert.equal(coordinates({...position(), coords: {...position().coords, accuracy: NaN}}).accuracy, null);
  assert.equal(coordinates(position(-90, 180)).longitude, 180);
});

test('web rejects insecure and unavailable environments before asking for location', async () => {
  const f = webFixture();
  await assert.rejects(createWebLocationAdapter(() => ({secureContext: false, geolocation: f.geolocation})).locate(), {code: 'unsupported'});
  assert.equal(f.options, undefined);
  await assert.rejects(createWebLocationAdapter(() => ({secureContext: true})).locate(), {code: 'unsupported'});
});

test('web locate takes one position, disables high accuracy, and removes the watch', async () => {
  const f = webFixture();
  const pending = createWebLocationAdapter(() => ({secureContext: true, geolocation: f.geolocation})).locate();
  await tick(); f.send(position());
  assert.deepEqual(await pending, {latitude: 44.4, longitude: 26.1, accuracy: 150, timestamp: 1_700_000_000_000});
  assert.equal(f.options.enableHighAccuracy, false);
  assert.equal(f.removals, 1);
});

test('web stop is idempotent and ignores queued callbacks after stopping', async () => {
  const f = webFixture(); const values = []; const errors = [];
  const stop = await createWebLocationAdapter(() => ({secureContext: true, geolocation: f.geolocation})).watchLocation(v => values.push(v), e => errors.push(e));
  f.send(position()); stop(); stop(); f.send(position(45)); f.fail({code: 1});
  assert.equal(values.length, 1); assert.equal(errors.length, 0); assert.equal(f.removals, 1);
});

test('web permission errors are Russian, terminal, and never expose native error text', async () => {
  const f = webFixture(); const errors = [];
  await createWebLocationAdapter(() => ({secureContext: true, geolocation: f.geolocation})).watchLocation(() => assert.fail('must not deliver'), e => errors.push(e));
  f.fail({code: 1, message: 'private diagnostic'}); f.send(position());
  assert.equal(errors[0].code, 'denied'); assert.match(errors[0].message, /Разрешите/);
  assert.doesNotMatch(errors[0].message, /private diagnostic/); assert.equal(f.removals, 1);
});

test('native denial never starts a subscription or asks for background access', async () => {
  const f = nativeFixture({granted: false, canAskAgain: false});
  await assert.rejects(createNativeLocationAdapter(f.location).locate(), {code: 'denied'});
  assert.equal(f.requests, 0); assert.equal(f.watches, 0);
  f.location.getForegroundPermissionsAsync = async () => ({granted: false, canAskAgain: true});
  await assert.rejects(createNativeLocationAdapter(f.location).locate(), {code: 'denied'});
  assert.equal(f.requests, 1); assert.equal(f.watches, 0);
});

test('native disabled service is unavailable without a permission prompt', async () => {
  const f = nativeFixture({granted: false, canAskAgain: true}); f.location.hasServicesEnabledAsync = async () => false;
  await assert.rejects(createNativeLocationAdapter(f.location).locate(), {code: 'unavailable'});
  assert.equal(f.requests, 0); assert.equal(f.watches, 0);
});

test('native live updates use balanced foreground options and stop after an invalid fix', async () => {
  const f = nativeFixture(); const values = []; const errors = [];
  const stop = await createNativeLocationAdapter(f.location).watchLocation(v => values.push(v), e => errors.push(e));
  assert.equal(f.options.accuracy, f.location.Accuracy.Balanced);
  assert.equal(f.options.mayShowUserSettingsDialog, false);
  assert.ok(f.options.timeInterval >= 30_000 && f.options.distanceInterval >= 100);
  f.send(position()); f.send(position(Infinity)); f.send(position()); stop();
  assert.equal(values.length, 1); assert.equal(errors[0].code, 'unavailable'); assert.equal(f.removals, 1);
});

test('native one-shot cleans up even when the first fix arrives before the subscription handle', async () => {
  const f = nativeFixture(); let release; let removed = 0;
  f.location.watchPositionAsync = async (_options, success) => {
    success(position());
    return new Promise(resolve => { release = () => resolve({remove() { removed++; }}); });
  };
  const result = await createNativeLocationAdapter(f.location).locate();
  assert.equal(result.latitude, 44.4); release(); await tick();
  assert.equal(removed, 1);
});

test('a timed out native registration removes a late handle and discards its late coordinates', async () => {
  const f = nativeFixture(); let release; let success; let removed = 0; let delivered = 0;
  f.location.watchPositionAsync = async (_options, onPosition) => {
    success = onPosition;
    return new Promise(resolve => { release = () => resolve({remove() { removed++; }}); });
  };
  await assert.rejects(createNativeLocationAdapter(f.location, {timeoutMs: 10}).watchLocation(() => delivered++, () => assert.fail('registration must reject')), {code: 'timeout'});
  release(); await tick(); success(position());
  assert.equal(removed, 1); assert.equal(delivered, 0);
});

test('a registered watch without a first fix reports timeout and releases its subscription', async () => {
  const f = nativeFixture(); let reported;
  const failed = new Promise(resolve => { reported = resolve; });
  const stop = await createNativeLocationAdapter(f.location, {timeoutMs: 10}).watchLocation(() => assert.fail('no position'), reported);
  assert.equal((await failed).code, 'timeout'); stop(); assert.equal(f.removals, 1);
});

test('aborting one-shot lookup immediately clears the OS watch and rejects with AbortError', async () => {
  const f = webFixture(); const controller = new AbortController();
  const pending = createWebLocationAdapter(() => ({secureContext: true, geolocation: f.geolocation})).locate(controller.signal);
  await tick(); controller.abort();
  assert.equal(f.removals, 1);
  await assert.rejects(pending, {name: 'AbortError'});
  f.send(position()); assert.equal(f.removals, 1);
});

test('aborting a pending native permission prompt never starts a late subscription', async () => {
  const f = nativeFixture({granted: false, canAskAgain: true}); const controller = new AbortController(); let allow;
  f.location.requestForegroundPermissionsAsync = () => new Promise(resolve => { allow = () => resolve({granted: true}); });
  const pending = createNativeLocationAdapter(f.location).locate(controller.signal);
  await tick(); controller.abort(); await assert.rejects(pending, {name: 'AbortError'});
  allow(); await tick(); assert.equal(f.watches, 0);
});

test('aborting pending native watch registration removes its later handle without delivering coordinates', async () => {
  const f = nativeFixture(); const controller = new AbortController(); let release; let deliver; let removed = 0;
  f.location.watchPositionAsync = (_options, success) => {
    deliver = success;
    return new Promise(resolve => { release = () => resolve({remove() { removed++; }}); });
  };
  const pending = createNativeLocationAdapter(f.location).watchLocation(() => assert.fail('late callback'), () => {}, controller.signal);
  await tick(); controller.abort(); await assert.rejects(pending, {name: 'AbortError'});
  release(); await tick(); deliver(position()); assert.equal(removed, 1);
});
