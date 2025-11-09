import { useMemo } from 'react';

/**
 * Универсальный хук для работы с темой
 * Возвращает конфигурацию цветов и стилей для текущей темы
 */
export const useTheme = (theme = 'light') => {
  const themeConfig = useMemo(() => {
    const isDark = theme === 'dark';
    
    return {
      // Основные цвета
      bg: isDark ? 'bg-slate-900' : 'bg-gray-50',
      text: isDark ? 'text-white' : 'text-gray-900',
      mutedText: isDark ? 'text-slate-300' : 'text-gray-600',
      subtleText: isDark ? 'text-slate-400' : 'text-slate-500',
      
      // Карточки и контейнеры
      card: isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-white border-gray-200',
      cardHover: isDark ? 'hover:bg-slate-800/70' : 'hover:bg-gray-50',
      surface: isDark ? 'bg-slate-800' : 'bg-white',
      
      // Границы и разделители
      border: isDark ? 'border-slate-700' : 'border-gray-200',
      divider: isDark ? 'border-white/10' : 'border-slate-200',
      
      // Акцентные цвета
      accent: isDark ? 'bg-indigo-600' : 'bg-indigo-500',
      accentText: isDark ? 'text-indigo-400' : 'text-indigo-600',
      accentHover: isDark ? 'hover:bg-indigo-700' : 'hover:bg-indigo-600',
      
      // Формы ввода
      input: isDark ? 'bg-slate-700 border-slate-600 text-white placeholder:text-slate-400' : 'bg-white border-gray-300 text-gray-900 placeholder:text-gray-400',
      inputFocus: isDark ? 'focus:border-indigo-500 focus:ring-indigo-500' : 'focus:border-indigo-500 focus:ring-indigo-500',
      
      // Кнопки
      button: isDark ? 'bg-slate-700 text-white hover:bg-slate-600' : 'bg-gray-100 text-gray-900 hover:bg-gray-200',
      buttonPrimary: isDark ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-indigo-500 text-white hover:bg-indigo-600',
      
      // Статусы
      success: isDark ? 'bg-emerald-400/15 text-emerald-100 border-emerald-500/40' : 'bg-emerald-100 text-emerald-700 border-emerald-200',
      warning: isDark ? 'bg-amber-400/20 text-amber-100 border-amber-500/40' : 'bg-amber-100 text-amber-700 border-amber-200',
      error: isDark ? 'bg-rose-400/15 text-rose-100 border-rose-500/40' : 'bg-rose-100 text-rose-700 border-rose-200',
      info: isDark ? 'bg-sky-400/15 text-sky-100 border-sky-500/40' : 'bg-sky-100 text-sky-700 border-sky-200',
      
      // Специальные эффекты
      glass: isDark ? 'bg-white/5 backdrop-blur-xl border border-white/10' : 'bg-white/70 backdrop-blur-xl border border-white/80',
      overlay: isDark ? 'bg-black/50' : 'bg-black/30',
      
      // Тени
      shadow: isDark ? 'shadow-xl shadow-black/50' : 'shadow-lg shadow-gray-200',
      shadowHover: isDark ? 'hover:shadow-2xl hover:shadow-black/60' : 'hover:shadow-xl hover:shadow-gray-300',
      
      // Переключатели и чекбоксы
      toggle: isDark ? 'bg-slate-700' : 'bg-gray-200',
      toggleActive: isDark ? 'bg-indigo-600' : 'bg-indigo-500',
      
      // Бейджи и чипы
      badge: isDark ? 'bg-slate-700 text-slate-200' : 'bg-gray-100 text-gray-700',
      badgeSuccess: isDark ? 'bg-emerald-900/30 text-emerald-400' : 'bg-emerald-100 text-emerald-800',
      badgeWarning: isDark ? 'bg-amber-900/30 text-amber-400' : 'bg-amber-100 text-amber-800',
      
      // Градиенты для фона
      pageGradient: isDark 
        ? 'radial-gradient(1400px at 50% -5%, rgba(56,189,248,0.18), transparent 65%), radial-gradient(900px at 80% 0%, rgba(94,234,212,0.12), transparent 70%)'
        : 'radial-gradient(1200px at 50% -5%, rgba(129,140,248,0.18), transparent 70%), radial-gradient(900px at 85% 5%, rgba(45,212,191,0.14), transparent 75%)',
      
      // Утилиты
      isDark,
      isLight: !isDark,
      theme
    };
  }, [theme]);
  
  return themeConfig;
};

/**
 * Получить цвет текста с правильным контрастом для заданного фона
 */
export const getContrastText = (backgroundColor, theme = 'light') => {
  // Если фон светлый - тёмный текст, если тёмный - светлый текст
  const isDark = theme === 'dark';
  
  // Для светлых фонов в любой теме используем тёмный текст
  if (backgroundColor && (
    backgroundColor.includes('white') ||
    backgroundColor.includes('100') ||
    backgroundColor.includes('200') ||
    backgroundColor.includes('50')
  )) {
    return 'text-gray-900';
  }
  
  // Для тёмных фонов используем светлый текст
  if (backgroundColor && (
    backgroundColor.includes('800') ||
    backgroundColor.includes('900') ||
    backgroundColor.includes('black')
  )) {
    return 'text-white';
  }
  
  // По умолчанию используем цвет текста темы
  return isDark ? 'text-white' : 'text-gray-900';
};

