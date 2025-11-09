"""
SIMPLE INTERACTIVE VERSION
Uses Twilio's Gather for two-way conversation
Much simpler than Media Streams - actually responds to the caller!
"""

import os
import logging
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import numpy as np

from config import SERVER_PORT, SERVER_HOST
from nemo_intent_model import NeMoIntentModel
from nemotron_agent import NemotronCustomerCareAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load models at startup
logger.info("Loading NeMo model...")
intent_model = NeMoIntentModel()

logger.info("Initializing Nemotron agent...")
agent = NemotronCustomerCareAgent()

# Store conversation state
conversations = {}


@app.route("/", methods=['GET'])
def home():
    return "Simple Interactive Voice AI - Actually Responds to Caller!"


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming calls with interactive speech recognition"""
    call_sid = request.values.get('CallSid', 'unknown')
    
    logger.info(f"📞 Incoming call: {call_sid}")
    
    # Initialize conversation
    conversations[call_sid] = {
        'turn_count': 0,
        'intents': []
    }
    
    resp = VoiceResponse()
    
    # Ask the caller a question
    gather = Gather(
        input='speech',
        action='/process_speech',
        speech_timeout='auto',
        language='en-US'
    )
    
    gather.say(
        "Hello! I'm your AI assistant. How can I help you today? "
        "You can ask about your bill, make a payment, or get support.",
        voice='alice'
    )
    
    resp.append(gather)
    
    # If caller says nothing, redirect
    resp.redirect('/voice')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route("/process_speech", methods=['POST'])
def process_speech():
    """
    Process caller's speech and respond intelligently
    This is where the AI magic happens!
    """
    call_sid = request.values.get('CallSid', 'unknown')
    speech_result = request.values.get('SpeechResult', '')
    
    logger.info(f"🎤 Caller said: {speech_result}")
    
    # Initialize if not exists
    if call_sid not in conversations:
        conversations[call_sid] = {'turn_count': 0, 'intents': []}
    
    conversations[call_sid]['turn_count'] += 1
    
    resp = VoiceResponse()
    
    if not speech_result:
        resp.say("I didn't catch that. Could you please repeat?", voice='alice')
        resp.redirect('/voice')
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    try:
        # Step 1: Detect intent from text (we don't need NeMo here since Twilio already transcribed!)
        parsed_intent = intent_model.parse_intent_output(speech_result)
        intent_name = parsed_intent['intent']
        
        logger.info(f"🎯 Detected intent: {intent_name}")
        conversations[call_sid]['intents'].append(intent_name)
        
        # Step 2: Use Nemotron AI agent to generate intelligent response
        account_id = "12345"  # In real app, would extract from caller ID
        
        agent_result = agent.process_customer_inquiry(
            account_id=account_id,
            intent=intent_name,
            slots=parsed_intent.get('slots', {}),
            transcription=speech_result
        )
        
        logger.info(f"🤖 Agent response: {agent_result}")
        
        # Step 3: Speak the AI response back to the caller
        if agent_result.get('success'):
            ai_response = agent_result.get('response', 'I understand your request.')
            
            # ✅ CALLER HEARS THIS!
            resp.say(ai_response, voice='alice')
            
            # Ask if they need anything else
            gather = Gather(
                input='speech',
                action='/process_speech',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say("Is there anything else I can help you with?", voice='alice')
            resp.append(gather)
            
            # Option to end call
            resp.say("Thank you for calling. Goodbye!", voice='alice')
            
        else:
            # Error handling
            resp.say(
                "I apologize, I'm having trouble processing that. "
                "Let me transfer you to a human agent.",
                voice='alice'
            )
            # In production, would actually transfer here
            
    except Exception as e:
        logger.error(f"❌ Error processing speech: {e}")
        resp.say(
            "I apologize for the technical difficulty. "
            "Please call back later or press 0 for a human agent.",
            voice='alice'
        )
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route("/status/<call_sid>", methods=['GET'])
def get_status(call_sid):
    """Check conversation status"""
    if call_sid in conversations:
        return {
            'call_sid': call_sid,
            'turn_count': conversations[call_sid]['turn_count'],
            'intents_detected': conversations[call_sid]['intents']
        }
    return {'error': 'Call not found'}, 404


@app.route("/health", methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "mode": "simple_interactive",
        "nemo_model": "loaded",
        "agent_model": "loaded",
        "active_conversations": len(conversations),
        "interactive": "YES - caller gets real responses!"
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", SERVER_PORT))
    logger.info(f"🚀 Starting Simple Interactive Voice AI on {SERVER_HOST}:{port}")
    logger.info("✅ This version ACTUALLY responds to callers!")
    app.run(host=SERVER_HOST, port=port, debug=False)

