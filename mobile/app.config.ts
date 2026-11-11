import { ExpoConfig } from 'expo/config';

const production = process.env.APP_VARIANT === 'production';
const apiUrl = process.env.EXPO_PUBLIC_API_URL;
const webBasePath = process.env.EXPO_PUBLIC_WEB_BASE_PATH || '';
if (webBasePath && !/^\/[a-zA-Z0-9_-]+$/.test(webBasePath)) {
  throw new Error('EXPO_PUBLIC_WEB_BASE_PATH must be a single repository path');
}
if (production && (!apiUrl || !apiUrl.startsWith('https://'))) {
  throw new Error('Production requires an explicit HTTPS EXPO_PUBLIC_API_URL');
}
const config: ExpoConfig = {
  name: 'NumerOM', slug: 'numerom', scheme: 'numerom', version: '0.1.0',
  icon: './assets/brand/icon.png',
  orientation: 'portrait', userInterfaceStyle: 'light',
  ios: { bundleIdentifier: 'com.numerom.app', supportsTablet: true,
    infoPlist: production ? { NSAppTransportSecurity: { NSAllowsArbitraryLoads: false, NSAllowsLocalNetworking: false } } : { NSLocalNetworkUsageDescription: 'Подключение к NumerOM в вашей локальной сети.', NSAppTransportSecurity: { NSAllowsLocalNetworking: true } } },
  android: { package: 'com.numerom.app', adaptiveIcon: {foregroundImage:'./assets/brand/adaptive-icon.png',backgroundColor:'#F6F7F5'} },
  web: { bundler: 'metro', output: 'single', lang: 'ru' },
  experiments: { ...(webBasePath ? {baseUrl: webBasePath} : {}) },
  plugins: ['expo-router', 'expo-sharing', ['expo-secure-store',{faceIDPermission:'Разрешите NumerOM использовать Face ID для защищённого входа.'}], 'expo-font', 'expo-asset', ['expo-location', {
    locationWhenInUsePermission: 'Разрешите NumerOM определить ваш город, пока вы пользуетесь приложением.',
    locationAlwaysPermission: false, locationAlwaysAndWhenInUsePermission: false,
    motionUsagePermission: false, isAndroidMotionActivityEnabled: false,
    isIosBackgroundLocationEnabled: false, isAndroidBackgroundLocationEnabled: false,
    isAndroidForegroundServiceEnabled: false,
  }], ['expo-audio', {
    microphonePermission: false, recordAudioAndroid: false,
    enableBackgroundRecording: false, enableBackgroundPlayback: true,
  }], ['expo-video', {supportsBackgroundPlayback: true, supportsPictureInPicture: true}]],
  extra: { production, ...(apiUrl ? {apiUrl} : {}), ...(process.env.EXPO_PUBLIC_SITE_URL ? {siteUrl: process.env.EXPO_PUBLIC_SITE_URL} : {}) },
};
export default config;
