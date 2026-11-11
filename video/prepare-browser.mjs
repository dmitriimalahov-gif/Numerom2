/** Installation only. Rendering never downloads a browser or accesses a CDN. */
import {ensureBrowser} from '@remotion/renderer';
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
process.chdir(root);
await mkdir(path.join(root, '.cache'), {recursive: true});
let lastPercent = -1;
const browser = await ensureBrowser({chromeMode: 'headless-shell', logLevel: 'error',
  onBrowserDownload: () => ({version: null, onProgress: ({percent}) => {
    const integer = Math.floor(percent * 100);
    if (integer !== lastPercent) {lastPercent = integer; process.stderr.write(`Browser ${integer}%\n`);}
  }})});
if (!browser.path || !browser.path.includes('chrome-headless-shell')) throw new Error('Expected standalone Chrome Headless Shell');
await writeFile(path.join(root, '.cache/browser.json'), JSON.stringify({path: browser.path, remotion: '4.0.538'}) + '\n', {mode: 0o600});
process.stdout.write(JSON.stringify({ready: true, browser: 'chrome-headless-shell'}) + '\n');
