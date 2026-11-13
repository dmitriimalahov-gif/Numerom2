// Postprocess an Expo web export. This directory, not the project tree, is public.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const output = path.resolve(process.argv[2] || 'mobile/dist-pages');
const base = process.env.EXPO_PUBLIC_WEB_BASE_PATH ?? '/numerom-app';
if (base && !/^\/[a-zA-Z0-9_-]+$/.test(base)) throw new Error('Invalid Pages path');
const indexPath = path.join(output, 'index.html');
let html = await fs.readFile(indexPath, 'utf8');
if (!html.includes('name="numerom-telegram"')) html = html.replace('</head>', '<meta name="numerom-telegram" content="1"/></head>');
html = html.replace('<html lang="en">', '<html lang="ru">');
if (!html.includes(`${base}/_expo/`)) throw new Error('Export has the wrong base path');
const branding = await fs.readFile(new URL('../packages/brand/numerom-logo.svg', import.meta.url), 'utf8');
await fs.writeFile(path.join(output, 'icon.svg'), branding);
const manifest = {
 name: 'NumerOM', short_name: 'NumerOM', lang: 'ru',
 description: 'Персональные числа, обучение и схемы NumerOM.',
 start_url: `${base}/`, scope: `${base}/`, id: `${base}/`,
 display: 'standalone', background_color: '#F6F7F5', theme_color: '#17354E',
 icons: [{src: `${base}/icon.svg`, sizes: 'any', type: 'image/svg+xml', purpose: 'any'}],
};
await fs.writeFile(path.join(output, 'manifest.webmanifest'), JSON.stringify(manifest, null, 2));
if (!html.includes('rel="manifest"')) html = html.replace('</head>', `<meta name="referrer" content="no-referrer"/>
<meta name="theme-color" content="#17354E"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-title" content="NumerOM"/>
<meta name="description" content="Персональные числа, обучение и схемы NumerOM."/>
<link rel="icon" type="image/svg+xml" href="${base}/icon.svg"/>
<link rel="manifest" href="${base}/manifest.webmanifest"/>
</head>`);
await fs.writeFile(indexPath, html);
// Known routes return HTTP 200 after reload; dynamic lessons retain their path via 404 shell.
for (const route of ['home','numbers','full-report','relationships','number-tools','learning','library','profile','guide','audio-guide','top-up','payment-result','consultations','credits','forgot-password','reset-password','daily-email','assessment','vedic-time','admin','business','telegram']) {
 await fs.mkdir(path.join(output, route), {recursive:true});
 await fs.writeFile(path.join(output, route, 'index.html'), html);
}
await fs.writeFile(path.join(output, '404.html'), html);
await fs.writeFile(path.join(output, '.nojekyll'), '');
await fs.writeFile(path.join(output, 'README.md'), `# NumerOM Mobile\n\nПубличная браузерная версия: https://dmitriimalahov-gif.github.io${base}/\n\nЭтот репозиторий содержит только собранный интерфейс для iPhone, Android и браузера. Подписанные IPA/APK будут выпущены отдельно. Сервер пилота работает на компьютере владельца. Службы автоматически перезапускаются; приложение получает новый HTTPS-адрес из подписанного runtime-config.json без смены ссылки. Во время отключения компьютера серверные функции недоступны.\n\nБаза пользователей, серверный код, ключи и пароли в этот репозиторий не включены.\n`);
const forbidden = /(?:\.env(?:\.|$)|\.map$|\.pem$|\.key$|\.sqlite(?:3)?$|credentials|token\.json|^server\.py$)/i;
let files = 0, bytes = 0;
async function audit(folder) {
 for (const entry of await fs.readdir(folder, {withFileTypes:true})) {
  const file = path.join(folder, entry.name);
  if (entry.name === 'node_modules' && path.relative(output, file) !== 'assets/node_modules') throw new Error('Unexpected dependencies');
  if (entry.isSymbolicLink() || forbidden.test(entry.name)) throw new Error(`Unexpected publication file: ${path.relative(output,file)}`);
  if (entry.isDirectory()) await audit(file);
  else {
   const content = await fs.readFile(file);
   if (/\.(js|html|json|md|webmanifest|svg|txt)$/.test(entry.name)) {
    const text = content.toString();
    if (/(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|(?:sk|rk|rkcs)_(?:test|live)_[A-Za-z0-9]{16,}|whsec_[A-Za-z0-9]{16,}|mongodb(?:\+srv)?:\/\/[^\s"']+:[^\s"']+@)/.test(text)) throw new Error(`Credential pattern in ${path.relative(output,file)}`);
   }
   if (/\.(js|html|json|txt)$/.test(entry.name) && /["'][0-9]{5,20}:[A-Za-z0-9_-]{25,}["']/.test(content.toString())) throw new Error(`Telegram credential pattern in ${path.relative(output,file)}`);
   files++; bytes += content.length;
  }
 }
}
await audit(output);
console.log(JSON.stringify({output, files, bytes, indexSha256:crypto.createHash('sha256').update(html).digest('hex')}));
