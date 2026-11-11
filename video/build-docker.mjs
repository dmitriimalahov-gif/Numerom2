/** Build context contains explicitly selected public source only, no reports/audio/secrets. */
import {mkdir, copyFile, cp, rm} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const context = path.join(root, '.cache/docker-build');
await rm(context, {recursive: true, force: true});
await mkdir(path.join(context, 'video'), {recursive: true});
await mkdir(path.join(context, 'packages/full-report'), {recursive: true});
await mkdir(path.join(context, 'packages/brand'), {recursive: true});
for (const file of ['package.json', 'package-lock.json', 'render.mjs', 'manifest.mjs', 'assets.mjs', 'prepare-browser.mjs']) {
  await copyFile(path.join(root, file), path.join(context, 'video', file));
}
await cp(path.join(root, 'src'), path.join(context, 'video/src'), {recursive: true});
for (const file of ['full-report/schematics.js', 'full-report/package.json', 'brand/numerom-logo.svg']) {
  await copyFile(path.resolve(root, '../packages', file), path.join(context, 'packages', file));
}
await copyFile(path.join(root, 'Dockerfile'), path.join(context, 'Dockerfile'));
const child = spawn('docker', ['build', '--tag', 'numerom-report-video:4.0.538', context], {stdio: 'inherit'});
child.once('error', (error) => {console.error(error.message); process.exitCode = 1;});
child.once('exit', (code) => {process.exitCode = code ?? 1;});
