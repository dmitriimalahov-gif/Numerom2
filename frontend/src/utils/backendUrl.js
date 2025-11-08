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
    const { protocol, hostname } = window.location;
    const port = window.location.port || (protocol === 'https:' ? '443' : '80');
    const devPorts = new Set(['3000', '5173', '4173', '4174']);
    const isLocalDev = devPorts.has(port);
    const isDockerFrontend = port === '5128' || port === '80';
    const targetHost = hostname;
    const targetPort = isLocalDev || isDockerFrontend ? '8001' : port;

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

  return normalized || 'http://192.168.110.178:8001';
};

export const getApiBaseUrl = () => {
  const base = getBackendUrl().replace(/\/+$/, '');
  return `${base}/api`;
};

