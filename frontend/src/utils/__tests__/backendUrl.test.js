import { getBackendUrl, getApiBaseUrl } from '../backendUrl';

test('an explicit deployed backend is respected by the web adapter', () => {
  const previous = process.env.REACT_APP_BACKEND_URL;
  process.env.REACT_APP_BACKEND_URL = 'https://numerom.example/api/';
  try {
    expect(getBackendUrl()).toBe('https://numerom.example');
    expect(getApiBaseUrl()).toBe('https://numerom.example/api');
  } finally {
    if (previous === undefined) delete process.env.REACT_APP_BACKEND_URL;
    else process.env.REACT_APP_BACKEND_URL = previous;
  }
});
