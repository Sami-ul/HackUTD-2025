import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { RadialBarChart, RadialBar, ResponsiveContainer, Cell } from 'recharts'

// Mock metrics data
const MOCK_METRICS = {
  avg_latency: 45,
  call_drop_rate: 1.2,
  signal_quality: 8.6,
  uptime: 99.4,
  active_nodes: 8,
  total_nodes: 10,
}

/**
 * HealthScoreGauge - Network Health Score radial gauge
 */
function HealthScoreGauge() {
  const [metrics, setMetrics] = useState(MOCK_METRICS)
  const [healthScore, setHealthScore] = useState(0)

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics')
      
      if (response.ok) {
        const data = await response.json()
        setMetrics(data)
      } else {
        setMetrics(MOCK_METRICS)
      }
    } catch (error) {
      console.warn('API unavailable, using mock data:', error)
      setMetrics(MOCK_METRICS)
    }
  }

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Calculate health score
    // score = uptime * 0.5 + signal_quality * 5 + (100 - latency / 2) - (drop_rate * 5)
    const score = Math.max(0, Math.min(100,
      metrics.uptime * 0.5 +
      metrics.signal_quality * 5 +
      (100 - metrics.avg_latency / 2) -
      (metrics.call_drop_rate * 5)
    ))
    setHealthScore(Math.round(score))
  }, [metrics])

  const getScoreColor = () => {
    if (healthScore >= 80) return '#22c55e' // green
    if (healthScore >= 60) return '#eab308' // yellow
    return '#ef4444' // red
  }

  const getScoreVariant = () => {
    if (healthScore >= 80) return 'success'
    if (healthScore >= 60) return 'warning'
    return 'error'
  }

  const chartData = [
    {
      name: 'Health Score',
      value: healthScore,
      fill: getScoreColor(),
    },
  ]

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="text-lg">Network Health Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center">
          <ResponsiveContainer width="100%" height={200}>
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              barSize={20}
              data={chartData}
              startAngle={90}
              endAngle={-270}
            >
              <RadialBar
                dataKey="value"
                cornerRadius={10}
                fill={getScoreColor()}
                animationDuration={1000}
              />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-center">
            <div className="text-5xl font-bold mb-2" style={{ color: getScoreColor() }}>
              {healthScore}
            </div>
            <div className="text-sm text-muted-foreground">out of 100</div>
            <div className="mt-3">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  healthScore >= 80
                    ? 'bg-green-100 text-green-800'
                    : healthScore >= 60
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {healthScore >= 80 ? 'Excellent' : healthScore >= 60 ? 'Good' : 'Needs Attention'}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default HealthScoreGauge

