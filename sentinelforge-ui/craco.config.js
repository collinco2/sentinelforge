const path = require("path");

module.exports = {
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
    configure: (webpackConfig) => {
      // Disable ModuleScopePlugin to allow imports outside of src/
      webpackConfig.resolve.plugins = webpackConfig.resolve.plugins.filter(
        plugin => plugin.constructor.name !== 'ModuleScopePlugin'
      );

      return webpackConfig;
    },
  },
  // Configure development server
  devServer: {
    hot: true,
  }
};
