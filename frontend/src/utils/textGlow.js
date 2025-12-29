/**
 * Утилиты для создания эффектов свечения текста в темной теме
 */

/**
 * Проверить, является ли цвет достаточно тёмным
 * @param {string} hexColor - Цвет в формате #RRGGBB
 * @returns {boolean}
 */
const isDarkColor = (hexColor) => {
  if (!hexColor || typeof hexColor !== 'string') return false;
  const hex = hexColor.replace('#', '');
  if (hex.length !== 6) return false;
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  // Рассчитываем яркость (luminance)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5; // Если яркость меньше 50% - считаем тёмным
};

/**
 * Получить яркий цвет для тёмного цвета планеты
 * @param {string} color - Исходный цвет
 * @returns {string} - Яркий цвет для тёмной темы
 */
export const getBrightColorForDark = (color) => {
  if (!color) return '#ffffff';
  
  // Словарь замен для тёмных цветов планет
  const brightColorMap = {
    '#3b82f6': '#60a5fa', // Синий -> Ярко-голубой (Shani)
    '#1e40af': '#60a5fa', // Тёмно-синий -> Ярко-голубой
    '#1e3a8a': '#60a5fa', // Тёмно-синий -> Ярко-голубой
    '#2563eb': '#60a5fa', // Синий -> Ярко-голубой
    '#6366f1': '#a5b4fc', // Индиго -> Светло-индиго
    '#4f46e5': '#a5b4fc', // Индиго -> Светло-индиго
    '#7c3aed': '#c4b5fd', // Фиолетовый -> Светло-фиолетовый
    '#6d28d9': '#c4b5fd', // Фиолетовый -> Светло-фиолетовый
    '#4b0082': '#a78bfa', // Индиго -> Светло-фиолетовый (Rahu)
    '#8b4513': '#d97706', // Коричневый -> Янтарный (Ketu)
    '#374151': '#9ca3af', // Серый -> Светло-серый
    '#1f2937': '#9ca3af', // Тёмно-серый -> Светло-серый
  };
  
  const lowerColor = color.toLowerCase();
  if (brightColorMap[lowerColor]) {
    return brightColorMap[lowerColor];
  }
  
  // Если цвет тёмный, осветляем его
  if (isDarkColor(color)) {
    const hex = color.replace('#', '');
    const r = Math.min(255, parseInt(hex.substring(0, 2), 16) + 80);
    const g = Math.min(255, parseInt(hex.substring(2, 4), 16) + 80);
    const b = Math.min(255, parseInt(hex.substring(4, 6), 16) + 80);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }
  
  return color;
};

/**
 * Получить стили для заголовка с мягким свечением
 * @param {boolean} isDark - Темная тема?
 * @param {string} color - Цвет свечения (по умолчанию белый)
 * @returns {object} - Объект стилей для применения
 */
export const getTitleGlow = (isDark, color = '#ffffff') => {
  if (!isDark) return {};
  
  // Для тёмных цветов используем белое свечение
  const glowColor = isDarkColor(color) ? '#ffffff' : color;
  
  return {
    textShadow: `
      0 0 10px ${glowColor}60,
      0 0 20px ${glowColor}40,
      0 0 30px ${glowColor}20
    `,
  };
};

/**
 * Получить стили для обычного текста с тонким свечением
 * @param {boolean} isDark - Темная тема?
 * @param {string} color - Цвет свечения
 * @returns {object}
 */
export const getTextGlow = (isDark, color = '#ffffff') => {
  if (!isDark) return {};
  
  const glowColor = isDarkColor(color) ? '#ffffff' : color;
  
  return {
    textShadow: `
      0 0 8px ${glowColor}40,
      0 0 15px ${glowColor}25
    `,
  };
};

/**
 * Получить стили для акцентного текста с ярким свечением
 * @param {boolean} isDark - Темная тема?
 * @param {string} color - Цвет свечения
 * @returns {object}
 */
export const getAccentGlow = (isDark, color = '#a78bfa') => {
  if (!isDark) return {};
  
  const glowColor = isDarkColor(color) ? '#ffffff' : color;
  
  return {
    textShadow: `
      0 0 15px ${glowColor}70,
      0 0 30px ${glowColor}50,
      0 0 45px ${glowColor}30
    `,
  };
};

/**
 * Получить стили для числа с сильным свечением
 * @param {boolean} isDark - Темная тема?
 * @param {string} color - Цвет свечения
 * @returns {object}
 */
export const getNumberGlow = (isDark, color = '#ffffff') => {
  if (!isDark) return {};
  
  const glowColor = isDarkColor(color) ? '#ffffff' : color;
  
  return {
    textShadow: `
      0 0 20px ${glowColor}60,
      0 0 40px ${glowColor}40,
      0 0 60px ${glowColor}25,
      0 2px 4px rgba(0,0,0,0.3)
    `,
  };
};

/**
 * Получить стили для планетарного заголовка с подсветкой
 * Использует яркий цвет для тёмных планет и белую обводку
 * @param {boolean} isDark - Темная тема?
 * @param {string} planetColor - Цвет планеты
 * @returns {object}
 */
export const getPlanetTitleGlow = (isDark, planetColor) => {
  if (!isDark) return { color: planetColor };
  
  const brightColor = getBrightColorForDark(planetColor);
  
  return {
    color: brightColor,
    textShadow: `
      0 0 12px ${brightColor}80,
      0 0 24px ${brightColor}50,
      0 0 36px ${brightColor}30,
      0 0 4px rgba(255,255,255,0.8)
    `,
  };
};

/**
 * CSS классы для подсветки текста (можно использовать напрямую)
 */
export const textGlowClasses = {
  title: 'dark:[text-shadow:0_0_10px_rgba(255,255,255,0.25),0_0_20px_rgba(255,255,255,0.13)]',
  text: 'dark:[text-shadow:0_0_8px_rgba(255,255,255,0.2),0_0_15px_rgba(255,255,255,0.1)]',
  accent: 'dark:[text-shadow:0_0_15px_rgba(167,139,250,0.4),0_0_30px_rgba(167,139,250,0.25)]',
  number: 'dark:[text-shadow:0_0_20px_rgba(255,255,255,0.3),0_0_40px_rgba(255,255,255,0.2)]',
};

