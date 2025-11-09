import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'

// Mock metrics data
const MOCK_METRICS = {
  avg_latency: 45,
  call_drop_rate: 1.2,
  signal_quality: 8.6,
  uptime: 99.4,
  active_nodes: 10,
  total_nodes: 15,
}

/**
 * DiagnosticPanel - Displays key network health metrics as KPI cards
 */
function DiagnosticPanel() {
  const [metrics, setMetrics] = useState(MOCK_METRICS)
  const [isLoading, setIsLoading] = useState(false)

  const fetchMetrics = async () => {
    try {
      setIsLoading(true)
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
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  const getStatusBadge = (value, thresholds, reverse = false) => {
    if (reverse) {
      if (value <= thresholds.good) return { variant: 'success', label: 'Good' }
      if (value <= thresholds.warning) return { variant: 'warning', label: 'Warning' }
      return { variant: 'error', label: 'Critical' }
    } else {
      if (value >= thresholds.good) return { variant: 'success', label: 'Good' }
      if (value >= thresholds.warning) return { variant: 'warning', label: 'Warning' }
      return { variant: 'error', label: 'Critical' }
    }
  }

  const KPICard = ({ title, value, unit, thresholds, reverse = false, icon }) => {
    const status = getStatusBadge(value, thresholds, reverse)
    
    return (
      <Card className="transition-all duration-300 hover:shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">{title}</span>
            <Badge variant={status.variant}>{status.label}</Badge>
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold">{value}</span>
            {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
          </div>
          {icon && <div className="mt-2 text-2xl">{icon}</div>}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Diagnostic KPIs</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <KPICard
            title="Average Latency"
            value={metrics.avg_latency}
            unit="ms"
            thresholds={{ good: 50, warning: 100 }}
            reverse={true}
            icon="⚡"
          />
          <KPICard
            title="Call Drop Rate"
            value={metrics.call_drop_rate}
            unit="%"
            thresholds={{ good: 1, warning: 3 }}
            icon="📞"
          />
          <KPICard
            title="Signal Quality"
            value={metrics.signal_quality}
            unit="/10"
            thresholds={{ good: 7, warning: 5 }}
            icon="📶"
          />
          <KPICard
            title="Uptime"
            value={metrics.uptime}
            unit="%"
            thresholds={{ good: 99, warning: 95 }}
            icon="✅"
          />
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50">
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Active Nodes</span>
                <Badge 
                  variant={metrics.active_nodes === metrics.total_nodes ? 'success' : 
                          metrics.active_nodes >= metrics.total_nodes * 0.8 ? 'warning' : 'error'}
                >
                  {metrics.active_nodes === metrics.total_nodes ? '🟢' : 
                   metrics.active_nodes >= metrics.total_nodes * 0.8 ? '🟡' : '🔴'}
                </Badge>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-blue-700">
                  {metrics.active_nodes}
                </span>
                <span className="text-sm text-muted-foreground">/ {metrics.total_nodes}</span>
              </div>
              <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${(metrics.active_nodes / metrics.total_nodes) * 100}%` }}
                ></div>
              </div>
            </div>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">Total Nodes</span>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold">{metrics.total_nodes}</span>
              </div>
              <div className="mt-2 text-2xl">📊</div>
            </CardContent>
          </Card>
        </div>
      </CardContent>
    </Card>
  )
}

export default DiagnosticPanel
