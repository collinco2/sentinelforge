const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://localhost:5056",
      changeOrigin: true,
      pathRewrite: {
        "^/api": "/api", // No rewrite needed
      },
      logLevel: "debug",
    }),
  );
};
