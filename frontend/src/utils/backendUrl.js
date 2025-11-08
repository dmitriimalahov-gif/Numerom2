const selectEnvValue = () => {
  if (typeof process !== 'undefined' && process.env?.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }

  try {
    // Vite-style envs
    if (typeof import.meta !== 'undefined' && import.meta?.env) {
      const metaEnv = import.meta.env;
      return (
        metaEnv.REACT_APP_BACKEND_URL ||
        metaEnv.VITE_BACKEND_URL ||
        metaEnv.VITE_API_URL ||
        metaEnv.BACKEND_URL ||
        null
      );
    }
  } catch (_) {
    // ignore import.meta access issues
  }

  return null;
};

const normalizeUrl = (rawUrl) => {
  if (!rawUrl || typeof rawUrl !== 'string') {
    return null;
  }

  // Удаляем пробелы и завершающие слэши
  let cleaned = rawUrl.trim().replace(/\/+$/, '');

  // Если ссылка заканчивается на /api — отрезаем, чтобы путь не дублировался
  if (cleaned.toLowerCase().endsWith('/api')) {
    cleaned = cleaned.slice(0, -4);
  }

  return cleaned;
};

export const getBackendUrl = () => {
  const fromEnv = selectEnvValue();
  const normalized = normalizeUrl(fromEnv);
  return normalized || 'http://localhost:8000';
};

export const getApiBaseUrl = () => {
  const base = getBackendUrl().replace(/\/+$/, '');
  return `${base}/api`;
};

