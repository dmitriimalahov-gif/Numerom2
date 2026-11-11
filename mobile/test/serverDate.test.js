const {test} = require('node:test');
const assert = require('node:assert/strict');
const {serverDate} = require('../src/lib/serverDate');
test('legacy UTC timestamps and explicit offsets identify the same instant', () => {
  for (const value of ['2026-10-15T22:03:12', '2026-10-15T22:03:12Z', '2026-10-16T01:03:12+03:00']) {
    assert.equal(serverDate(value).toISOString(), '2026-10-15T22:03:12.000Z');
  }
  assert.equal(serverDate('2026-10-15T22:03:12.123456').toISOString(), '2026-10-15T22:03:12.123Z');
  assert.equal(serverDate('invalid'), null);
  assert.equal(serverDate(undefined), null);
});
