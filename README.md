# 🎯 Agentic Customer Care System
**AI-Powered Voice Customer Service with NeMo ASR + Nemotron Agent**

## 🚀 Quick Start (3 Steps)

### 1️⃣ Configure Credentials
```bash
cp .env.example .env
nano .env  # Add your API keys
```

### 2️⃣ Start Server
```bash
./start_server.sh
```

### 3️⃣ Configure Twilio
- Point webhook to: `https://your-url.com/voice`
- Call your Twilio number!

---

## 📦 What's Included

- ✅ **NeMo ASR** - NVIDIA's speech recognition for intent detection
- ✅ **Nemotron Agent** - NVIDIA's LLM for intelligent responses  
- ✅ **Twilio Integration** - Real-time audio streaming
- ✅ **Customer Tools** - Bill lookup, payments, escalation
- ✅ **Production Ready** - Gunicorn + proper error handling

---

## 📖 Documentation

- **[SETUP.md](SETUP.md)** - Complete setup guide
- **[.env.example](.env.example)** - Configuration template

---

## 🛠️ Commands

```bash
# Development
./start_server.sh

# Production
./start_production.sh

# Test NeMo
python3 -c 'import nemo.collections.asr as nemo_asr; print("✅ Works!")'

# Health Check
curl http://localhost:5000/health
```

---

## 🏗️ Architecture

```
Phone Call → Twilio → WebSocket → Your Server
                                      ↓
                          Audio → NeMo (Intent Detection)
                                      ↓
                          Intent → Nemotron Agent (Smart Response)
                                      ↓
                          Tools → Database/Actions
```

---

## 🎯 Features

### Voice AI Pipeline
1. **Real-time audio streaming** via Twilio WebSocket
2. **Intent detection** with NeMo ASR models
3. **AI agent reasoning** with Nemotron
4. **Tool execution** for customer actions

### Customer Care Tools
- 📄 `get_bill_info` - Check account balance
- 💳 `make_payment` - Process payments  
- 📊 `write_dashboard_report` - Log interactions
- 👤 `escalate_to_human` - Transfer to agent

---

## 🔐 Required API Keys

1. **Twilio** - [console.twilio.com](https://console.twilio.com)
   - Account SID
   - Auth Token
   - Phone Number

2. **OpenRouter** - [openrouter.ai](https://openrouter.ai)
   - API Key (for Nemotron model)

---

## 📂 Project Structure

```
HackUTD-2025/
├── voice.py              # Main Flask app + Twilio handlers
├── nemo_intent_model.py  # NeMo ASR wrapper
├── nemotron_agent.py     # Nemotron AI agent
├── audio_processor.py    # Audio format conversion
├── tools.py              # Function definitions
├── mock_database.py      # Mock customer data
├── config.py             # Configuration loader
├── requirements.txt      # Python dependencies
├── .env                  # Your secrets (create this!)
├── start_server.sh       # Development launcher
└── start_production.sh   # Production launcher
```

---

## 🧪 Testing

### 1. Verify Installation
```bash
python3 -c 'import nemo.collections.asr as nemo_asr; print("✅ NeMo OK")'
```

### 2. Check Server Health
```bash
curl http://localhost:5000/health
```

### 3. Make Test Call
Call your Twilio number and say: *"What's my bill?"*

---

## 🌐 Deployment

### Quick (ngrok)
```bash
ngrok http 5000
# Use the https URL in Twilio webhook
```

### Production (Cloud)
- Deploy to AWS/GCP/Azure
- Use HTTPS with valid certificate
- Configure DNS and firewall
- Update Twilio webhook to your domain

---

## 📞 Call Flow Example

```
Customer: "What's my balance?"
   ↓
[NeMo detects: check_bill intent]
   ↓
[Nemotron agent calls get_bill_info()]
   ↓
Agent: "Your current balance is $125.50, due on Nov 15th"
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -i :5000
kill -9 <PID>
```

### NeMo Import Error
Check dependencies are installed:
```bash
pip3 list | grep nemo
```

### Twilio Not Connecting
- Verify webhook URL is **public HTTPS**
- Check server logs for errors
- Test with Twilio Console's "Test" button

---

## 📊 Monitoring

### View Active Calls
```bash
curl http://localhost:5000/health
```

### Get Call Details
```bash
curl http://localhost:5000/call_data/<CALL_SID>
```

---

## 🎓 HackUTD 2025

Built for HackUTD 2025 hackathon.

**Tech Stack:**
- NVIDIA NeMo (ASR)
- NVIDIA Nemotron (LLM)
- Twilio (Voice)
- Flask + WebSockets
- Python 3.10+

---

## 📝 License

MIT License - Feel free to use for your projects!

---

## 🤝 Contributing

Found a bug? Have an idea? Open an issue or PR!

---

## 🔗 Links

- [NeMo Docs](https://docs.nvidia.com/nemo-framework/)
- [Twilio Voice Docs](https://www.twilio.com/docs/voice)
- [OpenRouter](https://openrouter.ai)

---

**Ready to deploy?** See [SETUP.md](SETUP.md) for detailed instructions!

