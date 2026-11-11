import test from 'node:test';
import assert from 'node:assert/strict';
import {dockerArguments, IMAGE} from '../render-docker.mjs';

test('Docker runtime is offline, bounded and mounts only job input/output', () => {
  const args = dockerArguments({name: 'numerom-report-test', directory: '/tmp/one job', previewSeconds: 8, still: true});
  for (const [flag, value] of [['--network', 'none'], ['--pull', 'never'], ['--cpus', '2'], ['--memory', '2g'], ['--cap-drop', 'ALL']]) {
    assert.equal(args[args.indexOf(flag) + 1], value);
  }
  assert.deepEqual(args.filter((_, i) => args[i - 1] === '--mount'), [
    'type=bind,src=/tmp/one job/input,dst=/input,readonly',
    'type=bind,src=/tmp/one job/output,dst=/out',
  ]);
  assert.equal(args.includes('/var/run/docker.sock'), false);
  assert.equal(args.includes('--privileged'), false);
  assert.ok(args.includes(IMAGE));
  assert.equal(args.at(-1), '8');
});
test('Docker job cannot inject extra mounts or container names', () => {
  assert.throws(() => dockerArguments({name: 'bad name', directory: '/tmp/job'}), /Invalid/);
  assert.throws(() => dockerArguments({name: 'fine', directory: '/tmp/job,other'}), /Invalid/);
  assert.throws(() => dockerArguments({name: 'fine', directory: 'relative'}), /Invalid/);
});
