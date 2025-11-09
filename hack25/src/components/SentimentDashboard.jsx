import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Button } from './ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// Mock call data
const MOCK_CALLS = [
  { id: 1, caller: 'John D.', duration: '4:32', sentiment: 'negative', csat: 2, summary: 'Billing dispute, frustrated' },
  { id: 2, caller: 'Sarah M.', duration: '8:15', sentiment: 'positive', csat: 5, summary: 'Plan upgrade inquiry, satisfied' },
  { id: 3, caller: 'Mike T.', duration: '2:45', sentiment: 'neutral', csat: 3, summary: 'Technical support, routine' },
  { id: 4, caller: 'Emily R.', duration: '6:20', sentiment: 'negative', csat: 1, summary: 'Service outage complaint' },
  { id: 5, caller: 'David L.', duration: '5:10', sentiment: 'positive', csat: 5, summary: 'New customer onboarding' },
]

const SUBREDDITS = ['TMobile', 'tmobileISP', 'tmobile']

/**
 * SentimentDashboard - Displays sentiment analysis from Reddit and customer calls
 */
function SentimentDashboard() {
  const [redditPosts, setRedditPosts] = useState([])
  const [calls, setCalls] = useState(MOCK_CALLS)
  const [sentimentCounts, setSentimentCounts] = useState({ positive: 0, neutral: 0, negative: 0 })
  const [isLoading, setIsLoading] = useState(false)
  const [selectedSubreddit, setSelectedSubreddit] = useState('TMobile')

  const formatTime = (timestamp) => {
    const date = new Date(timestamp * 1000)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  const analyzeSentiment = async (text) => {
    try {
      const response = await fetch('/api/sentiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      console.warn('Sentiment analysis failed:', error)
    }
    return { sentiment: 'neutral', score: 0.5 }
  }

  const fetchRedditPosts = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/reddit?subreddit=${selectedSubreddit}`)
      
      if (response.ok) {
        const posts = await response.json()
        
        // Analyze sentiment for each post
        const postsWithSentiment = await Promise.all(
          posts.map(async (post) => {
            const text = `${post.title} ${post.selftext}`.trim()
            const sentimentData = await analyzeSentiment(text)
            return {
              ...post,
              sentiment: sentimentData.sentiment,
              sentimentScore: sentimentData.score,
              time: formatTime(post.created_utc),
            }
          })
        )
        
        setRedditPosts(postsWithSentiment)
      } else {
        console.warn('Failed to fetch Reddit posts')
        setRedditPosts([])
      }
    } catch (error) {
      console.warn('Error fetching Reddit posts:', error)
      setRedditPosts([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchRedditPosts()
    const interval = setInterval(fetchRedditPosts, 5 * 60 * 1000) // Every 5 minutes
    return () => clearInterval(interval)
  }, [selectedSubreddit])

  useEffect(() => {
    // Calculate sentiment counts
    const counts = redditPosts.reduce((acc, post) => {
      acc[post.sentiment] = (acc[post.sentiment] || 0) + 1
      return acc
    }, { positive: 0, neutral: 0, negative: 0 })
    setSentimentCounts(counts)
  }, [redditPosts])

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'success'
      case 'negative': return 'error'
      default: return 'default'
    }
  }

  const getSentimentBorder = (sentiment) => {
    return sentiment === 'negative' ? 'border-red-300 border-2' : 'border-border'
  }

  const getCSatColor = (csat) => {
    if (csat >= 4) return 'text-green-600 font-bold'
    if (csat >= 3) return 'text-yellow-600 font-bold'
    return 'text-red-600 font-bold'
  }

  const barChartData = [
    { name: 'Positive', value: sentimentCounts.positive, fill: '#22c55e' },
    { name: 'Neutral', value: sentimentCounts.neutral, fill: '#eab308' },
    { name: 'Negative', value: sentimentCounts.negative, fill: '#ef4444' },
  ]

  const pieChartData = [
    { name: 'Positive', value: sentimentCounts.positive, fill: '#22c55e' },
    { name: 'Neutral', value: sentimentCounts.neutral, fill: '#eab308' },
    { name: 'Negative', value: sentimentCounts.negative, fill: '#ef4444' },
  ]

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Customer Call Sentiment */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <span>📞</span>
            Customer Call Sentiment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Caller</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Sentiment</TableHead>
                <TableHead>CSat Score</TableHead>
                <TableHead>Summary</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {calls.map((call) => (
                <TableRow key={call.id}>
                  <TableCell className="font-medium">{call.caller}</TableCell>
                  <TableCell>{call.duration}</TableCell>
                  <TableCell>
                    <Badge variant={getSentimentColor(call.sentiment)}>
                      {call.sentiment}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className={getCSatColor(call.csat)}>
                      {call.csat}/5
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{call.summary}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Reddit Feed Monitor - Full Width */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <span>📱</span>
              Reddit Feed Monitor
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={selectedSubreddit}
                onChange={(e) => setSelectedSubreddit(e.target.value)}
                className="px-3 py-1.5 text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {SUBREDDITS.map((sub) => (
                  <option key={sub} value={sub}>
                    r/{sub}
                  </option>
                ))}
              </select>
              <Button
                onClick={fetchRedditPosts}
                disabled={isLoading}
                variant="outline"
                size="sm"
              >
                <span className="mr-2">🔄</span>
                {isLoading ? 'Loading...' : 'Refresh Feed'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {redditPosts.length === 0 && !isLoading ? (
            <div className="text-center text-muted-foreground py-8">
              <p>No posts found. Try refreshing or check the subreddit.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Scrollable Reddit Posts List */}
              <div className="lg:col-span-2">
                <div className="h-[500px] overflow-y-auto pr-2 space-y-3">
                  {redditPosts.map((post, index) => (
                    <a
                      key={post.id}
                      href={post.permalink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`block p-3 rounded-lg border ${getSentimentBorder(post.sentiment)} bg-card transition-all hover:shadow-md hover:border-primary/50 cursor-pointer animate-in fade-in`}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h4 className="font-medium text-sm flex-1 hover:text-primary transition-colors line-clamp-2">
                          {post.title}
                        </h4>
                        <Badge variant={getSentimentColor(post.sentiment)} className="text-xs flex-shrink-0 ml-2">
                          {post.sentiment}
                        </Badge>
                      </div>
                      
                      {/* Post Content */}
                      {post.selftext && (
                        <div className="mb-2">
                          <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                            {post.selftext}
                          </p>
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                        <span>u/{post.author}</span>
                        <span>⬆️ {post.ups}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">{post.time}</span>
                        <span className={`font-semibold ${
                          post.sentiment === 'positive' ? 'text-green-600' :
                          post.sentiment === 'negative' ? 'text-red-600' : 'text-yellow-600'
                        }`}>
                          {(post.sentimentScore * 100).toFixed(0)}%
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>

              {/* Sentiment Charts - Side Panel */}
              <div className="space-y-4">
                {/* Bar Chart */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Sentiment Distribution</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={barChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Pie Chart */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Sentiment Breakdown</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={pieChartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {pieChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default SentimentDashboard
