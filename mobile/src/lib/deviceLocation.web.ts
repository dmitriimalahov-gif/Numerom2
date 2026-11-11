import {createWebLocationAdapter} from './deviceLocationCore';

export {DeviceLocationError} from './deviceLocationCore';
export type {Coordinates, LocationErrorCode, PositionCallback, LocationErrorCallback} from './deviceLocationCore';

const adapter = createWebLocationAdapter(() => ({
  secureContext: typeof window !== 'undefined' && window.isSecureContext === true,
  geolocation: typeof navigator !== 'undefined' ? navigator.geolocation : undefined,
}));
export const locate = adapter.locate;
export const watchLocation = adapter.watchLocation;
