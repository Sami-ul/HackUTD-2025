import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

// Mock history data
const MOCK_HISTORY = [
  { timestamp: '20:00', call_drops: 5, active_nodes: 19 },
  { timestamp: '20:05', call_drops: 3, active_nodes: 20 },
  { timestamp: '20:10', call_drops: 6, active_nodes: 18 },
  { timestamp: '20:15', call_drops: 4, active_nodes: 19 },
  { timestamp: '20:20', call_drops: 2, active_nodes: 20 },
  { timestamp: '20:25', call_drops: 7, active_nodes: 17 },
]

/**
 * LiveMetricsChart - Displays live trends in call drops and node activity
 */
function LiveMetricsChart() {
  const [history, setHistory] = useState(MOCK_HISTORY)
  const [isLoading, setIsLoading] = useState(false)

  const fetchHistory = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/history')
      
      if (response.ok) {
        const data = await response.json()
        // Format timestamps to HH:MM for display
        const formatted = data.map(item => ({
          ...item,
          timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          }),
        }))
        setHistory(formatted)
      } else {
        // Fallback to mock data
        setHistory(MOCK_HISTORY)
      }
    } catch (error) {
      console.warn('API unavailable, using mock data:', error)
      setHistory(MOCK_HISTORY)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    // Initial fetch
    fetchHistory()

    // Set up auto-refresh every 60 seconds (1 minute)
    const interval = setInterval(fetchHistory, 60000)

    return () => clearInterval(interval)
  }, [])

  // Custom tooltip - Horizon UI Style
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-xl shadow-xl backdrop-blur-sm">
          <p className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide">
            {payload[0].payload.timestamp}
          </p>
          <div className="space-y-2">
            {payload.map((entry, index) => (
              <div key={index} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: entry.color }}
                  ></div>
                  <span className="text-sm font-medium text-gray-600">{entry.name}:</span>
                </div>
                <span className="text-sm font-bold" style={{ color: entry.color }}>
                  {entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="w-full">
      {isLoading && (
        <div className="text-center text-sm text-gray-500 py-2 mb-4">
          Refreshing chart data...
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={350}>
        <LineChart
          data={history}
          margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
        >
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#e5e7eb" 
            opacity={0.5}
          />
          <XAxis
            dataKey="timestamp"
            stroke="#9ca3af"
            style={{ fontSize: '12px', fontWeight: '500' }}
            tick={{ fill: '#6b7280' }}
          />
          <YAxis
            yAxisId="left"
            stroke="#ef4444"
            style={{ fontSize: '12px', fontWeight: '500' }}
            tick={{ fill: '#ef4444' }}
            label={{ 
              value: 'Call Drops', 
              angle: -90, 
              position: 'insideLeft',
              style: { textAnchor: 'middle', fill: '#ef4444', fontSize: '12px', fontWeight: '600' }
            }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#22c55e"
            style={{ fontSize: '12px', fontWeight: '500' }}
            tick={{ fill: '#22c55e' }}
            label={{ 
              value: 'Active Nodes', 
              angle: 90, 
              position: 'insideRight',
              style: { textAnchor: 'middle', fill: '#22c55e', fontSize: '12px', fontWeight: '600' }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="line"
            iconSize={12}
            formatter={(value) => <span className="text-sm font-semibold text-gray-700">{value}</span>}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="call_drops"
            stroke="#ef4444"
            strokeWidth={3}
            dot={{ fill: '#ef4444', r: 5, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 7, strokeWidth: 2, stroke: '#fff' }}
            name="Call Drops"
            animationDuration={500}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="active_nodes"
            stroke="#22c55e"
            strokeWidth={3}
            dot={{ fill: '#22c55e', r: 5, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 7, strokeWidth: 2, stroke: '#fff' }}
            name="Active Nodes"
            animationDuration={500}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default LiveMetricsChart

