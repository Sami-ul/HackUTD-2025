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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# Load models at startup
logger.info("Loading NeMo model...")
intent_model = NeMoIntentModel()

logger.info("Initializing Nemotron agent...")
agent = NemotronCustomerCareAgent()

# Store for call data
call_data = {}


@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Twilio Voice Server with NeMo + Nemotron Agent is running!"


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and set up media stream."""
    call_sid = request.form.get('CallSid', 'unknown')
    
    print("=" * 50)
    print(f"Incoming call: {call_sid}")
    print(f"From: {request.form.get('From')}")
    print(f"To: {request.form.get('To')}")
    print("=" * 50)
    
    # Initialize call data storage
    call_data[call_sid] = {
        'audio_chunks': [],
        'intent_detected': None,
        'agent_response': None
    }
    
    # Start TwiML response
    resp = VoiceResponse()
    
    # Greet the caller
    resp.say("Hello! Thank you for calling. Please describe how we can help you today.", 
             voice='alice', 
             language='en-US')
    
    # Start bi-directional media stream
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    # End message
    resp.say("Thank you for calling. Goodbye!", voice='alice', language='en-US')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


@sock.route('/media-stream')
def media_stream(ws):
    """Handle WebSocket connection for real-time audio streaming with NeMo + Nemotron."""
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
                # Stream started
                stream_sid = data['streamSid']
                call_sid = data['start']['callSid']
                logger.info(f"Stream started: {stream_sid} for call: {call_sid}")
                
            elif event_type == 'media':
                # Audio data received
                media = data['media']
                audio_payload = media['payload']  # Base64 encoded audio (mulaw)
                
                # Process audio: decode and resample
                processed_audio = audio_processor.process_twilio_audio_chunk(audio_payload)
                
                if processed_audio:
                    audio_processor.accumulate_audio(processed_audio)
                    if call_sid in call_data:
                        call_data[call_sid]['audio_chunks'].append(audio_payload)
                    
                    # Log progress every 100 chunks
                    if len(call_data.get(call_sid, {}).get('audio_chunks', [])) % 100 == 0:
                        logger.info(f"Received {len(call_data[call_sid]['audio_chunks'])} audio chunks")
                    
                    # Process every 64 chunks (approximately 2 seconds of audio)
                    if len(call_data[call_sid]['audio_chunks']) % 64 == 0:
                        process_with_agent(audio_processor, call_sid)
                
            elif event_type == 'stop':
                # Stream stopped - process final audio
                logger.info(f"Stream stopped: {stream_sid}")
                
                accumulated_audio = audio_processor.get_accumulated_audio()
                if len(accumulated_audio) > SAMPLE_RATE:  # At least 1 second
                    process_with_agent_final(accumulated_audio, call_sid)
                
                if call_sid and call_sid in call_data:
                    logger.info(f"Total audio chunks received: {len(call_data[call_sid]['audio_chunks'])}")
                    logger.info(f"Intent detected: {call_data[call_sid]['intent_detected']}")
                    logger.info(f"Agent response: {call_data[call_sid]['agent_response']}")
                
                break
                
        except Exception as e:
            logger.error(f"Error in WebSocket: {str(e)}")
            break
    
    logger.info("WebSocket connection closed")


def process_with_agent(audio_processor, call_sid):
    """Process accumulated audio with NeMo + Nemotron."""
    
    accumulated_audio = audio_processor.get_accumulated_audio()
    
    if len(accumulated_audio) < SAMPLE_RATE:  # Less than 1 second
        return
    
    try:
        # Step 1: Detect intent from audio using NeMo
        raw_intent = intent_model.infer(accumulated_audio)
        
        if not raw_intent:
            logger.warning("Could not detect intent from audio")
            return
        
        parsed_intent = intent_model.parse_intent_output(raw_intent)
        logger.info(f"Detected intent: {parsed_intent}")
        
        call_data[call_sid]['intent_detected'] = parsed_intent
        
        # Step 2: Use Nemotron agent to process and respond
        account_id = parsed_intent.get("slots", {}).get("account_id", "12345")
        intent_name = parsed_intent.get("intent")
        
        agent_result = agent.process_customer_inquiry(
            account_id=account_id,
            intent=intent_name,
            slots=parsed_intent.get("slots", {}),
            transcription="[Customer inquiry detected]"
        )
        
        logger.info(f"Agent result: {agent_result}")
        
        call_data[call_sid]['agent_response'] = agent_result
        
    except Exception as e:
        logger.error(f"Error processing with agent: {e}")


def process_with_agent_final(audio_array, call_sid):
    """Final processing with agent when call ends."""
    
    if len(audio_array) < SAMPLE_RATE:
        return
    
    try:
        # Detect final intent
        raw_intent = intent_model.infer(audio_array)
        
        if not raw_intent:
            logger.warning("Could not detect final intent")
            return
        
        parsed_intent = intent_model.parse_intent_output(raw_intent)
        logger.info(f"Final intent detected: {parsed_intent}")
        
        # Run final agent interaction
        account_id = parsed_intent.get("slots", {}).get("account_id", "12345")
        
        agent_result = agent.process_customer_inquiry(
            account_id=account_id,
            intent=parsed_intent.get("intent"),
            slots=parsed_intent.get("slots", {}),
            transcription="[Final customer inquiry]"
        )
        
        logger.info(f"Final agent result: {agent_result}")
        
        call_data[call_sid]['agent_response'] = agent_result
        
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
        "active_calls": len(call_data)
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", SERVER_PORT))
    logger.info(f"Starting Agentic Customer Care System on {SERVER_HOST}:{port}")
    app.run(host=SERVER_HOST, port=port, debug=False)
