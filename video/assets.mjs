import http from 'node:http';
import crypto from 'node:crypto';
import fs from 'node:fs';
import {open, readdir, realpath} from 'node:fs/promises';
import path from 'node:path';
import {Readable} from 'node:stream';

const CONTENT_TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.wasm': 'application/wasm', '.woff2': 'font/woff2', '.png': 'image/png', '.m4a': 'audio/mp4'};

export function byteRange(header, size) {
  if (header === undefined) return {start: 0, end: size - 1, partial: false};
  const match = /^bytes=([0-9]*)-([0-9]*)$/.exec(header);
  if (!match || (!match[1] && !match[2])) return null;
  const start = match[1] ? Number(match[1]) : Math.max(0, size - Number(match[2]));
  const end = match[1] && match[2] ? Math.min(Number(match[2]), size - 1) : size - 1;
  if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start > end || start >= size || end < 0) return null;
  return {start, end, partial: true};
}

/** Random capability URLs expose only pre-opened audio and this compiled app. */
export async function startAssetServer(audioPaths, bundleDirectory) {
  const nonce = crypto.randomBytes(24).toString('hex');
  const prefix = '/' + nonce;
  const files = new Map();
  const handles = [];
  let server;
  let host;
  async function add(route, filename, maximum) {
    const canonical = await realpath(filename);
    const handle = await open(canonical, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    handles.push(handle);
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size < 1 || stat.size > maximum) throw new Error('Asset must be a bounded regular file');
    files.set(route, {handle, size: stat.size, type: CONTENT_TYPES[path.extname(filename).toLowerCase()] || 'application/octet-stream'});
  }
  async function close() {
    if (server) {
      server.closeAllConnections();
      await new Promise((resolve) => server.close(resolve));
    }
    await Promise.allSettled(handles.map((handle) => handle.close()));
  }
  try {
    for (let index = 0; index < audioPaths.length; index++) await add(`${prefix}/audio/${index}.m4a`, audioPaths[index], 512 * 1024 * 1024);
    const bundleRoot = await realpath(bundleDirectory);
    async function walk(directory, relative = '') {
      for (const entry of await readdir(directory, {withFileTypes: true})) {
        if (entry.isSymbolicLink()) throw new Error('Bundle symlinks are not permitted');
        const next = path.join(directory, entry.name);
        const name = relative + entry.name;
        if (entry.isDirectory()) await walk(next, name + '/');
        else if (entry.isFile() && !name.endsWith('.map')) await add(`${prefix}/bundle/${name}`, next, 64 * 1024 * 1024);
      }
    }
    await walk(bundleRoot);
    const indexFile = files.get(`${prefix}/bundle/index.html`);
    if (!indexFile) throw new Error('Compiled bundle has no index');
    files.set(`${prefix}/bundle/`, indexFile);
    server = http.createServer((request, response) => {
      const deny = (status) => {response.writeHead(status, {'Cache-Control': 'no-store'}); response.end();};
      if (request.headers.host !== host) return deny(403);
      if (request.headers.origin && request.headers.origin !== `http://${host}`) return deny(403);
      if (request.method !== 'GET' && request.method !== 'HEAD') return deny(405);
      let route;
      try {route = new URL(request.url, `http://${host}`).pathname;} catch {return deny(400);}
      const file = files.get(route);
      if (!file) return deny(404);
      const range = byteRange(request.headers.range, file.size);
      if (!range) {
        response.writeHead(416, {'Content-Range': `bytes */${file.size}`, 'Cache-Control': 'no-store'});
        return response.end();
      }
      response.writeHead(range.partial ? 206 : 200, {
        'Content-Type': file.type,
        'Content-Length': range.end - range.start + 1,
        'Accept-Ranges': 'bytes',
        ...(range.partial ? {'Content-Range': `bytes ${range.start}-${range.end}/${file.size}`} : {}),
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'Cross-Origin-Resource-Policy': 'same-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'",
      });
      if (request.method === 'HEAD') return response.end();
      // A response owns its iterator, never the shared allowlisted descriptor.
      // FileHandle.createReadStream().destroy() closes that descriptor even
      // after a completed response, breaking later range requests in Chromium.
      const stream = Readable.from((async function* () {
        for (let position = range.start; position <= range.end;) {
          const buffer = Buffer.allocUnsafe(Math.min(128 * 1024, range.end - position + 1));
          const {bytesRead} = await file.handle.read(buffer, 0, buffer.length, position);
          if (bytesRead === 0) throw new Error('Allowlisted asset changed while rendering');
          position += bytesRead;
          yield buffer.subarray(0, bytesRead);
        }
      })());
      stream.on('error', () => response.destroy());
      response.on('close', () => stream.destroy());
      stream.pipe(response);
    });
    server.requestTimeout = 15000;
    server.headersTimeout = 10000;
    await new Promise((resolve, reject) => {server.once('error', reject); server.listen(0, '127.0.0.1', resolve);});
    host = '127.0.0.1:' + server.address().port;
    return {origin: `http://${host}`, serveUrl: `http://${host}${prefix}/bundle/`,
      audioSources: audioPaths.map((_, i) => `http://${host}${prefix}/audio/${i}.m4a`), close};
  } catch (error) {
    await close();
    throw error;
  }
}
