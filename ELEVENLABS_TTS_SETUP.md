# 🎙️ ElevenLabs TTS Setup Guide

## ✅ What's Been Added

I've integrated **ElevenLabs Text-to-Speech** into `voice_interactive.py` to enable real-time, ultra-realistic voice responses!

---

## 🎯 How It Works Now

```
Call → NeMo transcribes → AI agent processes → ElevenLabs speaks → ✅ Caller hears it!
```

---

## 📦 New Files Added

1. **`tts_handler.py`** - ElevenLabs TTS integration module
2. **`voice_interactive.py`** - Updated to use ElevenLabs TTS
3. **`requirements.txt`** - Added `elevenlabs>=1.0.0`

---

## 🚀 Quick Setup (2 Minutes!)

### **Step 1: Get Your ElevenLabs API Key**

1. Go to https://elevenlabs.io
2. Sign up (free tier available!)
3. Go to https://elevenlabs.io/app/settings/api-keys
4. Click **"Create API Key"**
5. Copy the key

### **Step 2: Install ElevenLabs SDK**

```bash
pip3 install elevenlabs
```

### **Step 3: Add API Key to Environment**

#### **Option A: Add to .env file**

```bash
# Edit your .env file
nano .env
```

Add this line:
```
ELEVENLABS_API_KEY=your_api_key_here
```

#### **Option B: Export as environment variable**

```bash
export ELEVENLABS_API_KEY="your_api_key_here"

# Make it permanent
echo 'export ELEVENLABS_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### **Step 4: Run!**

```bash
python3 voice_interactive.py
```

That's it! 🎉

---

## 🧪 Test ElevenLabs TTS

Quick test to verify it's working:

```bash
cd /home/ubuntu/HackUTD-2025
python3 << 'EOF'
from tts_handler import tts_handler

# Test TTS
text = "Hello! I'm your AI assistant powered by ElevenLabs."
audio = tts_handler.text_to_mulaw_base64(text)

if audio:
    print(f"✅ ElevenLabs TTS Working! Generated {len(audio)} bytes")
else:
    print("❌ TTS Failed - check API key")
EOF
```

---

## 🎤 Voice Options

The handler is configured with **Rachel** (natural, friendly female voice) by default.

### **Popular Voices:**

| Voice ID | Name | Description |
|----------|------|-------------|
| `21m00Tcm4TlvDq8ikWAM` | **Rachel** ⭐ | Natural, friendly (default) |
| `EXAVITQu4vr4xnSDxMaL` | **Bella** | Soft, kind, empathetic |
| `ErXwobaYiN019PkySvjV` | **Antoni** | Well-rounded male |
| `MF3mGyEYCl7XYWbV9V6O` | **Elli** | Expressive, energetic female |
| `TxGEqnHWrfWFTfGW9XjX` | **Josh** | Deep, confident male |

### **Change Voice:**

Edit `tts_handler.py`:

```python
self.voice_id = "EXAVITQu4vr4xnSDxMaL"  # Change to Bella
```

Or browse all voices at: https://elevenlabs.io/app/voice-library

---

## ⚙️ Voice Settings

Current configuration in `tts_handler.py`:

```python
VoiceSettings(
    stability=0.5,          # Lower = more expressive, Higher = more stable
    similarity_boost=0.75,  # How closely to match the original voice
    style=0.0,              # Style exaggeration (0-1)
    use_speaker_boost=True  # Enhanced clarity
)
```

**Tune for your use case:**
- **Customer service:** `stability=0.7, similarity_boost=0.8` (clear, consistent)
- **Conversational:** `stability=0.5, similarity_boost=0.75` (natural, expressive)
- **Dramatic:** `stability=0.3, similarity_boost=0.5` (highly expressive)

---

## 💰 ElevenLabs Pricing

### **Free Tier:**
- 10,000 characters per month
- Access to all standard voices
- Good for testing!

### **Starter Plan ($5/month):**
- 30,000 characters/month
- Commercial license
- All voices including premium

### **Creator Plan ($22/month):**
- 100,000 characters/month
- Voice cloning
- Priority support

**Example Usage:**
- Average AI response: 50 characters
- 1000 calls/month = 50,000 characters
- **Cost:** ~$5-22/month (Starter or Creator plan)

More info: https://elevenlabs.io/pricing

---

## 📊 Comparison: Twilio vs ElevenLabs TTS

| Feature | voice_simple_interactive.py<br>(Twilio TTS) | voice_interactive.py<br>(ElevenLabs TTS) |
|---------|---------------------------|--------------------------------|
| **Voice Quality** | Good | 🌟 **Excellent** (most realistic) |
| **Setup** | ✅ Works now | 2 min setup |
| **Naturalness** | Robotic | 🎯 **Human-like** |
| **Emotion** | Limited | 🎭 **Expressive** |
| **Voices** | Few options | 100+ voices |
| **Cost** | Included | $5-22/mo |
| **Latency** | Low | Low (turbo model) |

---

## 🔧 Technical Details

### **Audio Processing Pipeline:**

```
Text Input
    ↓
ElevenLabs API (eleven_turbo_v2_5 model)
    ↓
PCM audio @ 16kHz
    ↓
Downsample to 8kHz (Twilio requirement)
    ↓
Convert to mulaw format
    ↓
Base64 encode
    ↓
Split into 20ms chunks (160 bytes)
    ↓
Stream to WebSocket
    ↓
Caller hears audio!
```

### **Model Used:**
- **`eleven_turbo_v2_5`** - Optimized for low latency
- Alternative: `eleven_multilingual_v2` (supports 29 languages)

---

## 🐛 Troubleshooting

### **Error: "ELEVENLABS_API_KEY not set"**

```bash
# Check if set
echo $ELEVENLABS_API_KEY

# Set it
export ELEVENLABS_API_KEY="your_key_here"

# Or add to .env
echo 'ELEVENLABS_API_KEY=your_key_here' >> .env
```

### **Error: "Quota exceeded"**

You've used up your free tier. Options:
1. Wait until next month (free tier resets)
2. Upgrade plan at https://elevenlabs.io/pricing

### **Error: "Invalid API key"**

1. Get new key from: https://elevenlabs.io/app/settings/api-keys
2. Make sure there are no spaces or quotes
3. Try: `export ELEVENLABS_API_KEY=sk-...`

### **No audio but no errors?**

```bash
# Test the handler directly
python3 -c "from tts_handler import tts_handler; print(tts_handler.text_to_mulaw_base64('test'))"

# Check logs
python3 voice_interactive.py  # Look for "ElevenLabs TTS Handler initialized"
```

---

## 🎯 Quick Start Commands

```bash
# 1. Install
pip3 install elevenlabs

# 2. Set API key (get from https://elevenlabs.io/app/settings/api-keys)
export ELEVENLABS_API_KEY="your_key_here"

# 3. Run
python3 voice_interactive.py

# 4. Call your Twilio number
# Speak and hear ultra-realistic AI responses!
```

---

## 🌟 Why ElevenLabs?

✅ **Most realistic voices** - Industry-leading quality  
✅ **Fast processing** - Turbo model for low latency  
✅ **Easy setup** - Just an API key  
✅ **Expressive speech** - Conveys emotion naturally  
✅ **100+ voices** - Find the perfect match  
✅ **Multilingual** - Supports 29 languages  
✅ **Commercial license** - Use in production  

---

## 🔗 Useful Links

- **Get API Key:** https://elevenlabs.io/app/settings/api-keys
- **Voice Library:** https://elevenlabs.io/app/voice-library
- **Documentation:** https://elevenlabs.io/docs
- **Pricing:** https://elevenlabs.io/pricing
- **Python SDK:** https://github.com/elevenlabs/elevenlabs-python

---

## ✨ What You Get

**With `voice_interactive.py` + ElevenLabs:**

✅ **Your own NeMo ASR** - Full control over transcription  
✅ **ElevenLabs TTS** - Most realistic voices available  
✅ **Real-time streaming** - Low latency responses  
✅ **Sentiment analysis** - Track emotions live  
✅ **Full customization** - Control every aspect  
✅ **Production ready** - Professional quality  

---

## 🚀 Your Two Options Now:

### **1. `voice_simple_interactive.py`**
- ✅ Works immediately (no extra setup)
- ✅ Uses Twilio's TTS (good quality)
- ✅ Simple and reliable
- ✅ Already working!

### **2. `voice_interactive.py` + ElevenLabs**
- 🌟 Ultra-realistic voices
- 🎯 Your own NeMo ASR
- 🎭 Expressive, natural speech
- ⚡ 2 minutes to set up

---

**Choose based on your needs!**

🎤 **Want the best voice quality?** → Use ElevenLabs  
⚡ **Want simplicity?** → Stick with Twilio TTS  

Both work perfectly! 🚀

