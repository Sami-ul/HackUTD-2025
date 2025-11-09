# T-Mobile Network Health Dashboard

A comprehensive sentiment analysis and routing system for T-Mobile customer service calls, built for HackUTD.

## 🎯 Project Overview

This project provides:
1. **Real-time Sentiment Analysis** on customer service call transcripts
2. **Intelligent Call Routing** based on sentiment, urgency, and issue type
3. **Reddit Data Collection** for identifying trending issues
4. **Network Health Monitoring** by flagging issues from customer interactions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
cd HackUTD-1

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### 1. Scrape Reddit for T-Mobile Issues

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'hackutd-1'))

from src.reddit_scraper import RedditWebScraper

scraper = RedditWebScraper()
posts = scraper.scrape_subreddit('tmobile', sort='hot', limit=25)
```

#### 2. Analyze Call Transcript Sentiment

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'hackutd-1'))

from src.call_transcript_analyzer import (
    CallTranscriptSentimentAnalyzer, 
    CallTranscript
)

# Initialize analyzer
analyzer = CallTranscriptSentimentAnalyzer(model_type='sklearn')

# Create a transcript
transcript = CallTranscript(
    transcript_id="call_001",
    customer_text="I'm frustrated with the service in my area...",
    agent_text="I understand. Let me help...",
    full_transcript="Customer: ... Agent: ..."
)

# Analyze sentiment
prediction = analyzer.predict_sentiment(transcript)
print(f"Sentiment: {prediction.sentiment_label}")
print(f"Urgency: {prediction.urgency_score}")
print(f"Routing: {prediction.routing_recommendation}")
```

#### 3. Train a Custom Model

```bash
# Create sample training data
python hackutd_1/scripts/train_sentiment_model.py --create-sample

# Train the model
cd hackutd-1
python scripts/train_sentiment_model.py \
    --data data/sample_training_data.json \
    --model-type sklearn \
    --output models/sentiment_model.pkl
```

#### 4. Run Examples

```bash
cd hackutd-1
python scripts/example_usage.py
```

## 📁 Project Structure

```
HackUTD-1/
├── hackutd_1/
│   ├── src/
│   │   ├── reddit_scraper.py          # Reddit web scraper
│   │   └── call_transcript_analyzer.py # Sentiment analysis for call transcripts
│   ├── scripts/
│   │   ├── train_sentiment_model.py   # Training script
│   │   └── example_usage.py           # Example usage
│   ├── models/                        # Saved models (created after training)
│   └── data/                          # Training data (created after data collection)
├── DATA_SOURCES.md                    # Guide to finding call transcript data
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

## 📊 Data Sources

See [DATA_SOURCES.md](DATA_SOURCES.md) for comprehensive information on:
- Where to find call transcript datasets
- How to create your own training data
- Data format requirements
- Data collection strategies

### Quick Data Collection Options:

1. **Reddit Scraping** (Already implemented)
   - Scrape r/tmobile for customer complaints
   - Use as proxy for call transcripts

2. **Public Datasets**
   - Kaggle customer service datasets
   - Hugging Face datasets
   - Academic corpora

3. **Synthetic Data**
   - Create realistic call transcripts
   - Label manually for training

## 🎓 Training Your Model

### Train Sklearn Model (Fast, Simple, Recommended)

```bash
cd hackutd-1

# Step 1: Prepare your data (supports JSON, CSV, or Parquet)
python scripts/prepare_training_data.py your_transcripts.parquet --output data/training_data.json

# Step 2: Add labels to data/training_data.json
# Add 'customer_sentiment' to each transcript: 'very_positive', 'positive', 'neutral', 'negative', 'very_negative'

# Step 3: Train the model
python scripts/train_sentiment_model.py \
    --data data/training_data.json \
    --output models/sentiment_model.pkl

# Or train directly from parquet (if it has labels):
python scripts/train_sentiment_model.py \
    --data ../train-00000-of-00001.parquet \
    --output models/sentiment_model.pkl
```

**Benefits:**
- Very fast training and inference
- Simple to use
- No large model downloads
- Works well with 50+ labeled examples

## 🔧 Features

### Sentiment Analysis
- **Sentiment Labels**: very_positive, positive, neutral, negative, very_negative
- **Emotion Detection**: angry, frustrated, satisfied, happy, etc.
- **Urgency Scoring**: 0-1 scale for call urgency
- **Issue Categorization**: network, billing, customer_service, technical, etc.

### Call Routing Recommendations
Based on sentiment analysis, the system recommends:
- `human_escalation`: For high urgency or very negative sentiment
- `agent_qa`: For billing/plan questions with neutral sentiment
- `network_health_dashboard`: For network coverage issues
- `standard_agent`: For routine inquiries

### Reddit Scraping
- Scrape T-Mobile-related posts from Reddit
- No API required (web scraping)
- Extract posts, comments, and metadata
- Filter for T-Mobile-related content

## 📝 Model Types

### 1. Sklearn (Recommended for HackUTD)
- Fast training and inference
- Works well with 500-2000 labeled examples
- Good for demo/prototype

### 2. Transformers (Advanced)
- Requires more data (1000+ examples)
- Better accuracy with fine-tuning
- Slower but more accurate

### 3. Rule-based (Fallback)
- No training required
- Works immediately
- Lower accuracy but always available

## 🎯 Use Cases

1. **Real-time Call Routing**
   - Analyze live call transcripts
   - Route to appropriate agent/department
   - Escalate urgent issues

2. **Issue Detection**
   - Flag network problems from customer calls
   - Track trending issues
   - Monitor customer satisfaction

3. **Agent Dashboard**
   - Show sentiment before call transfer
   - Provide context and suggested responses
   - Track customer emotion

4. **Network Health Monitoring**
   - Aggregate issues from calls
   - Create heat maps of problem areas
   - Identify patterns and trends

## 🔍 API vs Web Scraping for Reddit

**Web Scraping (Current Implementation)**
- ✅ No API keys required
- ✅ No rate limits (but be respectful!)
- ✅ Works immediately
- ❌ More fragile (breaks if Reddit changes HTML)
- ❌ Slower for large-scale scraping

**Reddit API (Alternative)**
- ✅ More reliable
- ✅ Better rate limits
- ✅ Official support
- ❌ Requires API keys
- ❌ Rate limits (60 requests/minute)

For HackUTD demo, web scraping is fine. For production, consider using the API.

## 📚 Next Steps

1. **Collect Training Data**
   - Use Reddit scraper to collect posts
   - Label them manually or use weak supervision
   - See DATA_SOURCES.md for more options

2. **Train Your Model**
   - Start with sklearn model (easiest)
   - Use sample data to test
   - Fine-tune on your collected data

3. **Integrate with Dashboard**
   - Connect sentiment analyzer to your dashboard
   - Stream call transcripts in real-time
   - Display routing recommendations

4. **Enhance Features**
   - Add more issue categories
   - Improve emotion detection
   - Add multi-language support

## 🤝 Contributing

This is a HackUTD project. Feel free to:
- Add more data sources
- Improve sentiment analysis
- Enhance routing logic
- Add visualization features

## 📄 License

MIT License - feel free to use for HackUTD!

## 🆘 Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### No Training Data
```bash
cd hackutd-1
python scripts/train_sentiment_model.py --create-sample
```

### Reddit Scraping Fails
- Reddit may have changed their HTML structure
- Try using the JSON endpoint (already implemented)
- Consider using Reddit API as alternative

### Model Training Fails
- Ensure you have labeled data
- Check that `customer_sentiment` field is present
- Minimum 10-20 examples recommended

## 📞 Questions?

Check:
- `DATA_SOURCES.md` for data collection help
- `hackutd_1/scripts/example_usage.py` for code examples
- Script docstrings for API documentation

Good luck with HackUTD! 🚀

