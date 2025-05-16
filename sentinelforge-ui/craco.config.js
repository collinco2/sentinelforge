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

      // Force specific versions of React for all dependencies
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        react: require.resolve("react"),
        "react-dom": require.resolve("react-dom"),
        "@types/react": require.resolve("@types/react"),
      };

      return webpackConfig;
    },
  },
};
