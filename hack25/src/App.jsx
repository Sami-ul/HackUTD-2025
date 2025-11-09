import { useState } from 'react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/ui/tabs'
import SentimentDashboard from './components/SentimentDashboard'
import NetworkHealthDashboard from './components/NetworkHealthDashboard'
import LiveCallerDashboard from './components/LiveCallerDashboard'

/**
 * NetPulse - Main application with three interactive dashboards
 */
function App() {
  const [activeTab, setActiveTab] = useState('sentiment')

  return (
    <div className="min-h-screen bg-background">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 bg-background border-b border-border p-4 flex items-center justify-between shadow-sm">
        <h1 className="text-2xl font-bold text-primary">🧠 NetPulse</h1>
        <div className="text-sm text-muted-foreground">
          Network Intelligence Dashboard
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto p-4 md:p-6 lg:p-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="sentiment" className="flex items-center gap-2">
              <span>🧠</span>
              Sentiment Analysis
            </TabsTrigger>
            <TabsTrigger value="network" className="flex items-center gap-2">
              <span>📡</span>
              Network Health
            </TabsTrigger>
            <TabsTrigger value="caller" className="flex items-center gap-2">
              <span>☎️</span>
              Live Caller
            </TabsTrigger>
          </TabsList>

          <TabsContent value="sentiment" className="mt-0">
            <SentimentDashboard />
          </TabsContent>

          <TabsContent value="network" className="mt-0">
            <NetworkHealthDashboard />
          </TabsContent>

          <TabsContent value="caller" className="mt-0">
            <LiveCallerDashboard />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App
