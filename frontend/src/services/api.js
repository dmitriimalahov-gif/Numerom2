import { createApiClient } from '@numerom/api-client';
import { getBackendUrl } from '../utils/backendUrl';

// Existing feature modules may still use axios during the incremental migration.
export const api = createApiClient({
  baseUrl: getBackendUrl(),
  getToken: () => localStorage.getItem('token'),
});
