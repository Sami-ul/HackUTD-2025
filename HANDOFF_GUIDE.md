# Human Handoff Feature Guide

## Overview
Your Twilio voice app now supports transferring calls from AI to human agents when needed.

## Setup

### 1. Set Environment Variables in Render
Go to your Render dashboard and add these environment variables:

- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token  
- `HUMAN_AGENT_PHONE`: Phone number to transfer to (e.g., `+17202990300`)

### 2. Choose Your Endpoint

#### Option A: Voice Menu (Simple)
Use `/voice-with-handoff` endpoint in Twilio
- Caller presses 0 for human
- Caller presses 1 for AI

**Twilio Webhook URL:** `https://hackutd-2025.onrender.com/voice-with-handoff`

#### Option B: WebSocket with Smart Handoff (Advanced)
Keep using `/voice` endpoint
- AI analyzes sentiment in real-time
- Automatically offers handoff when needed
- Call API to trigger transfer

**Twilio Webhook URL:** `https://hackutd-2025.onrender.com/voice`

## API Endpoints

### Check if Handoff is Needed
```bash
POST /check-handoff-needed
Content-Type: application/json

{
  "call_sid": "CA...",
  "transcription": "I want to speak to a person",
  "sentiment": "negative",
  "confidence": 0.3
}

Response:
{
  "handoff_needed": true,
  "reason": "Customer requested human agent",
  "call_sid": "CA..."
}
```

### Transfer Call to Human
```bash
POST /transfer-to-human
Content-Type: application/json

{
  "call_sid": "CA...",
  "from_number": "+17202990300"
}

Response:
{
  "success": true,
  "message": "Transfer initiated",
  "twiml": "<?xml version=..."
}
```

### Get Sentiment Data
```bash
GET /sentiment/<call_sid>

Response:
{
  "call_sid": "CA...",
  "total_chunks": 450,
  "sentiment_data": [...]
}
```

## Handoff Triggers

The system automatically detects when handoff is needed based on:

1. **Keywords:** "human", "agent", "person", "representative", "supervisor"
2. **Negative Sentiment:** Very negative or low confidence sentiment
3. **Negative Language:** "angry", "frustrated", "upset", "mad", "terrible"

## Integration Example

```python
# In your sentiment analysis function
def analyze_sentiment(transcription, audio):
    # Your sentiment analysis logic
    sentiment = get_sentiment(transcription)
    
    # Check if handoff needed
    response = requests.post('https://hackutd-2025.onrender.com/check-handoff-needed', json={
        'call_sid': call_sid,
        'transcription': transcription,
        'sentiment': sentiment,
        'confidence': 0.8
    })
    
    if response.json()['handoff_needed']:
        # Trigger transfer
        transfer_response = requests.post('https://hackutd-2025.onrender.com/transfer-to-human', json={
            'call_sid': call_sid,
            'from_number': caller_number
        })
```

## Testing

1. Call your Twilio number
2. Say "I want to speak to a human"
3. System should detect and offer transfer
4. Or press 0 if using voice menu

## Notes

- Human agent phone must be verified in Twilio trial accounts
- Transfers timeout after 30 seconds if agent doesn't answer
- Agent sees caller's number on their phone
