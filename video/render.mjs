import {bundle} from '@remotion/bundler';
import {openBrowser, selectComposition, renderMedia, renderStill, makeCancelSignal} from '@remotion/renderer';
import {readFile, mkdir, stat, writeFile, access, unlink} from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import schematics from '../packages/full-report/schematics.js';
import {validateManifest, browserProps} from './manifest.mjs';
import {startAssetServer} from './assets.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const CACHE = path.join(ROOT, '.cache');
const VERSION = '4.0.538';
const SOURCE_FILES = ['render.mjs', 'src/index.jsx', 'src/ReportVideo.jsx', 'src/timeline.mjs', 'src/layout.mjs', 'src/directing.mjs', 'src/motion.mjs', 'src/frame-scheduler.mjs', 'package-lock.json', '../packages/full-report/schematics.js', '../packages/brand/numerom-logo.svg'];

export function parseArguments(args) {
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i], value = args[i + 1];
    if (!['--input', '--output', '--still', '--preview-seconds'].includes(key) || !value || options[key] !== undefined) throw new Error('Expected --input, --output, optional --still and --preview-seconds');
    options[key] = value;
  }
  for (const name of ['--input', '--output']) if (!options[name] || !path.isAbsolute(options[name])) throw new Error(`${name} must be an absolute local path`);
  if (!options['--input'].endsWith('.json') || !options['--output'].endsWith('.mp4')) throw new Error('Expected JSON input and MP4 output');
  if (options['--still'] && (!path.isAbsolute(options['--still']) || !options['--still'].endsWith('.png'))) throw new Error('--still must be an absolute PNG path');
  if (options['--preview-seconds'] !== undefined) {
    const seconds = Number(options['--preview-seconds']);
    if (!Number.isFinite(seconds) || seconds <= 0 || seconds > 60) throw new Error('Preview must be between 0 and 60 seconds');
    options.previewSeconds = seconds;
  }
  return options;
}

export async function compiledBundle(progress = () => {}) {
  const hash = crypto.createHash('sha256');
  for (const name of SOURCE_FILES) hash.update(await readFile(path.resolve(ROOT, name)));
  const directory = path.join(CACHE, 'bundles', hash.digest('hex').slice(0, 24));
  try {await access(path.join(directory, 'complete.json')); return directory;} catch {}
  await mkdir(path.join(CACHE, 'empty-public'), {recursive: true});
  await bundle({entryPoint: path.join(ROOT, 'src/index.jsx'), outDir: directory, rootDir: ROOT,
    publicDir: path.join(CACHE, 'empty-public'), publicPath: './', enableCaching: false,
    gitSource: null, onProgress: (percent) => progress(2 + percent * .1),
    webpackOverride: (config) => {
      const canonical = path.resolve(ROOT, '../packages/full-report/schematics.js');
      return {...config, devtool: false, module: {...config.module, rules: [
        ...config.module.rules.map((rule) => rule.test?.test('file.js') && rule.use
          ? {...rule, exclude: [rule.exclude, canonical].filter(Boolean)} : rule),
        {include: canonical, type: 'javascript/auto'},
      ]}};
    }});
  await writeFile(path.join(directory, 'complete.json'), JSON.stringify({version: VERSION}));
  return directory;
}

export async function render(options) {
  process.chdir(ROOT);
  const input = options['--input'], output = options['--output'], still = options['--still'];
  if ((await stat(input)).size > 5 * 1024 * 1024) throw new Error('Manifest exceeds 5 MiB');
  const manifest = validateManifest(JSON.parse(await readFile(input, 'utf8')));
  for (const chapter of manifest.chapters) if (chapter.section?.diagram) schematics.diagramSvg(chapter.section.diagram);
  for (const destination of [output, still].filter(Boolean)) {
    try {await access(destination); throw new Error('Output already exists; use a new pending output path');}
    catch (error) {if (error.code !== 'ENOENT') throw error;}
    await mkdir(path.dirname(destination), {recursive: true});
  }
  let browser, server, startedOutput = false, completed = false, lastProgress = -1;
  const progress = (value) => {
    const integer = Math.max(0, Math.min(100, Math.floor(value)));
    if (integer > lastProgress) {lastProgress = integer; process.stdout.write(JSON.stringify({progress: integer}) + '\n');}
  };
  const {cancelSignal, cancel} = makeCancelSignal();
  let interrupted = false;
  const interrupt = () => {
    interrupted = true; cancel();
    // Also interrupt still capture, whose CDP screenshot call has no own abort.
    if (browser) void browser.close({silent: true}).catch(() => {});
  };
  process.on('SIGTERM', interrupt);
  process.on('SIGINT', interrupt);
  try {
    progress(0);
    const saved = JSON.parse(await readFile(path.join(CACHE, 'browser.json'), 'utf8'));
    if (saved.remotion !== VERSION || !saved.path?.includes('chrome-headless-shell')
      || !path.resolve(saved.path).startsWith(path.join(ROOT, 'node_modules') + path.sep)) throw new Error('Run npm run prepare-browser inside video first');
    await access(saved.path);
    const directory = await compiledBundle(progress);
    if (interrupted) throw new Error('Render cancelled');
    server = await startAssetServer(manifest.chapters.map((c) => c.audioPath), directory);
    const inputProps = {report: browserProps(manifest, server.audioSources)};
    browser = await openBrowser('chrome', {chromeMode: 'headless-shell', browserExecutable: saved.path,
      logLevel: 'error', chromiumOptions: {disableWebSecurity: false, ignoreCertificateErrors: false},
      onBrowserDownload: () => {throw new Error('Offline render cannot download a browser');}});
    const common = {serveUrl: server.serveUrl, inputProps, puppeteerInstance: browser, logLevel: 'error', timeoutInMilliseconds: 60000,
      onBrowserLog: (log) => {if (['error', 'warning', 'warn'].includes(log.type)) process.stderr.write(log.text.slice(0, 2000) + '\n');}};
    const composition = await selectComposition({...common, id: 'NumeromReport'});
    progress(13);
    const frames = options.previewSeconds ? Math.min(composition.durationInFrames, Math.max(1, Math.floor(options.previewSeconds * manifest.fps))) : composition.durationInFrames;
    if (still) {
      let timer;
      try {
        await Promise.race([
          renderStill({...common, composition, output: still, imageFormat: 'png', frame: Math.min(frames - 1, 72)}),
          new Promise((_, reject) => {timer = setTimeout(() => {
            void browser.close({silent: true}).catch(() => {});
            reject(new Error('Still capture exceeded 60 seconds'));
          }, 60000);}),
        ]);
      } finally {clearTimeout(timer);}
    }
    progress(14);
    if (interrupted) throw new Error('Render cancelled');
    progress(15);
    startedOutput = true;
    await renderMedia({...common, composition, outputLocation: output,
      // JPEG frames and two browser tabs: an hour of report renders in about 50 minutes instead of 1.5 hours.
      frameRange: [0, frames - 1], codec: 'h264', pixelFormat: 'yuv420p', colorSpace: 'bt709', imageFormat: 'jpeg', jpegQuality: 92, audioCodec: 'aac', audioBitrate: '128k',
      // Stream captured JPEGs into FFmpeg. Keeping every frame on disk first
      // can exhaust local storage for a three-hour narrated report.
      concurrency: 2, disallowParallelEncoding: false, disableSharedMemoryCapture: true, x264Preset: 'veryfast', crf: 20,
      overwrite: false, cancelSignal, mediaCacheSizeInBytes: 64 * 1024 * 1024,
      // Remotion's MP4 finalizer writes the moov atom before mdat (Fast Start).
      // Restrict FFmpeg threads too: browser concurrency alone does not do so.
      ffmpegOverride: ({args}) => [...args.slice(0, -1), '-threads', '1', '-t', String(frames / manifest.fps), ...args.slice(-1)],
      onProgress: ({progress: fraction}) => progress(15 + fraction * 84)});
    completed = true;
    progress(100);
  } finally {
    process.removeListener('SIGTERM', interrupt);
    process.removeListener('SIGINT', interrupt);
    if (browser) await browser.close({silent: true}).catch(() => {});
    if (server) await server.close();
    if (startedOutput && !completed) await unlink(output).catch((error) => {if (error.code !== 'ENOENT') process.stderr.write('Could not remove incomplete pending video\n');});
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  // stdout is a machine-readable JSON progress stream, diagnostics use stderr.
  console.log = (...args) => process.stderr.write(args.join(' ') + '\n');
  console.info = console.log;
  Promise.resolve().then(() => render(parseArguments(process.argv.slice(2)))).catch((error) => {
    process.stderr.write(String(error?.message || 'Video render failed') + '\n');
    process.exitCode = 1;
  });
}
