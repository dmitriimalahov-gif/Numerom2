import { resolveBackendUrl } from '@numerom/api-client';

export const getBackendUrl = () => resolveBackendUrl(
  process.env.REACT_APP_BACKEND_URL,
  typeof window === 'undefined' ? undefined : window.location,
);
export const getApiBaseUrl = () => `${getBackendUrl()}/api`;
