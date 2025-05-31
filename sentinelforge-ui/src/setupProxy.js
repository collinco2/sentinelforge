const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Main API endpoints
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5059',
      changeOrigin: true,
      pathRewrite: false,
      logLevel: 'debug',
    })
  );

  // Timeline API endpoints
  app.use(
    '/api/alerts/timeline',
    createProxyMiddleware({
      target: 'http://localhost:5101',
      changeOrigin: true,
      logLevel: 'debug',
    })
  );
};
