// Saved report → PDF file: the same self-contained HTML the app prints, rendered by the Remotion Chrome.
// Scripts are off and every request other than the report file itself is refused.
// Run from the service runtime copy: Chrome on this macOS hangs when launched from Desktop.
//   node video/render-report-pdf.mjs --html <report.html> --output <report.pdf>
import {openBrowser} from '@remotion/renderer';
import {readFile, rename, rm, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, value, i, all) => i % 2 ? pairs : [...pairs, [value, all[i + 1]]], []));
const input = args['--html'], output = args['--output'];
if (!input || !output || !path.isAbsolute(input) || !path.isAbsolute(output)) throw new Error('Expected absolute --html and --output');

const saved = JSON.parse(await readFile(path.join(ROOT, '.cache/browser.json'), 'utf8'));
const browser = await openBrowser('chrome', {chromeMode: 'headless-shell', browserExecutable: saved.path, logLevel: 'error'});
try {
  const page = await browser.newPage({context: () => null, logLevel: 'error', indent: false, pageIndex: 0, onBrowserLog: null, onLog: () => {}});
  const client = page._client();
  const report = pathToFileURL(input).href;
  await client.send('Emulation.setScriptExecutionDisabled', {value: true});
  await client.send('Fetch.enable', {patterns: [{urlPattern: '*'}]});
  client.on('Fetch.requestPaused', ({requestId, request}) => {
    const allowed = request.url === report;
    client.send(allowed ? 'Fetch.continueRequest' : 'Fetch.failRequest', allowed ? {requestId} : {requestId, errorReason: 'BlockedByClient'}).catch(() => {});
  });
  await page.goto({url: report, timeout: 60000});
  const {value} = await client.send('Page.printToPDF', {printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false});
  await writeFile(output + '.part', Buffer.from(value.data, 'base64'));
  await rename(output + '.part', output);
  process.stdout.write(`Готово: ${output}\n`);
} finally {
  await browser.close({silent: true}).catch(() => {});
  await rm(output + '.part', {force: true});
}
