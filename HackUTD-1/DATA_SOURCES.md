# Call Transcript Data Sources for Training

## 🎯 Overview
This document outlines where to find call transcript data for training your sentiment analysis models for the T-Mobile Network Health Dashboard.

## 📊 Public Datasets

### 1. **Customer Service Transcripts Datasets**

#### Kaggle Datasets
- **Customer Support on Twitter**: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
  - Contains customer service interactions (though Twitter-based, can be adapted)
  - Format: JSON/CSV
  - Size: ~3M conversations

- **Customer Service Conversations**: https://www.kaggle.com/datasets/eliasdabbas/web-scraping-customer-reviews
  - Customer service chat logs and reviews
  - Good for sentiment analysis training

- **Call Center Data**: Search Kaggle for "call center" or "customer service transcripts"
  - Multiple datasets available
  - Various formats (CSV, JSON, TXT)

#### Hugging Face Datasets
- **Customer Support Dataset**: https://huggingface.co/datasets
  - Search for "customer service", "call transcripts", "sentiment"
  - Many pre-processed datasets available
  - Easy to load with `datasets` library

#### Academic Datasets
- **Ubuntu Dialogue Corpus**: https://github.com/rkadlec/ubuntu-ranking-dataset-creator
  - Technical support conversations
  - Good for training on technical issues

- **Switchboard Corpus**: https://catalog.ldc.upenn.edu/LDC97S62
  - Phone conversation transcripts
  - Requires license but comprehensive

### 2. **Telecom-Specific Datasets**

#### Synthetic Data Generation
Since telecom-specific call transcripts are hard to find publicly, consider:

1. **Generate synthetic transcripts** based on common T-Mobile scenarios:
   - Billing questions
   - Network coverage issues
   - Plan changes
   - Technical support
   - Device issues

2. **Use Reddit/Twitter data** as proxy:
   - Scrape customer complaints from r/tmobile
   - Use Twitter customer service interactions
   - Label them manually or with weak supervision

### 3. **Creating Your Own Dataset**

#### Option 1: Manual Collection
1. **Use T-Mobile's public customer service interactions**:
   - Twitter/X replies
   - Reddit posts and comments
   - App store reviews
   - BBB complaints

2. **Label the data**:
   - Sentiment: positive, negative, neutral, very_positive, very_negative
   - Emotion: angry, frustrated, satisfied, happy, etc.
   - Issue category: network, billing, customer_service, etc.
   - Urgency: low, medium, high

#### Option 2: Web Scraping
1. **Scrape customer service forums**:
   - T-Mobile community forums
   - Reddit r/tmobile
   - Twitter/X mentions
   - Review sites (Trustpilot, Consumer Affairs)

2. **Use the Reddit scraper** we built to collect data

#### Option 3: Simulated Conversations
1. **Create realistic call transcripts**:
   - Use templates based on common issues
   - Vary sentiment and emotion
   - Include both customer and agent responses

## 🔧 Data Format

Your training data should be in this format:

```json
{
  "transcript_id": "call_001",
  "customer_text": "I've been having terrible service in my area...",
  "agent_text": "I understand your frustration. Let me help...",
  "full_transcript": "Customer: ... Agent: ...",
  "duration": 245.5,
  "timestamp": "2024-01-15T10:30:00",
  "issue_category": "network_coverage",
  "resolution_status": "resolved",
  "customer_sentiment": "negative",
  "urgency_level": "high"
}
```

Or as CSV:
```csv
transcript_id,customer_text,agent_text,full_transcript,customer_sentiment,issue_category,urgency_level
call_001,"I'm frustrated with...","I understand...","Customer: ... Agent: ...",negative,network_coverage,high
```

## 📝 Data Collection Strategy for HackUTD

### Quick Start (For Demo)
1. **Use Reddit data** (already have scraper):
   - Scrape r/tmobile posts
   - Treat post titles + text as "customer_text"
   - Manually label or use weak supervision for sentiment

2. **Use pre-trained models**:
   - Start with Hugging Face sentiment models
   - Fine-tune on small labeled dataset
   - Use transfer learning

3. **Synthetic data**:
   - Create 50-100 realistic call transcripts
   - Label them manually
   - Use for fine-tuning

### Production Approach
1. **Partner with T-Mobile** (if possible):
   - Get anonymized call transcripts
   - Use their existing labels
   - Follow data privacy regulations

2. **Build data collection pipeline**:
   - Real-time collection from customer service channels
   - Automatic labeling where possible
   - Human review for edge cases

## 🎓 Training Data Requirements

### Minimum Dataset Size
- **Rule-based/Simple ML**: 100-500 labeled examples
- **Sklearn models**: 500-2000 labeled examples
- **Transformer fine-tuning**: 1000-5000 labeled examples
- **Production quality**: 10,000+ labeled examples

### Label Distribution
Aim for balanced labels:
- Positive: 20-30%
- Neutral: 30-40%
- Negative: 20-30%
- Very Negative: 10-20%

### Data Quality
- **Clean transcripts**: Remove filler words, normalize text
- **Accurate labels**: Human-reviewed labels preferred
- **Diverse scenarios**: Cover all issue categories
- **Realistic language**: Use actual customer language patterns

## 🚀 Quick Data Collection Script

See `scripts/collect_training_data.py` for a script that:
1. Scrapes Reddit for T-Mobile posts
2. Extracts customer complaints/questions
3. Formats them as call transcripts
4. Provides labeling interface

## 📚 Additional Resources

- **Sentiment Analysis Datasets**: https://github.com/clairett/pytorch-sentiment-classification
- **Customer Service Datasets**: https://github.com/topics/customer-service-dataset
- **NLP Datasets**: https://github.com/niderhoff/nlp-datasets

## ⚠️ Important Notes

1. **Privacy**: Never use real customer data without proper anonymization
2. **Bias**: Be aware of bias in training data
3. **Domain Adaptation**: Models trained on general data may need fine-tuning for telecom domain
4. **Continuous Learning**: Plan to retrain models as you collect more data


