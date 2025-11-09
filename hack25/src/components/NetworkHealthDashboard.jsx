import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import DFWNetworkMap from './DFWNetworkMap'
import DiagnosticPanel from './DiagnosticPanel'
import NetworkCharts from './NetworkCharts'
import AlertsFeed from './AlertsFeed'

/**
 * NetworkHealthDashboard - A comprehensive network operations center dashboard
 * for the DFW region with map, metrics, charts, and alerts.
 * Built with React, Tailwind, shadcn/ui, Recharts, and React-Leaflet.
 */
function NetworkHealthDashboard() {
  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Map and Alerts Feed - Side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4 items-stretch">
        {/* Map - Takes 3 columns */}
        <div className="lg:col-span-3">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="text-lg">DFW Network Map</CardTitle>
            </CardHeader>
            <CardContent className="flex-1">
              <DFWNetworkMap />
            </CardContent>
          </Card>
        </div>

        {/* Alerts Feed - Takes 1 column */}
        <div className="lg:col-span-1">
          <AlertsFeed />
        </div>
      </div>

      {/* Diagnostic KPIs - Horizontal */}
      <div className="mb-4">
        <DiagnosticPanel />
      </div>

      {/* Charts Row */}
      <div className="mb-4">
        <NetworkCharts />
      </div>
    </div>
  )
}

export default NetworkHealthDashboard
