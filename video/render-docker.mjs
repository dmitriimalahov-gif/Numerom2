/** Same manifest/CLI as render.mjs, isolated Linux runtime for host compositor failures. */
import {spawn} from 'node:child_process';
import {mkdtemp, mkdir, readFile, writeFile, stat, copyFile, chmod, rm, access} from 'node:fs/promises';
import {constants} from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {parseArguments} from './render.mjs';
import {validateManifest} from './manifest.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
export const IMAGE = 'numerom-report-video:4.0.538';

export function dockerArguments({name, directory, previewSeconds, still}) {
  if (!/^[a-z0-9-]+$/.test(name) || !path.isAbsolute(directory) || directory.includes(',')) throw new Error('Invalid isolated render directory');
  return ['run', '--rm', '--pull', 'never', '--name', name,
    '--network', 'none', '--cpus', '2', '--memory', '2g', '--pids-limit', '256',
    '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--shm-size', '128m',
    '--mount', `type=bind,src=${path.join(directory, 'input')},dst=/input,readonly`,
    '--mount', `type=bind,src=${path.join(directory, 'output')},dst=/out`,
    IMAGE, '--input', '/input/manifest.json', '--output', '/out/report.mp4',
    ...(still ? ['--still', '/out/preview.png'] : []),
    ...(previewSeconds ? ['--preview-seconds', String(previewSeconds)] : [])];
}

function command(args, stdio = 'inherit') {
  return new Promise((resolve, reject) => {
    const child = spawn('docker', args, {stdio});
    child.once('error', reject);
    child.once('exit', (code, signal) => code === 0 ? resolve() : reject(new Error(`Isolated render exited ${signal || code}`)));
  });
}

export async function renderDocker(options) {
  const source = options['--input'];
  if ((await stat(source)).size > 5 * 1024 * 1024) throw new Error('Manifest exceeds 5 MiB');
  // Canonical diagrams are derived here before the raw snapshot is discarded.
  const manifest = validateManifest(JSON.parse(await readFile(source, 'utf8')));
  const destinations = [options['--output'], options['--still']].filter(Boolean);
  for (const destination of destinations) {
    try {await access(destination); throw new Error('Output already exists; use a new pending output path');}
    catch (error) {if (error.code !== 'ENOENT') throw error;}
    await mkdir(path.dirname(destination), {recursive: true});
  }
  // --pull never: missing images fail before personal data is copied.
  try {await command(['image', 'inspect', IMAGE, '--format', '{{.Id}}'], 'ignore');}
  catch {throw new Error('Prepared video image unavailable; check Docker and run node video/build-docker.mjs');}
  await mkdir(path.join(ROOT, '.cache/jobs'), {recursive: true, mode: 0o700});
  const directory = await mkdtemp(path.join(ROOT, '.cache/jobs/render-'));
  await chmod(directory, 0o700);
  const name = 'numerom-report-' + crypto.randomUUID();
  let interrupted = false;
  const interrupt = () => {interrupted = true; void command(['stop', '--time', '5', name], 'ignore').catch(() => {});};
  process.on('SIGINT', interrupt); process.on('SIGTERM', interrupt);
  try {
    await mkdir(path.join(directory, 'input'), {mode: 0o755});
    await mkdir(path.join(directory, 'output'), {mode: 0o777});
    await chmod(path.join(directory, 'output'), 0o777);
    for (let index = 0; index < manifest.chapters.length; index++) {
      if (interrupted) throw new Error('Render cancelled');
      const chapter = manifest.chapters[index], metadata = await stat(chapter.audioPath);
      if (!metadata.isFile() || metadata.size === 0 || metadata.size > 512 * 1024 * 1024) throw new Error('Invalid verified narration file');
      const file = `audio-${index}.m4a`, target = path.join(directory, 'input', file);
      await copyFile(chapter.audioPath, target, constants.COPYFILE_EXCL);
      await chmod(target, 0o644);
      chapter.audioPath = '/input/' + file;
    }
    await writeFile(path.join(directory, 'input/manifest.json'), JSON.stringify(manifest), {mode: 0o644});
    if (interrupted) throw new Error('Render cancelled');
    await command(dockerArguments({name, directory, previewSeconds: options.previewSeconds, still: !!options['--still']}));
    if (interrupted) throw new Error('Render cancelled');
    if (options['--still']) await copyFile(path.join(directory, 'output/preview.png'), options['--still'], constants.COPYFILE_EXCL);
    await copyFile(path.join(directory, 'output/report.mp4'), options['--output'], constants.COPYFILE_EXCL);
  } finally {
    process.removeListener('SIGINT', interrupt); process.removeListener('SIGTERM', interrupt);
    // Limit cleanup to this random job. No unrelated containers or volumes touched.
    await command(['rm', '--force', name], 'ignore').catch(() => {});
    await rm(directory, {recursive: true, force: true});
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  Promise.resolve().then(() => renderDocker(parseArguments(process.argv.slice(2)))).catch((error) => {
    process.stderr.write(String(error?.message || 'Isolated render failed') + '\n'); process.exitCode = 1;
  });
}
