import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { RadialBarChart, RadialBar, ResponsiveContainer, Cell } from 'recharts'

// Mock transcription chunks
const TRANSCRIPTION_CHUNKS = [
  "Thank you for calling T-Mobile, this is Sarah. How can I help you today?",
  "Hi, I've been experiencing really slow internet speeds for the past week.",
  "I understand your frustration. Let me check your account and see what might be causing this issue.",
  "I've tried restarting my router multiple times, but nothing seems to work.",
  "I can see there's a network maintenance scheduled in your area. That might be affecting your service.",
  "Let me escalate this to our technical team right away.",
  "That would be great. I really need this fixed soon.",
]

// Mock caller info
const MOCK_CALLER = {
  name: 'John Smith',
  age: 34,
  city: 'Dallas, TX',
  accountId: 'ACC-789456',
  signalStrength: 85,
  sentiment: 'frustrated',
}

// Mock analysis
const MOCK_ANALYSIS = {
  tone: 'frustrated',
  emotion: 75, // 0-100 scale
  keyInsights: [
    'Experiencing slow internet speeds',
    'Multiple router restarts attempted',
    'Network maintenance in area',
    'Needs urgent resolution',
  ],
}

/**
 * LiveCallerDashboard - Real-time caller monitoring and analysis
 */
function LiveCallerDashboard() {
  const [transcription, setTranscription] = useState([])
  const [callerInfo, setCallerInfo] = useState(MOCK_CALLER)
  const [analysis, setAnalysis] = useState(MOCK_ANALYSIS)

  useEffect(() => {
    // Simulate live transcription updates
    let chunkIndex = 0
    
    const interval = setInterval(() => {
      if (chunkIndex < TRANSCRIPTION_CHUNKS.length) {
        setTranscription(prev => [
          ...prev,
          {
            id: Date.now(),
            text: TRANSCRIPTION_CHUNKS[chunkIndex],
            timestamp: new Date().toLocaleTimeString(),
            speaker: chunkIndex % 2 === 0 ? 'Agent' : 'Caller',
          }
        ])
        chunkIndex++
      } else {
        // Reset and start over for demo
        chunkIndex = 0
        setTranscription([])
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Simulate analysis updates
    const interval = setInterval(() => {
      setAnalysis(prev => ({
        ...prev,
        emotion: Math.max(50, Math.min(100, prev.emotion + (Math.random() - 0.5) * 10)),
      }))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const getToneColor = (tone) => {
    switch (tone) {
      case 'frustrated': return '#ef4444'
      case 'satisfied': return '#22c55e'
      case 'neutral': return '#eab308'
      default: return '#3b82f6'
    }
  }

  const emotionData = [
    {
      name: 'Emotion Level',
      value: analysis.emotion,
      fill: getToneColor(analysis.tone),
    },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 animate-in fade-in duration-300">
      {/* Live Transcription - Takes 2 columns */}
      <div className="lg:col-span-2">
        <Card className="h-full flex flex-col">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🎙️</span>
              Live Transcription
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-hidden">
            <div className="bg-muted/30 rounded-lg p-4 h-full overflow-y-auto space-y-3">
              {transcription.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <p>Waiting for call to begin...</p>
                </div>
              ) : (
                transcription.map((item) => (
                  <div
                    key={item.id}
                    className="animate-in fade-in slide-in-from-bottom-2"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                        item.speaker === 'Agent' ? 'bg-blue-500' : 'bg-green-500'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-muted-foreground">
                            {item.speaker}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {item.timestamp}
                          </span>
                        </div>
                        <p className="text-sm leading-relaxed">{item.text}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right Column - Caller Info and Analysis */}
      <div className="space-y-4">
        {/* Caller Info Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <span>👤</span>
              Caller Info
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-2xl font-bold">{callerInfo.name}</p>
              <p className="text-sm text-muted-foreground">Age {callerInfo.age}</p>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Location</span>
                <span className="font-medium">{callerInfo.city}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Account ID</span>
                <span className="font-medium font-mono text-xs">{callerInfo.accountId}</span>
              </div>
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Signal Strength</span>
                <Badge variant={callerInfo.signalStrength > 70 ? 'success' : 'warning'}>
                  {callerInfo.signalStrength}%
                </Badge>
              </div>
              <Progress value={callerInfo.signalStrength} className="h-2" />
            </div>

            <div className="pt-2 border-t">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Sentiment:</span>
                <Badge variant="error">{callerInfo.sentiment}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Augmented Analysis Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <span>🧠</span>
              Augmented Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Tone/Emotion Meter */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Emotion Level</span>
                <span className="text-sm text-muted-foreground">{Math.round(analysis.emotion)}%</span>
              </div>
              <ResponsiveContainer width="100%" height={120}>
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="40%"
                  outerRadius="80%"
                  barSize={10}
                  data={emotionData}
                  startAngle={90}
                  endAngle={-270}
                >
                  <RadialBar
                    dataKey="value"
                    cornerRadius={10}
                    fill={getToneColor(analysis.tone)}
                    animationDuration={1000}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="text-center mt-2">
                <Badge variant="error" className="text-xs">{analysis.tone}</Badge>
              </div>
            </div>

            {/* Key Insights */}
            <div className="pt-2 border-t">
              <h4 className="text-sm font-medium mb-3">Key Insights</h4>
              <ul className="space-y-2">
                {analysis.keyInsights.map((insight, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-primary mt-0.5">•</span>
                    <span className="text-muted-foreground">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default LiveCallerDashboard

