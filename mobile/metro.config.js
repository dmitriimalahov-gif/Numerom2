const path = require('node:path');
const {getDefaultConfig} = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
// All shared calculation, API and knowledge packages must resolve in clean native builds.
config.watchFolders = [...config.watchFolders, path.resolve(__dirname, '../packages')];
module.exports = config;
