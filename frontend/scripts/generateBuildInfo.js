const fs = require('fs');
const path = require('path');

// Генерируем уникальную информацию о сборке
const now = new Date();
const timestamp = now.toISOString().replace('T', ' ').split('.')[0];
const buildNumber = now.getTime(); // Уникальный номер сборки на основе времени

const buildInfo = {
  buildDate: timestamp,
  buildNumber: buildNumber,
  version: `${now.getFullYear()}.${(now.getMonth() + 1).toString().padStart(2, '0')}.${now.getDate().toString().padStart(2, '0')}.${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}`,
  timestamp: buildNumber
};

// Создаем директорию src/utils если её нет
const utilsDir = path.join(__dirname, '..', 'src', 'utils');
if (!fs.existsSync(utilsDir)) {
  fs.mkdirSync(utilsDir, { recursive: true });
}

// Записываем информацию в файл
const outputPath = path.join(utilsDir, 'buildInfo.js');
const content = `// Автоматически генерируется при каждой сборке
// НЕ РЕДАКТИРУЙТЕ ВРУЧНУЮ!

export const BUILD_INFO = ${JSON.stringify(buildInfo, null, 2)};

export const getBuildVersion = () => BUILD_INFO.version;
export const getBuildDate = () => BUILD_INFO.buildDate;
export const getBuildNumber = () => BUILD_INFO.buildNumber;
`;

fs.writeFileSync(outputPath, content, 'utf8');

console.log('🏗️  Генерация информации о сборке...');
console.log(`📅 Дата: ${now.toLocaleDateString('ru-RU')}`);
console.log(`⏰ Время: ${timestamp}`);
console.log(`🔢 Номер сборки: ${buildNumber}`);
console.log(`✅ Информация о сборке обновлена!`);
console.log(`📦 Build: ${buildInfo.version}`);

