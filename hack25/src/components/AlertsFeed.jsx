import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'

const MOCK_ALERTS = [
  { id: 1, message: 'Tower 12 offline (Irving)', severity: 'error', timestamp: new Date() },
  { id: 2, message: 'Latency spike detected in Plano', severity: 'warning', timestamp: new Date(Date.now() - 30000) },
  { id: 3, message: 'Signal quality improved in Dallas', severity: 'success', timestamp: new Date(Date.now() - 60000) },
]

const ALERT_TEMPLATES = [
  { message: 'Tower {n} offline ({city})', severity: 'error' },
  { message: 'Latency spike detected in {city}', severity: 'warning' },
  { message: 'Signal quality improved in {city}', severity: 'success' },
  { message: 'High call drop rate in {city}', severity: 'warning' },
  { message: 'Tower {n} restored ({city})', severity: 'success' },
]

const CITIES = ['Dallas', 'Fort Worth', 'Arlington', 'Plano', 'Irving']

/**
 * AlertsFeed - Real-time alerts feed component
 */
function AlertsFeed() {
  const [alerts, setAlerts] = useState(MOCK_ALERTS)

  useEffect(() => {
    const interval = setInterval(() => {
      const template = ALERT_TEMPLATES[Math.floor(Math.random() * ALERT_TEMPLATES.length)]
      const city = CITIES[Math.floor(Math.random() * CITIES.length)]
      const towerNum = Math.floor(Math.random() * 20) + 1
      
      const message = template.message
        .replace('{city}', city)
        .replace('{n}', towerNum.toString())
      
      const newAlert = {
        id: Date.now(),
        message,
        severity: template.severity,
        timestamp: new Date(),
      }
      
      setAlerts(prev => [newAlert, ...prev].slice(0, 5))
    }, 8000) // Add new alert every 8 seconds

    return () => clearInterval(interval)
  }, [])

  const getSeverityVariant = (severity) => {
    switch (severity) {
      case 'error': return 'error'
      case 'warning': return 'warning'
      case 'success': return 'success'
      default: return 'default'
    }
  }

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="text-lg">Alerts Feed</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <div className="space-y-3 h-full overflow-y-auto pr-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 border border-border animate-in fade-in slide-in-from-right-2"
            >
              <Badge variant={getSeverityVariant(alert.severity)} className="mt-0.5 flex-shrink-0">
                {alert.severity === 'error' ? '🔴' : alert.severity === 'warning' ? '🟡' : '🟢'}
              </Badge>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{alert.message}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {formatTime(alert.timestamp)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default AlertsFeed

