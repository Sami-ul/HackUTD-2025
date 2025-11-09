// Simple mock API server for /api/nodes
// Run with: node mock-api-server.js
// Then access at http://localhost:3001/api/nodes

import http from 'http'

const MOCK_NODES = [
  { id: 1, name: 'Tower Alpha', lat: 32.7767, lon: -96.7970, status: 'online' },
  { id: 2, name: 'Tower Beta', lat: 32.8500, lon: -96.8500, status: 'online' },
  { id: 3, name: 'Tower Gamma', lat: 32.7500, lon: -96.7500, status: 'offline' },
  { id: 4, name: 'Tower Delta', lat: 32.8000, lon: -96.9000, status: 'online' },
  { id: 5, name: 'Tower Epsilon', lat: 32.7200, lon: -96.8200, status: 'online' },
  { id: 6, name: 'Tower Zeta', lat: 32.8800, lon: -96.7800, status: 'offline' },
  { id: 7, name: 'Tower Eta', lat: 32.7000, lon: -96.9500, status: 'online' },
  { id: 8, name: 'Tower Theta', lat: 32.8200, lon: -96.7000, status: 'online' },
  { id: 9, name: 'Tower Iota', lat: 32.7300, lon: -96.8800, status: 'offline' },
  { id: 10, name: 'Tower Kappa', lat: 32.7900, lon: -96.7200, status: 'online' },
]

const server = http.createServer((req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    res.writeHead(200)
    res.end()
    return
  }

  if (req.url === '/api/nodes' && req.method === 'GET') {
    // Simulate some status changes for demo purposes
    const nodesWithRandomStatus = MOCK_NODES.map(node => ({
      ...node,
      // Randomly change status occasionally (10% chance)
      status: Math.random() > 0.9 
        ? (node.status === 'online' ? 'offline' : 'online')
        : node.status
    }))

    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(nodesWithRandomStatus))
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ error: 'Not found' }))
  }
})

const PORT = 3001
server.listen(PORT, () => {
  console.log(`Mock API server running at http://localhost:${PORT}/api/nodes`)
})

