// Load configuration from environment or config file
const path = require('path');
const DirectoryReadGuardPlugin = require('./scripts/DirectoryReadGuardPlugin');

// Environment variable overrides
const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true',
};

module.exports = {
  jest: {
    configure: {
      // CRA's Jest 27 does not resolve React Router 7's package exports.
      moduleNameMapper: {
        '^@numerom/api-client$': path.resolve(__dirname, '../packages/api-client/index.js'),
        '^@numerom/full-report$': path.resolve(__dirname, '../packages/full-report/index.js'),
        '^react-router-dom$': path.join(path.dirname(require.resolve('react-router-dom/package.json')), 'dist/index.js'),
        '^react-router$': path.join(path.dirname(require.resolve('react-router/package.json')), 'dist/development/index.js'),
        '^react-router/dom$': path.join(path.dirname(require.resolve('react-router/package.json')), 'dist/development/dom-export.js'),
      },
    },
  },
  devServer: {
    host: '0.0.0.0',
    port: process.env.PORT || 5128,
    allowedHosts: 'all',
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws'
    }
  },
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@numerom/api-client': path.resolve(__dirname, '../packages/api-client/index.js'),
      '@numerom/full-report': path.resolve(__dirname, '../packages/full-report/index.js'),
    },
    configure: (webpackConfig) => {
      if (process.platform === 'darwin') {
        webpackConfig.plugins.push(new DirectoryReadGuardPlugin(__dirname));
      }
      
      // The shared package is plain JS and deliberately lives outside CRA src.
      const scope = webpackConfig.resolve.plugins.find(plugin => plugin.constructor.name === 'ModuleScopePlugin');
      if (scope) scope.allowedPaths.push(path.resolve(__dirname, '../packages/api-client'));
      if (scope) scope.allowedPaths.push(path.resolve(__dirname, '../packages/full-report'));

      // Disable hot reload completely if environment variable is set
      if (config.disableHotReload) {
        // Remove hot reload related plugins
        webpackConfig.plugins = webpackConfig.plugins.filter(plugin => {
          return !(plugin.constructor.name === 'HotModuleReplacementPlugin');
        });
        
        // Disable watch mode
        webpackConfig.watch = false;
        webpackConfig.watchOptions = {
          ignored: /.*/, // Ignore all files
        };
      } else {
        // Add ignored patterns to reduce watched directories
        webpackConfig.watchOptions = {
          ...webpackConfig.watchOptions,
          ignored: [
            '**/node_modules/**',
            '**/.git/**',
            '**/build/**',
            '**/dist/**',
            '**/coverage/**',
            '**/public/**',
          ],
        };
      }
      
      return webpackConfig;
    },
  },
};
