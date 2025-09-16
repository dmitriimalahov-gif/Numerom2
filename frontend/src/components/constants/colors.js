export const PLANET_COLORS = {
  Surya: '#FFA500',   // Солнце — оранжево-золотой
  Chandra: '#9CA3AF', // Луна — серый для видимости на белом фоне
  Guru: '#FFA500',    // Юпитер — оранжевый
  Rahu: '#8B4513',    // Раху — коричневый
  Buddhi: '#2ECC71',  // Меркурий — зелёный
  Shukra: '#FF69B4',  // Венера — розовый
  Ketu: '#808080',    // Кету — серый
  Shani: '#2C3E50',   // Сатурн — тёмный графит
  Mangal: '#FF0000'   // Марс — красный
};

export const NUMBER_COLORS = {
  1: PLANET_COLORS.Surya,
  2: PLANET_COLORS.Chandra,
  3: PLANET_COLORS.Guru,
  4: PLANET_COLORS.Rahu,
  5: PLANET_COLORS.Buddhi,
  6: PLANET_COLORS.Shukra,
  7: PLANET_COLORS.Ketu,
  8: PLANET_COLORS.Shani,
  9: PLANET_COLORS.Mangal
};

// Специальный серый градиент для Луны/Chandra для видимости на белом фоне
export const getChandraGradient = () => {
  return 'linear-gradient(135deg, #9CA3AF 0%, #6B7280 50%, #4B5563 100%)';
};

// Проверка, является ли планета Луной/Chandra
export const isChandraPlanet = (planetKey) => {
  return planetKey === 'Chandra' || planetKey === 'chandra';
};

export const withAlpha = (hex, alpha = 0.12) => {
  if (!hex || !hex.startsWith('#') || (hex.length !== 7)) return `rgba(0,0,0,${alpha})`;
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// Универсальная функция, красит планету по имени (RU/EN/Sanskrit)
export const getPlanetColor = (name = '') => {
  const n = String(name).trim().toLowerCase();
  if (!n) return '#475569';
  if (/(surya|солнц|sun)/.test(n)) return PLANET_COLORS.Surya;
  if (/(chandra|луна|moon)/.test(n)) return PLANET_COLORS.Chandra;
  if (/(guru|юпитер|jupiter)/.test(n)) return PLANET_COLORS.Guru;
  if (/(rahu|раху)/.test(n)) return PLANET_COLORS.Rahu;
  if (/(budh|buddhi|меркур|mercury)/.test(n)) return PLANET_COLORS.Buddhi;
  if (/(shukra|венер|venus)/.test(n)) return PLANET_COLORS.Shukra;
  if (/(ketu|кету)/.test(n)) return PLANET_COLORS.Ketu;
  if (/(shani|сатурн|saturn)/.test(n)) return PLANET_COLORS.Shani;
  if (/(mangal|марс|mars)/.test(n)) return PLANET_COLORS.Mangal;
  return '#475569';
};