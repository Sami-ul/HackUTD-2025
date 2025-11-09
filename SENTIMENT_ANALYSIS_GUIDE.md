# 📊 Live Sentiment Analysis Guide

## ✅ What's Now Active

Your voice system now includes **LIVE sentiment analysis** that:

- 😊 Detects positive, negative, and neutral sentiment
- 🎭 Identifies emotions (frustrated, confused, satisfied, urgent)
- 📈 Tracks sentiment trends throughout the call
- ⚠️  Recommends escalation when needed
- 📉 Analyzes call quality and customer satisfaction

---

## 🎯 How It Works

### **Real-Time Analysis Pipeline:**

```
Phone Call → Audio Stream → NeMo ASR → Transcription
                                            ↓
                        Sentiment Analyzer (every ~2 seconds)
                                            ↓
                        Analyzes: Emotions, Trends, Escalation
                                            ↓
                        Stores: History + Progression
                                            ↓
                        Generates: Summary at call end
```

---

## 📱 Live During Call

### **What Gets Analyzed:**

Every 2 seconds of speech:
1. **Sentiment Score**: -1 (very negative) to +1 (very positive)
2. **Primary Sentiment**: positive, neutral, or negative
3. **Emotions Detected**: frustrated, confused, satisfied, urgent
4. **Escalation Flag**: Should a human take over?
5. **Trend Analysis**: Is sentiment improving or declining?

### **Example Live Analysis:**

```
Customer says: "I'm really frustrated with this bill issue!"

Analysis:
  Sentiment: 😠 Negative (score: -0.75)
  Emotions: [frustrated, urgent]
  Should Escalate: YES
  Trend: Declining
```

---

## 🔍 API Endpoints for Sentiment

### **1. Get Latest Sentiment (Real-Time)**
```bash
curl http://localhost:5000/sentiment/<CALL_SID>
```

**Response:**
```json
{
  "call_sid": "CA123...",
  "latest_sentiment": {
    "sentiment_score": -0.67,
    "primary_sentiment": "negative",
    "sentiment_label": "😠 Negative",
    "emotions": ["frustrated", "urgent"],
    "should_escalate": true,
    "confidence": 0.85
  },
  "progression": {
    "trend": "declining",
    "trend_emoji": "📉",
    "average_recent_score": -0.45,
    "needs_immediate_attention": true
  }
}
```

---

### **2. Get Complete Sentiment History**
```bash
curl http://localhost:5000/sentiment/<CALL_SID>/history
```

**Response:**
```json
{
  "call_sid": "CA123...",
  "sentiment_history": [
    {
      "transcription": "what's my bill",
      "sentiment": {
        "sentiment_score": 0.0,
        "primary_sentiment": "neutral",
        "emotions": []
      },
      "progression": {
        "trend": "initial",
        "interaction_count": 1
      }
    },
    {
      "transcription": "this is frustrating and urgent",
      "sentiment": {
        "sentiment_score": -0.75,
        "primary_sentiment": "negative",
        "emotions": ["frustrated", "urgent"],
        "should_escalate": true
      },
      "progression": {
        "trend": "declining",
        "trend_emoji": "📉",
        "escalation_triggers": 1
      }
    }
  ]
}
```

---

### **3. Get Call Summary (After Call Ends)**
```bash
curl http://localhost:5000/sentiment/<CALL_SID>/summary
```

**Response:**
```json
{
  "call_sid": "CA123...",
  "total_interactions": 5,
  "overall_sentiment": "negative",
  "overall_emoji": "😠",
  "average_score": -0.34,
  "sentiment_breakdown": {
    "positive": 1,
    "neutral": 2,
    "negative": 2
  },
  "emotions_detected": ["frustrated", "confused", "urgent"],
  "escalation_count": 2,
  "call_quality": {
    "started_negative": false,
    "ended_positive": false,
    "improved_during_call": false,
    "needs_followup": true
  },
  "score_range": {
    "min": -0.75,
    "max": 0.2,
    "variance": 0.95
  }
}
```

---

### **4. Get Complete Call Data (Everything)**
```bash
curl http://localhost:5000/call_data/<CALL_SID>
```

Includes:
- Audio chunks count
- Intent detected
- Agent response
- **Full sentiment data**
- **Sentiment summary**

---

## 🎭 Detected Emotions

### **Positive Emotions:**
- `satisfied` - Customer is happy
- Multiple positive keywords detected

### **Negative Emotions:**
- `frustrated` - Customer is upset (3+ negative words)
- `urgent` - Needs immediate attention
- `confused` - Needs clarification

### **Keywords Tracked:**

| Emotion | Example Keywords |
|---------|-----------------|
| **Positive** | thank, great, excellent, happy, appreciate, wonderful |
| **Negative** | frustrated, angry, upset, terrible, awful, hate, worst |
| **Urgent** | urgent, immediately, asap, now, emergency, critical |
| **Confused** | confused, don't understand, unclear, what, why, explain |

---

## ⚠️ Escalation Logic

**Automatic escalation recommended when:**

1. **High negativity**: 3+ negative words
2. **Urgency**: 2+ urgent keywords
3. **Combined**: Frustrated + any urgency
4. **Multiple triggers**: 2+ escalations in one call

---

## 📈 Trend Analysis

### **Sentiment Trends:**

- 📈 **Improving**: Scores getting more positive
- 📉 **Declining**: Scores getting more negative  
- ➡️ **Stable**: Consistent sentiment
- 🆕 **Initial**: Just started

### **Example Scenario:**

```
Interaction 1: "What's my bill?" → 😐 0.0 (neutral)
Interaction 2: "This is confusing" → 😐 -0.2 (slight negative)
Interaction 3: "I'm frustrated!" → 😠 -0.7 (negative)
Trend: 📉 DECLINING → RECOMMEND ESCALATION
```

---

## 🧪 Testing Sentiment Analysis

### **Test Case 1: Positive Customer**
```bash
# Say: "Thank you! This is great service, I really appreciate your help!"
# Expected: 😊 Positive (score: ~0.8)
# Emotions: [satisfied]
```

### **Test Case 2: Frustrated Customer**
```bash
# Say: "This is terrible! I'm so frustrated and need help immediately!"
# Expected: 😠 Negative (score: ~-0.9)
# Emotions: [frustrated, urgent]
# Escalation: YES
```

### **Test Case 3: Confused Customer**
```bash
# Say: "I don't understand, can you explain what's happening?"
# Expected: 😐 Neutral/Slight Negative
# Emotions: [confused]
```

### **Test Case 4: Improving Sentiment**
```bash
# Say first: "This is frustrating"
# Then say: "Okay, that makes sense, thank you"
# Trend: 📈 IMPROVING
```

---

## 📊 Real-Time Monitoring

### **Watch Live Sentiment in Logs:**

When running the server, you'll see:

```
INFO: Transcription: what's my bill
INFO: Detected intent: check_bill
INFO: 📊 Sentiment: 😐 Neutral | Score: 0.0 | Emotions: []

INFO: Transcription: this is frustrating and urgent  
INFO: Detected intent: general_inquiry
INFO: 📊 Sentiment: 😠 Negative | Score: -0.75 | Emotions: ['frustrated', 'urgent']
WARNING: ⚠️  ESCALATION RECOMMENDED: declining

INFO: 📊 Final Sentiment: 😠 negative (avg: -0.34)
```

---

## 🎯 Use Cases

### **1. Live Dashboard**
Show real-time sentiment to supervisors:
```javascript
// Poll every 2 seconds
setInterval(() => {
  fetch(`/sentiment/${callSid}`)
    .then(r => r.json())
    .then(data => {
      updateDashboard(data.latest_sentiment);
    });
}, 2000);
```

### **2. Automatic Escalation**
Route calls based on sentiment:
```python
if sentiment_result['should_escalate']:
    transfer_to_human_agent(call_sid)
```

### **3. Post-Call Analytics**
Analyze all calls:
```python
summary = get_sentiment_summary(call_sid)
if summary['call_quality']['needs_followup']:
    schedule_followup_call(customer_id)
```

### **4. Training Data**
Identify problematic patterns:
```python
negative_calls = [
    call for call in calls 
    if call['sentiment_summary']['average_score'] < -0.3
]
```

---

## 🔧 Customization

### **Add Custom Keywords**

Edit `sentiment_analyzer.py`:

```python
self.positive_words = {
    'thank', 'great', 'excellent',
    # Add your industry-specific positive words
    'resolved', 'fixed', 'perfect'
}

self.negative_words = {
    'frustrated', 'angry', 'terrible',
    # Add your specific negative words
    'broken', 'outage', 'down'
}
```

### **Adjust Escalation Thresholds**

```python
should_escalate = (
    (primary_sentiment == "negative" and negative_count >= 3) or  # Change 3
    (urgency_count >= 2) or                                        # Change 2
    ("frustrated" in emotions and urgency_count >= 1)
)
```

---

## 📝 Sample Dashboard Code

```html
<!DOCTYPE html>
<html>
<head>
    <title>Live Sentiment Dashboard</title>
    <style>
        .sentiment { font-size: 24px; padding: 20px; }
        .positive { background: #4CAF50; color: white; }
        .negative { background: #f44336; color: white; }
        .neutral { background: #9E9E9E; color: white; }
    </style>
</head>
<body>
    <h1>Live Call Sentiment</h1>
    <div id="sentiment" class="sentiment">Waiting for data...</div>
    
    <script>
        const callSid = 'CA123...'; // Get from URL or backend
        
        setInterval(async () => {
            const res = await fetch(`/sentiment/${callSid}`);
            const data = await res.json();
            
            const div = document.getElementById('sentiment');
            const sentiment = data.latest_sentiment;
            
            div.innerHTML = `
                ${sentiment.sentiment_label}<br>
                Score: ${sentiment.sentiment_score}<br>
                Emotions: ${sentiment.emotions.join(', ')}<br>
                Trend: ${data.progression.trend_emoji} ${data.progression.trend}
            `;
            
            div.className = `sentiment ${sentiment.primary_sentiment}`;
        }, 2000);
    </script>
</body>
</html>
```

---

## ✅ Quick Test

```bash
# 1. Start server
./start_server.sh

# 2. In another terminal, simulate a call
# (You'll need actual Twilio call, but you can test the endpoint)

# 3. Check health
curl http://localhost:5000/health

# Should show:
# "sentiment_analyzer": "active"
```

---

## 🚀 Next Steps

1. ✅ **Sentiment analysis is LIVE** in your system
2. Make a test call with different emotions
3. Watch the sentiment in real-time logs
4. Query the API endpoints to see data
5. Build a dashboard (optional)
6. Set up automatic escalation rules (optional)

---

## 📚 Integration Examples

### **With Your Nemotron Agent**

The agent can now consider sentiment:

```python
# In nemotron_agent.py
def process_with_sentiment(self, transcription, sentiment_data):
    if sentiment_data['should_escalate']:
        # Use more empathetic language
        context = f"Customer is {sentiment_data['primary_sentiment']}. Be extra helpful."
    else:
        context = f"Normal inquiry from customer."
    
    # ... rest of processing
```

---

**🎉 Sentiment analysis is now LIVE in your system!**

Test it by making calls with different emotional tones and watch the real-time analysis in action!

