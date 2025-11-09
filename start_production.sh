#!/bin/bash

echo "==================================="
echo "Twilio Voice AI Server (PRODUCTION)"
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

source .env

echo "✓ Environment loaded"
echo "✓ Using ${WORKERS:-2} workers, ${THREADS:-4} threads"
echo ""

# Start with Gunicorn (production-ready)
gunicorn \
    --bind ${SERVER_HOST:-0.0.0.0}:${SERVER_PORT:-5000} \
    --workers ${WORKERS:-2} \
    --threads ${THREADS:-4} \
    --worker-class sync \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    voice:app

