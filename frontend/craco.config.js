// Load configuration from environment or config file
const path = require('path');

// Force-disable React Fast Refresh in production to avoid runtime conflicts
if (process.env.NODE_ENV === 'production') {
  process.env.FAST_REFRESH = 'false';
}

// Environment variable overrides
const config = {
  disableHotReload: process.env.DISABLE_HOT_RELOAD === 'true' || process.env.NODE_ENV === 'production',
};

module.exports = {
  webpack: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    configure: (webpackConfig) => {
      // In production or when explicitly disabled, remove HMR/React Refresh completely
      if (config.disableHotReload) {
        // Remove hot reload related plugins including ReactRefreshPlugin
        webpackConfig.plugins = (webpackConfig.plugins || []).filter((plugin) => {
          const name = plugin && plugin.constructor && plugin.constructor.name;
          return !(
            name === 'HotModuleReplacementPlugin' ||
            name === 'ReactRefreshPlugin'
          );
        });

        // Ensure devServer-related hot reload features are off if present
        if (webpackConfig.devServer) {
          webpackConfig.devServer.hot = false;
          webpackConfig.devServer.liveReload = false;
        }

        // Disable watch mode fully in production service use
        webpackConfig.watch = false;
        webpackConfig.watchOptions = {
          ignored: /.*/, // Ignore all files
        };
      } else {
        // Add ignored patterns to reduce watched directories during development
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