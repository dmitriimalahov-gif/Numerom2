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
  let normalized = normalizeUrl(fromEnv);

  if (typeof window !== 'undefined') {
    const { protocol } = window.location;
    const port = window.location.port || (protocol === 'https:' ? '443' : '80');
    const devPorts = new Set(['3000', '5173', '4173', '4174']);
    const isLocalDev = devPorts.has(port);
    const isDockerFrontend = port === '5128' || port === '80';
    const isLearningV2Frontend = port === '5129';

    // Всегда используем localhost для backend, так как он доступен через Docker networking
    // Независимо от того, как пользователь заходит к frontend (localhost или IP)
    let targetHost = 'localhost';
    let targetPort = '8000';

    if (isLearningV2Frontend) {
      targetPort = '8002';  // Backend для системы обучения V2
    }

    // Специальная логика для компонентов V2 в основном проекте
    // Они должны подключаться к основному backend через внешний порт
    if (window.location.pathname.startsWith('/learning-v2') ||
        window.location.pathname.startsWith('/admin-v2') ||
        window.location.pathname === '/learning-v2-dashboard') {
      targetPort = '8000';  // Основной backend для V2 компонентов
    }

    // Используем тот же hostname, что и у frontend, для backend
    // Это работает как для localhost, так и для внешних IP адресов
    targetHost = window.location.hostname;

    if (normalized) {
      try {
        const url = new URL(normalized);
        if (isLocalDev || isDockerFrontend) {
          url.hostname = targetHost;
          url.port = targetPort;
        }
        return url.toString();
      } catch (error) {
        // fall through to manual string construction
        if (isLocalDev || isDockerFrontend) {
          normalized = normalized.replace(/:\d+$/, `:${targetPort}`);
        }
        return normalized;
      }
    }

    return `${protocol}//${targetHost}:${targetPort}`;
  }

  return normalized || 'http://localhost:8000';
};

export const getApiBaseUrl = () => {
  const base = getBackendUrl().replace(/\/+$/, '');
  return `${base}/api`;
};

