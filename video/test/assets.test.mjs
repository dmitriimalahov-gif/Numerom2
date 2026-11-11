import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, mkdir, writeFile, rm, symlink} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import {byteRange, startAssetServer} from '../assets.mjs';

const request = (url, options = {}) => new Promise((resolve, reject) => {
  const req = http.request(url, options, (res) => {const chunks = []; res.on('data', (part) => chunks.push(part));
    res.on('end', () => resolve({status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString()}));});
  req.on('error', reject); req.end();
});
test('single and suffix byte ranges are bounded; multipart and invalid ranges fail', () => {
  assert.deepEqual(byteRange('bytes=2-5', 10), {start: 2, end: 5, partial: true});
  assert.deepEqual(byteRange('bytes=-4', 10), {start: 6, end: 9, partial: true});
  assert.deepEqual(byteRange('bytes=3-', 10), {start: 3, end: 9, partial: true});
  assert.deepEqual(byteRange('bytes=0-100', 10), {start: 0, end: 9, partial: true});
  for (const header of ['bytes=11-', 'bytes=5-2', 'bytes=-0', 'bytes=0-2,4-6', 'bytes=-', 'bad']) assert.equal(byteRange(header, 10), null);
});
test('private server serves only allowlisted files with range support and no ambient project files', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'numerom-video-test-')); let server;
  try {
    const bundle = path.join(root, 'bundle'), audio = path.join(root, 'voice.m4a');
    await mkdir(bundle); await writeFile(audio, '0123456789'); await writeFile(path.join(bundle, 'index.html'), '<html>test</html>');
    await writeFile(path.join(root, 'secret.txt'), 'not-public'); await writeFile(path.join(bundle, 'app.js.map'), 'not-public');
    server = await startAssetServer([audio], bundle);
    assert.equal(new URL(server.origin).hostname, '127.0.0.1');
    const full = await request(server.audioSources[0]); assert.equal(full.status, 200); assert.equal(full.body, '0123456789');
    assert.equal(full.headers['cache-control'], 'no-store');
    assert.match(full.headers['content-security-policy'], /connect-src 'self'/);
    const range = await request(server.audioSources[0], {headers: {Range: 'bytes=2-5'}});
    assert.equal(range.status, 206); assert.equal(range.body, '2345'); assert.equal(range.headers['content-range'], 'bytes 2-5/10');
    const suffix = await request(server.audioSources[0], {headers: {Range: 'bytes=-2'}}); assert.equal(suffix.body, '89');
    assert.equal((await request(server.audioSources[0], {method: 'HEAD'})).body, '');
    assert.equal((await request(server.audioSources[0], {headers: {Range: 'bytes=20-'}})).status, 416);
    assert.equal((await request(server.audioSources[0], {headers: {Host: 'evil.example'}})).status, 403);
    assert.equal((await request(server.audioSources[0], {headers: {Origin: 'https://evil.example'}})).status, 403);
    assert.equal((await request(server.audioSources[0], {method: 'POST'})).status, 405);
    for (const url of [server.origin + '/secret.txt', server.serveUrl + '../../secret.txt', server.serveUrl + 'app.js.map']) assert.equal((await request(url)).status, 404);
    const concurrent = await Promise.all(Array.from({length: 8}, () => request(server.audioSources[0], {headers: {Range: 'bytes=1-3'}})));
    assert.ok(concurrent.every((result) => result.body === '123'));
    await server.close(); server = null;
  } finally {if (server) await server.close(); await rm(root, {recursive: true, force: true});}
});
test('bundle symlinks cannot expose non-allowlisted files', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'numerom-video-symlink-'));
  try {
    await mkdir(path.join(root, 'bundle')); await writeFile(path.join(root, 'voice.m4a'), 'audio');
    await writeFile(path.join(root, 'bundle/index.html'), '<html></html>');
    await symlink(path.join(root, 'voice.m4a'), path.join(root, 'bundle/escape.m4a'));
    await assert.rejects(startAssetServer([path.join(root, 'voice.m4a')], path.join(root, 'bundle')), /symlinks/);
  } finally {await rm(root, {recursive: true, force: true});}
});
