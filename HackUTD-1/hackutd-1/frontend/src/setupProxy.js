const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API requests to Flask backend
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5001',
      changeOrigin: true,
      ws: false, // WebSocket handled separately
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        // Add CORS headers
        proxyReq.setHeader('Origin', 'http://localhost:5001');
      }
    })
  );
  
  // Proxy Socket.IO requests (both HTTP polling and WebSocket)
  app.use(
    '/socket.io',
    createProxyMiddleware({
      target: 'http://localhost:5001',
      changeOrigin: true,
      ws: true, // Enable WebSocket proxying
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        // Don't override Origin - let it pass through
      },
      onProxyReqWs: (proxyReq, req, socket, options, head) => {
        // Handle WebSocket upgrade
      }
    })
  );
};

