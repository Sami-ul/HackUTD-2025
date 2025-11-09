import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

// Mock history data
const MOCK_HISTORY = [
  { timestamp: '20:00', call_drops: 5, latency: 45 },
  { timestamp: '20:05', call_drops: 3, latency: 42 },
  { timestamp: '20:10', call_drops: 6, latency: 48 },
  { timestamp: '20:15', call_drops: 4, latency: 44 },
  { timestamp: '20:20', call_drops: 2, latency: 40 },
  { timestamp: '20:25', call_drops: 7, latency: 50 },
]

const MOCK_REGIONS = [
  { region: 'Dallas', latency: 45 },
  { region: 'Fort Worth', latency: 48 },
  { region: 'Arlington', latency: 42 },
  { region: 'Plano', latency: 50 },
  { region: 'Irving', latency: 44 },
]

const MOCK_TRAFFIC = [
  { time: '20:00', volume: 1200 },
  { time: '20:05', volume: 1350 },
  { time: '20:10', volume: 1100 },
  { time: '20:15', volume: 1400 },
  { time: '20:20', volume: 1500 },
  { time: '20:25', volume: 1300 },
]

/**
 * NetworkCharts - Multiple charts for network insights
 */
function NetworkCharts() {
  const [callDropHistory, setCallDropHistory] = useState(MOCK_HISTORY)
  const [regionLatency, setRegionLatency] = useState(MOCK_REGIONS)
  const [trafficVolume, setTrafficVolume] = useState(MOCK_TRAFFIC)

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/history')
      
      if (response.ok) {
        const data = await response.json()
        // Format for call drop chart
        const formatted = data.map(item => ({
          timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          }),
          call_drops: item.call_drops || 0,
          latency: 40 + Math.random() * 15, // Simulated latency
        }))
        setCallDropHistory(formatted.slice(-6))
      } else {
        setCallDropHistory(MOCK_HISTORY)
      }
    } catch (error) {
      console.warn('API unavailable, using mock data:', error)
      setCallDropHistory(MOCK_HISTORY)
    }
  }

  const fetchRegionLatency = async () => {
    try {
      const response = await fetch('/api/regions/latency')
      
      if (response.ok) {
        const data = await response.json()
        setRegionLatency(data)
      } else {
        setRegionLatency(MOCK_REGIONS)
      }
    } catch (error) {
      console.warn('API unavailable, using mock data:', error)
      setRegionLatency(MOCK_REGIONS)
    }
  }

  const fetchTrafficVolume = async () => {
    try {
      const response = await fetch('/api/traffic')
      
      if (response.ok) {
        const data = await response.json()
        // Format for traffic volume chart
        const formatted = data.map(item => ({
          time: new Date(item.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          }),
          volume: item.volume || 0,
        }))
        setTrafficVolume(formatted.slice(-6))
      } else {
        setTrafficVolume(MOCK_TRAFFIC)
      }
    } catch (error) {
      console.warn('API unavailable, using mock data:', error)
      setTrafficVolume(MOCK_TRAFFIC)
    }
  }

  useEffect(() => {
    fetchHistory()
    fetchRegionLatency()
    fetchTrafficVolume()
    
    const interval = setInterval(() => {
      fetchHistory()
      fetchRegionLatency()
      fetchTrafficVolume()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Call Drop Rate Over Time */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Call Drop Rate Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={callDropHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="call_drops"
                stroke="#ef4444"
                strokeWidth={2}
                name="Call Drops"
                animationDuration={500}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Latency by Region */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Latency by Region</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={regionLatency}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="latency"
                fill="#3b82f6"
                name="Latency (ms)"
                animationDuration={500}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Network Traffic Volume */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-lg">Network Traffic Volume</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={trafficVolume}>
              <defs>
                <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="volume"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorVolume)"
                name="Call Volume"
                animationDuration={500}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

export default NetworkCharts

