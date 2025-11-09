#!/bin/bash

echo "==================================="
echo "Twilio Voice AI Server"
echo "NeMo + Nemotron Customer Care"
echo "==================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Edit with your API keys"
    echo ""
    exit 1
fi

# Check required environment variables
source .env

if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your_openrouter_api_key_here" ]; then
    echo "⚠️  WARNING: OPENROUTER_API_KEY not set properly in .env"
fi

if [ -z "$TWILIO_ACCOUNT_SID" ] || [ "$TWILIO_ACCOUNT_SID" = "your_twilio_account_sid_here" ]; then
    echo "⚠️  WARNING: TWILIO credentials not set properly in .env"
fi

echo "✓ Environment loaded"
echo ""

# Run health check
echo "Testing NeMo import..."
python3 -c 'import nemo.collections.asr as nemo_asr; print("✅ NeMo ready!")' 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ NeMo import failed! Please check installation."
    exit 1
fi

echo ""
echo "Starting server..."
echo "Server will be available at: http://0.0.0.0:${SERVER_PORT:-5000}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the server
python3 voice.py

