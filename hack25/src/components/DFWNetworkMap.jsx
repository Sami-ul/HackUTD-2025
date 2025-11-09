import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import L from 'leaflet'

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// DFW area center coordinates
const DFW_CENTER = [32.7767, -96.7970]

// Mock data with 15 nodes around DFW area
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
  { id: 11, name: 'Tower Lambda', lat: 32.7600, lon: -96.8000, status: 'online' },
  { id: 12, name: 'Tower Mu', lat: 32.8100, lon: -96.8300, status: 'offline' },
  { id: 13, name: 'Tower Nu', lat: 32.7400, lon: -96.7600, status: 'online' },
  { id: 14, name: 'Tower Xi', lat: 32.8600, lon: -96.9200, status: 'online' },
  { id: 15, name: 'Tower Omicron', lat: 32.7100, lon: -96.9000, status: 'offline' },
]

/**
 * DFWNetworkMap - A self-contained React component that displays network towers
 * on a Leaflet map centered on the Dallas-Fort Worth area.
 * 
 * Features:
 * - Fetches node data from /api/nodes (with mock fallback)
 * - Auto-refreshes every 5 seconds
 * - Color-coded markers (green=online, red=offline)
 * - Clickable markers with popups
 * - Responsive design with Tailwind CSS
 */
function DFWNetworkMap() {
  const [nodes, setNodes] = useState(MOCK_NODES)
  const [isLoading, setIsLoading] = useState(false)
  const [togglingNodeId, setTogglingNodeId] = useState(null)

  const fetchNodes = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/nodes')
      
      if (response.ok) {
        const data = await response.json()
        setNodes(data)
      } else {
        // Fallback to mock data if API is not available
        setNodes(MOCK_NODES)
      }
    } catch (error) {
      // Fallback to mock data on error
      console.warn('API unavailable, using mock data:', error)
      setNodes(MOCK_NODES)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleNodeStatus = async (nodeId) => {
    try {
      setTogglingNodeId(nodeId)
      
      // Optimistic update - update UI immediately
      setNodes(prevNodes => 
        prevNodes.map(node => 
          node.id === nodeId 
            ? { ...node, status: node.status === 'online' ? 'offline' : 'online' }
            : node
        )
      )

      const response = await fetch(`/api/nodes/${nodeId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const updatedNode = await response.json()
        // Update with server response to ensure consistency
        setNodes(prevNodes => 
          prevNodes.map(node => 
            node.id === nodeId ? updatedNode : node
          )
        )
      } else {
        // Revert optimistic update on error
        fetchNodes()
        console.error('Failed to toggle node status')
      }
    } catch (error) {
      // Revert optimistic update on error
      fetchNodes()
      console.error('Error toggling node status:', error)
    } finally {
      setTogglingNodeId(null)
    }
  }

  useEffect(() => {
    // Initial fetch
    fetchNodes()

    // Set up auto-refresh every 5 seconds
    const interval = setInterval(fetchNodes, 5000)

    return () => clearInterval(interval)
  }, [])

  const getMarkerColor = (status) => {
    return status === 'online' ? '#22c55e' : '#ef4444' // green-500 : red-500
  }

  return (
    <div className="w-full h-[400px] rounded-lg shadow-lg overflow-hidden relative">
      <MapContainer
        center={DFW_CENTER}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {nodes.map((node) => (
          <CircleMarker
            key={node.id}
            center={[node.lat, node.lon]}
            radius={16}
            pathOptions={{
              fillColor: getMarkerColor(node.status),
              color: '#ffffff',
              fillOpacity: 1,
              weight: 4,
            }}
            eventHandlers={{
              click: () => {
                // Popup is handled by the Popup component
              },
              mouseover: (e) => {
                const layer = e.target
                layer.setStyle({
                  weight: 6,
                  radius: 18,
                })
              },
              mouseout: (e) => {
                const layer = e.target
                layer.setStyle({
                  weight: 4,
                  radius: 16,
                })
              },
            }}
          >
            <Popup>
              <div className="p-2 min-w-[180px]">
                <h3 className="font-semibold text-gray-900 mb-2">{node.name}</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Status: <span className={`font-medium ${node.status === 'online' ? 'text-green-600' : 'text-red-600'}`}>
                    {node.status}
                  </span>
                </p>
                <button
                  onClick={() => toggleNodeStatus(node.id)}
                  disabled={togglingNodeId === node.id}
                  className={`w-full px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    node.status === 'online'
                      ? 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200'
                      : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {togglingNodeId === node.id ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Toggling...
                    </span>
                  ) : (
                    `Toggle to ${node.status === 'online' ? 'Offline' : 'Online'}`
                  )}
                </button>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-3 z-[1000]">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Status</h4>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600">Online</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-xs text-gray-600">Offline</span>
          </div>
        </div>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md px-3 py-2 z-[1000]">
          <span className="text-sm text-gray-600">Refreshing...</span>
        </div>
      )}
    </div>
  )
}

export default DFWNetworkMap

