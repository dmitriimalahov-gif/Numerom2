// «Слово автора»: one fixed MP4 from the voiced asset in mobile/assets/author.
// Run from the service runtime copy: Chrome on this macOS hangs when launched from Desktop.
//   node video/render-author.mjs --word <author-word.json> --output <author-word.mp4>
//   --stills 2,24.5,30 renders those seconds as PNG next to --output instead of the movie (layout checks).
//   --vertical renders the 1080×1920 phone version.
import {bundle} from '@remotion/bundler';
import {openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {copyFile, mkdtemp, readFile, rm} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {startAssetServer} from './assets.mjs';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).filter((value) => value !== '--vertical').reduce((pairs, value, i, all) => i % 2 ? pairs : [...pairs, [value, all[i + 1]]], []));
const wordPath = args['--word'], output = args['--output'];
if (!wordPath || !output || !path.isAbsolute(wordPath) || !path.isAbsolute(output)) throw new Error('Expected absolute --word and --output');

const word = JSON.parse(await readFile(wordPath, 'utf8'));
const pub = await mkdtemp(path.join(os.tmpdir(), 'numerom-author-'));
let browser, server;
try {
  await copyFile(path.join(path.dirname(wordPath), 'author-word.m4a'), path.join(pub, 'author-word.m4a'));
  await copyFile(path.resolve(ROOT, '../packages/brand/numerom-logo.svg'), path.join(pub, 'numerom-logo.svg'));
  for (const scheme of ['KVADRATW.png', '123W.png', '159W.png'])
    await copyFile(path.resolve(path.dirname(wordPath), '../illustrations', scheme), path.join(pub, scheme));
  const directory = await bundle({entryPoint: path.join(ROOT, 'src/author/index.jsx'), publicDir: pub, enableCaching: false});
  // Use the same isolated loopback server as paid reports. Another local app
  // can already own localhost:3000 (including on the other IP address family).
  server = await startAssetServer([], directory);
  const serveUrl = server.serveUrl;
  const saved = JSON.parse(await readFile(path.join(ROOT, '.cache/browser.json'), 'utf8'));
  browser = await openBrowser('chrome', {chromeMode: 'headless-shell', browserExecutable: saved.path, logLevel: 'error'});
  const inputProps = {word, audio: 'author-word.m4a'};
  const id = process.argv.includes('--vertical') ? 'AuthorWordVertical' : 'AuthorWord';
  const composition = await selectComposition({serveUrl, id, inputProps, puppeteerInstance: browser});
  if (args['--stills']) {
    for (const second of args['--stills'].split(',').map(Number)) {
      const file = output.replace(/\.mp4$/, '') + `-${second}s.png`;
      await renderStill({composition, serveUrl, inputProps, puppeteerInstance: browser, output: file, frame: Math.round(second * composition.fps)});
      process.stdout.write(`${file}\n`);
    }
  } else await renderMedia({composition, serveUrl, inputProps, puppeteerInstance: browser, outputLocation: output, codec: 'h264',
    pixelFormat: 'yuv420p', audioCodec: 'aac', audioBitrate: '128k', crf: 22, x264Preset: 'medium', concurrency: 2,
    onProgress: ({progress}) => process.stdout.write(`\r${Math.round(progress * 100)}%`)});
  process.stdout.write(`\nГотово: ${output}\n`);
} finally {
  if (browser) await browser.close({silent: true}).catch(() => {});
  if (server) await server.close();
  await rm(pub, {recursive: true, force: true});
}
