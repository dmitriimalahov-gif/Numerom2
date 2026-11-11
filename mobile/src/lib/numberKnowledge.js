const catalog = require('../../../packages/number-knowledge/ru.json');
const manifest = require('../../../packages/number-knowledge/audio-manifest.json');

const numberKnowledge = digit => {
  if (!Number.isInteger(digit) || digit < 1 || digit > 9) return null;
  const entry = catalog.items.find(item => item.digit === digit);
  const audio = manifest.items.find(item => item.digit === digit);
  return entry && audio ? {...entry, audio} : null;
};
module.exports = {numberKnowledge, knowledgeNumbers: catalog.items.map(item => item.digit), knowledgeNote: catalog.note};
