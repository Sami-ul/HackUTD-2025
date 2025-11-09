import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './SentimentPanel.css';

function SentimentPanel({ currentSentiment, currentEmotion, currentUrgency, sentimentHistory, sentimentChange }) {
  // Prepare chart data - handle both formats (with sentiment object or direct score)
  const chartData = sentimentHistory.length > 0
    ? sentimentHistory.map((item, idx) => {
        const timestamp = item.timestamp || item.time || new Date().toISOString();
        const time = item.time || new Date(timestamp).toLocaleTimeString() || `Point ${idx + 1}`;
        const score = item.sentiment?.score !== undefined 
          ? item.sentiment.score 
          : (typeof item.score === 'number' ? item.score : 0);
        return { time, score, index: idx };
      })
    : [{ time: 'Start', score: currentSentiment.score || 0, index: 0 }];

  const getSentimentColor = (label) => {
    const colors = {
      'very_positive': '#10b981',
      'positive': '#34d399',
      'neutral': '#6b7280',
      'negative': '#f59e0b',
      'very_negative': '#ef4444'
    };
    return colors[label] || '#6b7280';
  };

  const getSentimentIcon = (label) => {
    const icons = {
      'very_positive': '😄',
      'positive': '🙂',
      'neutral': '😐',
      'negative': '😞',
      'very_negative': '😠'
    };
    return icons[label] || '😐';
  };

  const getEmotionIcon = (emotion) => {
    const icons = {
      'angry': '😠',
      'frustrated': '😤',
      'disappointed': '😞',
      'confused': '😕',
      'anxious': '😰',
      'satisfied': '🙂',
      'happy': '😄',
      'neutral': '😐'
    };
    return icons[emotion] || '😐';
  };

  return (
    <div className="sentiment-panel">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Current Sentiment</h3>
        </div>
        <div className="sentiment-display">
          <div className="sentiment-main">
            <span className="sentiment-icon">{getSentimentIcon(currentSentiment.label)}</span>
            <div>
              <div className={`sentiment-badge sentiment-${currentSentiment.label}`}>
                {currentSentiment.label.replace('_', ' ')}
              </div>
              <div className="sentiment-score">
                Score: {currentSentiment.score.toFixed(3)}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Emotion & Urgency</h3>
        </div>
        <div className="emotion-urgency">
          <div className="emotion-item">
            <span className="emotion-icon">{getEmotionIcon(currentEmotion)}</span>
            <div>
              <div className="emotion-label">Emotion</div>
              <div className="emotion-value">{currentEmotion}</div>
            </div>
          </div>
          <div className="urgency-item">
            <div className={`urgency-badge urgency-${currentUrgency.level.toLowerCase()}`}>
              {currentUrgency.level}
            </div>
            <div className="urgency-score">
              Score: {currentUrgency.score.toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Sentiment Trend</h3>
        </div>
        <div className="sentiment-chart">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke={getSentimentColor(currentSentiment.label)}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Sentiment Score"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">
              <p>No sentiment data yet</p>
            </div>
          )}
        </div>
        {sentimentChange !== 0 && (
          <div className={`sentiment-change ${sentimentChange > 0 ? 'positive' : 'negative'}`}>
            {sentimentChange > 0 ? '📈' : '📉'} 
            Sentiment {sentimentChange > 0 ? 'improved' : 'declined'} by {Math.abs(sentimentChange).toFixed(3)}
          </div>
        )}
      </div>
    </div>
  );
}

export default SentimentPanel;

