import os
from dotenv import load_dotenv

load_dotenv()

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# OpenRouter API
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Server
SERVER_PORT = int(os.getenv("SERVER_PORT", 5000))
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")

# NeMo
NEMO_MODEL_NAME = os.getenv("NEMO_MODEL_NAME", "slu_conformer_transformer_large_slurp")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", 16000))
TWILIO_SAMPLE_RATE = int(os.getenv("TWILIO_SAMPLE_RATE", 8000))