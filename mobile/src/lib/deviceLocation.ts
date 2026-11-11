import * as Location from 'expo-location';
import {createNativeLocationAdapter} from './deviceLocationCore';

export {DeviceLocationError} from './deviceLocationCore';
export type {Coordinates, LocationErrorCode, PositionCallback, LocationErrorCallback} from './deviceLocationCore';

const adapter = createNativeLocationAdapter(Location);
export const locate = adapter.locate;
export const watchLocation = adapter.watchLocation;
