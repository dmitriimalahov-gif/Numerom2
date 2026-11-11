const {test} = require('node:test');
const assert = require('node:assert/strict');
const {recoveryToken, passwordError} = require('../src/lib/recovery');
test('recovery code is read only from a valid fragment, never from query parameters', () => {
 const token = 'A'.repeat(43);
 assert.equal(recoveryToken(`https://example.org/reset-password#token=${token}`), token);
 assert.equal(recoveryToken(`numerom://reset-password#token=${token}`), token);
 assert.equal(recoveryToken(`https://example.org/reset-password?token=${token}`), '');
 assert.equal(recoveryToken('https://example.org/reset-password#token=bad'), '');
 assert.equal(recoveryToken(null), '');
});
test('password validation respects UTF-8 bcrypt limit and matching confirmation', () => {
 assert.equal(passwordError('a'.repeat(72), 'a'.repeat(72)), '');
 assert.equal(passwordError('я'.repeat(36), 'я'.repeat(36)), '');
 assert.ok(passwordError('я'.repeat(37), 'я'.repeat(37)));
 assert.ok(passwordError('short', 'short'));
 assert.ok(passwordError('long password', 'different password'));
});
