const path = require("path");

module.exports = {
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
    configure: (webpackConfig) => {
      const scopePluginIndex = webpackConfig.resolve.plugins.findIndex(
        (plugin) => plugin.constructor.name === "ModuleScopePlugin",
      );
      if (scopePluginIndex !== -1) {
        webpackConfig.resolve.plugins.splice(scopePluginIndex, 1);
        console.log("Attempted to remove ModuleScopePlugin.");
      } else {
        console.log("ModuleScopePlugin not found.");
      }
      return webpackConfig;
    },
  },
  devServer: {
    port: 3000,
    host: "0.0.0.0",
    hot: true,
    open: false,
    allowedHosts: "all",
    historyApiFallback: true,
    setupMiddlewares: (middlewares, devServer) => {
      // Custom middleware setup if needed
      return middlewares;
    },
  },
};
