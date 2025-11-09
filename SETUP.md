# Setup Guide: Twilio Voice AI with NeMo + Nemotron

## ✅ What's Already Done
- ✅ All Python dependencies installed (NeMo, Twilio, Flask, etc.)
- ✅ Application code complete
- ✅ NeMo ASR model integration ready
- ✅ Nemotron AI agent configured

## 🚀 Quick Start Guide

### 1. Create Environment File

Copy the example and fill in your credentials:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

**Required credentials:**
- **Twilio Account SID** - Get from https://console.twilio.com
- **Twilio Auth Token** - Get from https://console.twilio.com
- **Twilio Phone Number** - Purchase from Twilio Console
- **OpenRouter API Key** - Get from https://openrouter.ai/keys

### 2. Run the Server

**Option A: Development Mode**
```bash
cd /home/ubuntu/HackUTD-2025
python3 voice.py
```

**Option B: Production Mode (with Gunicorn)**
```bash
cd /home/ubuntu/HackUTD-2025
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 voice:app
```

### 3. Expose Server to Internet

Since Twilio needs a public URL, use one of these:

**Option A: ngrok (Quick Testing)**
```bash
ngrok http 5000
```
Copy the `https://` URL ngrok provides.

**Option B: Production Deployment**
- Deploy to AWS/GCP/Azure with a public IP
- Set up proper SSL/TLS certificates
- Configure firewall rules

### 4. Configure Twilio Webhook

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on your phone number
3. Under "Voice Configuration":
   - **A CALL COMES IN**: Set to your public URL + `/voice`
   - Example: `https://your-server.com/voice` or `https://abc123.ngrok.io/voice`
   - Method: `HTTP POST`
4. Save

## 🧪 Testing

### Test Server Health
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "nemo_model": "loaded",
  "agent_model": "loaded",
  "active_calls": 0
}
```

### Make a Test Call
1. Call your Twilio phone number
2. Follow the voice prompts
3. The system will:
   - Detect your intent using NeMo
   - Process with Nemotron AI agent
   - Execute customer care actions

### View Call Data
```bash
curl http://localhost:5000/call_data/<CALL_SID>
```

## 📋 What This System Does

1. **Receives Phone Call** → Twilio forwards to `/voice` endpoint
2. **Streams Audio** → WebSocket connection to `/media-stream`
3. **Processes Speech** → NeMo detects intent from audio
4. **AI Response** → Nemotron agent generates smart replies
5. **Takes Action** → Executes tools (bill lookup, payments, etc.)

## 🛠️ Available Tools

The agent can:
- 📄 Look up bill information
- 💳 Process payments
- 📊 Write dashboard reports
- 👤 Escalate to human agents

## 🔍 Monitoring

### View Logs
```bash
# Real-time logs
tail -f /var/log/voice_server.log

# Or if running in terminal, logs appear directly
```

### Check Call Records
```bash
# List all active calls
curl http://localhost:5000/health
```

## 🔧 Troubleshooting

### NeMo Model Not Loading
```bash
python3 -c 'import nemo.collections.asr as nemo_asr; print("✅ NeMo works!")'
```

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>
```

### Twilio Connection Issues
- Ensure your server has a **public HTTPS URL**
- Check firewall allows incoming connections on port 5000
- Verify webhook URL in Twilio Console is correct

## 🌐 Production Deployment Checklist

- [ ] Set `debug=False` in Flask app (already done)
- [ ] Use HTTPS (required by Twilio)
- [ ] Set up proper logging
- [ ] Configure environment variables securely
- [ ] Use gunicorn with multiple workers
- [ ] Set up monitoring/alerting
- [ ] Configure database (currently using mock)

## 📞 Example Call Flow

```
1. Customer calls → "Hello! Thank you for calling..."
2. Customer speaks → Audio streams to server
3. NeMo detects → "check_bill" intent
4. Agent queries → Mock database for bill info
5. Agent responds → (via Twilio TTS or your preferred method)
6. Call ends → Data saved for analytics
```

## 🆘 Need Help?

- Twilio Docs: https://www.twilio.com/docs/voice
- NeMo Docs: https://docs.nvidia.com/nemo-framework/
- OpenRouter: https://openrouter.ai/docs

