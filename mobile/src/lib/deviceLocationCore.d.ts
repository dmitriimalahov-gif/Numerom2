export type Coordinates = {latitude: number; longitude: number; accuracy: number | null; timestamp: number};
export type LocationErrorCode = 'denied' | 'unsupported' | 'timeout' | 'unavailable';
export class DeviceLocationError extends Error {
  readonly code: LocationErrorCode;
  constructor(code: LocationErrorCode, message?: string);
}
export type PositionCallback = (position: Coordinates) => void;
export type LocationErrorCallback = (error: DeviceLocationError) => void;
export type DeviceLocationAdapter = {
  locate(signal?: AbortSignal): Promise<Coordinates>;
  watchLocation(onPosition: PositionCallback, onError: LocationErrorCallback, signal?: AbortSignal): Promise<() => void>;
};
export function coordinates(position: unknown): Coordinates;
export function createWebLocationAdapter(environment: () => {
  secureContext: boolean;
  geolocation?: Geolocation;
}, options?: {timeoutMs?: number}): DeviceLocationAdapter;
export function createNativeLocationAdapter(location: Pick<typeof import('expo-location'),
  'Accuracy' | 'hasServicesEnabledAsync' | 'getForegroundPermissionsAsync' | 'requestForegroundPermissionsAsync' | 'watchPositionAsync'
>, options?: {timeoutMs?: number}): DeviceLocationAdapter;
