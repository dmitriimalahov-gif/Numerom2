const { test } = require('node:test');
const assert = require('node:assert/strict');
const Plugin = require('./DirectoryReadGuardPlugin');

test('known ancestor directories return EISDIR without opening the protected directory', async () => {
  let setup;
  let reads = 0;
  const compiler = {
    hooks: { afterEnvironment: { tap(_name, fn) { setup = fn; } } },
    inputFileSystem: { readFile() { reads++; throw new Error('directory opened'); } },
  };
  new Plugin('/Users/example/Desktop/numerom/frontend').apply(compiler);
  setup();
  await new Promise(resolve => compiler.inputFileSystem.readFile('/Users/example/Desktop', error => {
    assert.equal(error.code, 'EISDIR');
    assert.equal(reads, 0);
    resolve();
  }));
});

test('source files retain the original reader, receiver, options and result', async () => {
  let setup;
  const fileSystem = { readFile(filename, options, callback) {
    assert.equal(this, fileSystem);
    assert.equal(filename, '/project/frontend/src/App.js');
    assert.equal(options, 'utf8');
    callback(null, 'source');
  } };
  new Plugin('/project/frontend').apply({ inputFileSystem: fileSystem,
    hooks: { afterEnvironment: { tap(_name, fn) { setup = fn; } } } });
  setup();
  await new Promise(resolve => fileSystem.readFile('/project/frontend/src/App.js', 'utf8', (error, value) => {
    assert.equal(error, null);
    assert.equal(value, 'source');
    resolve();
  }));
});
