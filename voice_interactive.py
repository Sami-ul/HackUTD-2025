"""
ENHANCED VERSION: Interactive Two-Way Voice Conversation
This version RESPONDS to the caller in real-time
"""

import os
import json
import base64
import logging
from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import numpy as np

from config import SERVER_PORT, SERVER_HOST, SAMPLE_RATE, TWILIO_SAMPLE_RATE
from audio_processor import TwilioAudioProcessor
from nemo_intent_model import NeMoIntentModel
from nemotron_agent import NemotronCustomerCareAgent
from tts_handler import tts_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# Load models
logger.info("Loading NeMo model...")
intent_model = NeMoIntentModel()

logger.info("Initializing Nemotron agent...")
agent = NemotronCustomerCareAgent()

logger.info("ElevenLabs TTS ready...")

call_data = {}


@app.route("/", methods=['GET'])
def home():
    return "Twilio Interactive Voice Server - NeMo + Nemotron"


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and set up BIDIRECTIONAL media stream."""
    call_sid = request.form.get('CallSid', 'unknown')
    
    logger.info(f"Incoming call: {call_sid}")
    
    call_data[call_sid] = {
        'audio_chunks': [],
        'intent_detected': None,
        'agent_response': None
    }
    
    resp = VoiceResponse()
    
    # IMPORTANT: For two-way audio, we need bidirectional stream
    resp.say("Hello! I'm your AI assistant. How can I help you today?", 
             voice='alice', language='en-US')
    
    # Start BIDIRECTIONAL stream
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


@sock.route('/media-stream')
def media_stream(ws):
    """
    Handle WebSocket for BIDIRECTIONAL audio streaming
    - Receives caller's audio
    - Sends back AI responses
    """
    call_sid = None
    stream_sid = None
    audio_processor = TwilioAudioProcessor(
        twilio_sample_rate=TWILIO_SAMPLE_RATE,
        target_sample_rate=SAMPLE_RATE
    )
    
    logger.info("WebSocket connection established")
    
    while True:
        try:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type == 'start':
                stream_sid = data['streamSid']
                call_sid = data['start']['callSid']
                logger.info(f"Stream started: {stream_sid} for call: {call_sid}")
                
            elif event_type == 'media':
                # Receive caller's audio
                media = data['media']
                audio_payload = media['payload']
                
                processed_audio = audio_processor.process_twilio_audio_chunk(audio_payload)
                
                if processed_audio:
                    audio_processor.accumulate_audio(processed_audio)
                    if call_sid in call_data:
                        call_data[call_sid]['audio_chunks'].append(audio_payload)
                    
                    # Process every 64 chunks (~2 seconds)
                    if len(call_data.get(call_sid, {}).get('audio_chunks', [])) % 64 == 0:
                        response_text = process_with_agent_realtime(
                            audio_processor, call_sid, ws, stream_sid
                        )
                        
                        # SEND RESPONSE BACK TO CALLER
                        if response_text:
                            send_tts_to_caller(ws, stream_sid, response_text)
                
            elif event_type == 'stop':
                logger.info(f"Stream stopped: {stream_sid}")
                
                # Final processing
                accumulated_audio = audio_processor.get_accumulated_audio()
                if len(accumulated_audio) > SAMPLE_RATE:
                    process_with_agent_final(accumulated_audio, call_sid, ws, stream_sid)
                
                break
                
        except Exception as e:
            logger.error(f"Error in WebSocket: {str(e)}")
            break
    
    logger.info("WebSocket connection closed")


def process_with_agent_realtime(audio_processor, call_sid, ws, stream_sid):
    """Process audio and return response text for TTS"""
    
    accumulated_audio = audio_processor.get_accumulated_audio()
    
    if len(accumulated_audio) < SAMPLE_RATE:
        return None
    
    try:
        # Step 1: Transcribe
        transcription = intent_model.infer(accumulated_audio)
        
        if not transcription:
            return None
        
        # Step 2: Get intent
        parsed_intent = intent_model.parse_intent_output(transcription)
        logger.info(f"Transcription: {transcription}")
        logger.info(f"Intent: {parsed_intent['intent']}")
        
        call_data[call_sid]['intent_detected'] = parsed_intent
        
        # Step 3: Get AI response
        account_id = "12345"  # Could extract from transcription
        
        agent_result = agent.process_customer_inquiry(
            account_id=account_id,
            intent=parsed_intent.get("intent"),
            slots=parsed_intent.get("slots", {}),
            transcription=transcription
        )
        
        logger.info(f"Agent response: {agent_result}")
        call_data[call_sid]['agent_response'] = agent_result
        
        # Return the response text to send back to caller
        if agent_result.get('success'):
            return agent_result.get('response', 'I understand. Let me help you with that.')
        
    except Exception as e:
        logger.error(f"Error processing: {e}")
    
    return None


def send_tts_to_caller(ws, stream_sid, text):
    """
    Send text-to-speech response back to the caller via WebSocket
    
    Uses ElevenLabs TTS to convert text to speech, then sends via Twilio Media Streams
    """
    
    logger.info(f"🔊 Sending TTS to caller: {text}")
    
    try:
        # Convert text to audio chunks using ElevenLabs TTS
        audio_chunks = tts_handler.text_to_twilio_chunks(text)
        
        if not audio_chunks:
            logger.error("Failed to generate TTS audio")
            return
        
        # Send each chunk to Twilio via WebSocket
        for chunk in audio_chunks:
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": chunk
                }
            }
            ws.send(json.dumps(media_message))
        
        logger.info(f"✅ Sent {len(audio_chunks)} audio chunks to caller")
        
    except Exception as e:
        logger.error(f"Error sending TTS: {e}")


def process_with_agent_final(audio_array, call_sid, ws, stream_sid):
    """Final processing when call ends"""
    
    if len(audio_array) < SAMPLE_RATE:
        return
    
    try:
        transcription = intent_model.infer(audio_array)
        
        if transcription:
            parsed_intent = intent_model.parse_intent_output(transcription)
            logger.info(f"Final transcription: {transcription}")
            
            agent_result = agent.process_customer_inquiry(
                account_id="12345",
                intent=parsed_intent.get("intent"),
                slots=parsed_intent.get("slots", {}),
                transcription=transcription
            )
            
            logger.info(f"Final agent result: {agent_result}")
            
    except Exception as e:
        logger.error(f"Error in final processing: {e}")


@app.route("/call_data/<call_sid>", methods=['GET'])
def get_call_data(call_sid):
    """API endpoint to retrieve call data."""
    if call_sid in call_data:
        return {
            'call_sid': call_sid,
            'total_chunks': len(call_data[call_sid]['audio_chunks']),
            'intent_detected': call_data[call_sid]['intent_detected'],
            'agent_response': call_data[call_sid]['agent_response']
        }
    return {'error': 'Call not found'}, 404


@app.route("/health", methods=['GET'])
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "nemo_model": "loaded",
        "agent_model": "loaded",
        "active_calls": len(call_data),
        "interactive": "partial - needs TTS integration"
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", SERVER_PORT))
    logger.info(f"Starting Interactive Customer Care System on {SERVER_HOST}:{port}")
    logger.info("⚠️  NOTE: Real-time responses require TTS integration!")
    app.run(host=SERVER_HOST, port=port, debug=False)

