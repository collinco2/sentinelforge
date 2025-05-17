const path = require("path");

module.exports = {
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
    configure: (webpackConfig) => {
      // Handle dependency resolution issues
      webpackConfig.resolve = {
        ...webpackConfig.resolve,
        fallback: {
          ...webpackConfig.resolve?.fallback,
        },
      };

      // Force specific versions of React for all dependencies using relative paths
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        react: path.resolve(__dirname, "node_modules/react"),
        "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      };

      // Enable React Refresh properly
      const plugins = webpackConfig.plugins || [];
      plugins.forEach(plugin => {
        if (plugin.constructor.name === 'ReactRefreshPlugin') {
          // It's already included by CRA, but might need configuration
          plugin.options = {
            ...plugin.options,
            overlay: false, // Disable error overlay to prevent path issues
          };
        }
      });

      return webpackConfig;
    },
  },
  // Configure development server
  devServer: {
    hot: true,
  }
}; 