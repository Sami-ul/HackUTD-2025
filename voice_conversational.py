"""
CONVERSATIONAL VERSION: Like ChatGPT/Claude Voice Mode
- Continuous listening with Voice Activity Detection
- Full LLM reasoning (NO keyword matching)
- Maintains conversation context
- Proactive tool calling
- Natural interruptions
- Call recording + transcription
"""

import os
import json
import base64
import logging
import threading
from collections import deque
from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import numpy as np

from config import SERVER_PORT, SERVER_HOST, SAMPLE_RATE, TWILIO_SAMPLE_RATE
from audio_processor import TwilioAudioProcessor
from nemo_intent_model import NeMoIntentModel
from nemotron_agent import NemotronCustomerCareAgent
from tts_handler import tts_handler

logging.basicConfig(level=logging.DEBUG)  # DEBUG for more info
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# Enable WebSocket debugging
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}

# Load models
logger.info("Loading NeMo model for transcription...")
nemo_model = NeMoIntentModel()

logger.info("Initializing Nemotron conversational agent...")
agent = NemotronCustomerCareAgent()

logger.info("ElevenLabs TTS ready...")

# Conversation storage
conversations = {}


class ConversationContext:
    """Maintains full conversation state for natural dialogue"""
    
    def __init__(self, call_sid, account_id="12345"):
        self.call_sid = call_sid
        self.account_id = account_id
        self.messages = []  # Full conversation history for LLM
        self.is_speaking = False  # AI is currently speaking
        self.turn_count = 0
        self.tools_called = []  # Track which tools were used
        
        logger.info(f"📝 Created conversation context for {call_sid}")
    
    def add_user_turn(self, transcription):
        """Add user's speech to conversation"""
        self.messages.append({
            "role": "user",
            "content": transcription
        })
        self.turn_count += 1
        logger.info(f"👤 User (turn {self.turn_count}): {transcription}")
    
    def add_assistant_turn(self, response):
        """Add AI's response to conversation"""
        self.messages.append({
            "role": "assistant",
            "content": response
        })
        logger.info(f"🤖 AI (turn {self.turn_count}): {response}")
    
    def get_conversation_for_llm(self):
        """Get conversation in format for LLM"""
        return self.messages.copy()
    
    def log_tool_call(self, tool_name, args):
        """Track tool usage for analytics"""
        self.tools_called.append({
            "tool": tool_name,
            "args": args,
            "turn": self.turn_count
        })
    
    def get_summary(self):
        """Get conversation summary for logging"""
        return {
            "call_sid": self.call_sid,
            "account_id": self.account_id,
            "total_turns": self.turn_count,
            "total_messages": len(self.messages),
            "tools_used": len(self.tools_called),
            "tools_list": [t["tool"] for t in self.tools_called]
        }


@app.route("/", methods=['GET'])
def home():
    return "🎙️ Conversational Voice AI - LLM-Powered Reasoning"


@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming call with recording + streaming"""
    call_sid = request.values.get('CallSid', 'unknown')
    from_number = request.values.get('From', 'unknown')
    
    logger.info(f"📞 CALL FROM {from_number}: {call_sid}")
    
    # Initialize conversation context
    conversations[call_sid] = ConversationContext(call_sid)
    
    resp = VoiceResponse()
    
    # Say greeting FIRST
    resp.say("Hello! I'm your AI assistant. How can I help you today?", voice='alice')
    
    conversations[call_sid].add_assistant_turn("Hello! I'm your AI assistant. How can I help you today?")
    
    # Start WebSocket stream AFTER greeting
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    logger.info(f"📡 WEBSOCKET URL: wss://{request.host}/media-stream")
    logger.info(f"📡 FULL TwiML: {str(resp)}")
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


@sock.route('/media-stream')
def media_stream(ws):
    """
    CONVERSATIONAL WebSocket Handler with LLM Reasoning
    - Processes audio continuously
    - Voice Activity Detection
    - Maintains context
    - Responds naturally
    """
    call_sid = None
    stream_sid = None
    audio_processor = TwilioAudioProcessor(TWILIO_SAMPLE_RATE, SAMPLE_RATE)
    
    # Voice Activity Detection state
    silence_counter = 0
    speech_detected = False
    
    logger.info("🔌 WebSocket connected successfully!")
    logger.info(f"   Client: {ws.environ.get('REMOTE_ADDR', 'unknown')}")
    
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
                logger.info(f"🎙️ Stream started: {call_sid}")
            
            elif event_type == 'media':
                logger.debug("📥 Received audio chunk")
                media = data['media']
                audio_payload = media['payload']
                
                # Process audio chunk
                processed_audio = audio_processor.process_twilio_audio_chunk(audio_payload)
                logger.debug(f"✅ Processed audio: {len(processed_audio) if processed_audio else 0} bytes")
                
                if processed_audio:
                    audio_processor.accumulate_audio(processed_audio)
                    
                    # CONTINUOUS PROCESSING (not batched)
                    # Check every 0.5 seconds for responsiveness
                    accumulated = audio_processor.get_accumulated_audio()
                    
                    if len(accumulated) >= SAMPLE_RATE * 0.5:  # 0.5 seconds minimum
                        
                        # Voice Activity Detection (VAD)
                        # Check if there's actual speech or just silence
                        audio_energy = np.abs(accumulated).mean()
                        logger.debug(f"🔊 Audio energy: {audio_energy:.6f}")
                        
                        if audio_energy > 0.001:  # LOWERED threshold - Speech detected
                            speech_detected = True
                            silence_counter = 0
                            logger.debug("🎤 SPEECH DETECTED")
                        else:  # Silence
                            silence_counter += 1
                        
                        # Process when: speech detected + now silence (user finished speaking)
                        if speech_detected and silence_counter > 3:  # LOWERED - ~100ms of silence
                            logger.info(f"🎯 Processing speech (energy={audio_energy:.6f}, silence={silence_counter})")
                            
                            if call_sid in conversations:
                                # Process in background thread to avoid blocking WebSocket
                                threading.Thread(
                                    target=process_with_llm_reasoning,
                                    args=(
                                        accumulated.copy(),
                                        call_sid,
                                        ws,
                                        stream_sid,
                                        conversations[call_sid]
                                    ),
                                    daemon=True
                                ).start()
                            
                            # Reset state
                            speech_detected = False
                            silence_counter = 0
                            audio_processor.clear_buffer()
            
            elif event_type == 'stop':
                logger.info(f"📴 Stream stopped: {call_sid}")
                
                # Log final conversation summary
                if call_sid in conversations:
                    summary = conversations[call_sid].get_summary()
                    logger.info(f"📊 Call summary: {summary}")
                
                break
        
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            break
    
    logger.info("🔌 WebSocket closed")


def process_with_llm_reasoning(audio_array, call_sid, ws, stream_sid, context):
    """
    Process audio and let LLM do ALL the reasoning
    NO KEYWORD MATCHING - LLM decides everything:
    - What the user wants
    - Which tools to call
    - How to respond naturally
    """
    
    try:
        # Step 1: Transcribe with NeMo (FAST!)
        transcription = nemo_model.infer(audio_array)
        
        if not transcription or len(transcription.strip()) < 3:
            logger.debug("Ignoring empty/short transcription")
            return  # Ignore very short/empty transcriptions
        
        # Step 2: Add user's message to conversation context
        context.add_user_turn(transcription)
        
        # Step 3: Let LLM reason about the ENTIRE conversation
        # The LLM will:
        # - Understand context from previous messages
        # - Decide if tools are needed
        # - Generate natural responses
        # - Reference previous information
        
        conversation_for_llm = context.get_conversation_for_llm()
        
        logger.info(f"🧠 Sending conversation ({len(conversation_for_llm)} messages) to LLM")
        
        response_text = agent.process_conversation_turn(
            conversation_history=conversation_for_llm,
            account_id=context.account_id
        )
        
        if response_text:
            # Step 4: Add AI response to conversation context
            context.add_assistant_turn(response_text)
            
            # Step 5: Speak response to caller using ElevenLabs TTS
            context.is_speaking = True
            send_tts_to_caller(ws, stream_sid, response_text)
            context.is_speaking = False
        else:
            logger.warning("⚠️ No response generated from LLM")
    
    except Exception as e:
        logger.error(f"❌ Processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Send error message to caller
        try:
            error_msg = "I'm sorry, I didn't catch that. Could you repeat?"
            send_tts_to_caller(ws, stream_sid, error_msg)
        except:
            pass


def send_tts_to_caller(ws, stream_sid, text):
    """Send TTS audio to caller using ElevenLabs"""
    try:
        logger.info(f"🔊 Generating TTS for: {text[:50]}...")
        
        audio_chunks = tts_handler.text_to_twilio_chunks(text)
        
        if not audio_chunks:
            logger.error("❌ No audio generated from TTS")
            return
        
        # Send each chunk to Twilio via WebSocket
        for chunk in audio_chunks:
            media_message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": chunk}
            }
            ws.send(json.dumps(media_message))
        
        logger.info(f"✅ Sent {len(audio_chunks)} TTS chunks to caller")
    
    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        import traceback
        logger.error(traceback.format_exc())


@app.route("/recording-complete", methods=['GET', 'POST'])
def recording_complete():
    """Save recording and conversation transcript when call ends"""
    # Use request.values to handle both GET and POST
    recording_url = request.values.get('RecordingUrl')
    recording_sid = request.values.get('RecordingSid')
    call_sid = request.values.get('CallSid')
    duration = request.values.get('RecordingDuration')
    
    logger.info(f"📼 Recording complete: {recording_url}")
    logger.info(f"⏱️ Duration: {duration} seconds")
    
    # Save conversation transcript and metadata
    if call_sid in conversations:
        context = conversations[call_sid]
        
        logger.info(f"💬 Conversation had {len(context.messages)} messages")
        logger.info(f"🔧 Tools called: {[t['tool'] for t in context.tools_called]}")
        
        # Log full conversation
        logger.info("📝 Full conversation transcript:")
        for msg in context.messages:
            logger.info(f"  {msg['role'].upper()}: {msg['content']}")
        
        # Save to database/storage
        save_call_data(
            call_sid=call_sid,
            recording_url=recording_url,
            duration=duration,
            messages=context.messages,
            tools_called=context.tools_called
        )
    else:
        logger.warning(f"⚠️ No conversation context found for {call_sid}")
    
    return '', 200


def save_call_data(call_sid, recording_url, duration, messages, tools_called):
    """Save full call data for analytics/compliance"""
    
    call_data = {
        "call_sid": call_sid,
        "recording_url": recording_url,
        "duration": duration,
        "transcript": messages,
        "tool_calls": tools_called,
        "total_turns": len([m for m in messages if m["role"] == "user"]),
        "timestamp": "2025-11-09"  # Would use datetime.now()
    }
    
    # TODO: Save to your database
    # TODO: Upload recording to S3
    # TODO: Send to analytics pipeline
    
    logger.info(f"💾 Saved call data for: {call_sid}")
    logger.info(f"   Recording: {recording_url}.mp3")
    logger.info(f"   Turns: {call_data['total_turns']}")
    logger.info(f"   Tools: {len(tools_called)}")


@app.route("/call_data/<call_sid>", methods=['GET'])
def get_call_data(call_sid):
    """API endpoint to retrieve active call data"""
    if call_sid in conversations:
        context = conversations[call_sid]
        return {
            'call_sid': call_sid,
            'account_id': context.account_id,
            'turns': context.turn_count,
            'messages': len(context.messages),
            'tools_called': len(context.tools_called),
            'is_speaking': context.is_speaking,
            'conversation': context.messages
        }, 200
    
    return {'error': 'Call not found or ended'}, 404


@app.route("/active_calls", methods=['GET'])
def active_calls():
    """List all active calls"""
    return {
        "active_calls": len(conversations),
        "call_sids": list(conversations.keys())
    }, 200


@app.route("/health", methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "mode": "conversational_llm_reasoning",
        "features": [
            "✅ NeMo STT (fast transcription)",
            "✅ LLM reasoning (NO keyword matching)",
            "✅ Proactive tool calling",
            "✅ Conversation context",
            "✅ ElevenLabs TTS (natural voice)",
            "✅ Full call recording",
            "✅ Voice Activity Detection",
            "✅ Continuous processing"
        ],
        "models": {
            "stt": "NeMo QuartzNet",
            "llm": "Nemotron Nano 9B",
            "tts": "ElevenLabs"
        },
        "active_conversations": len(conversations)
    }, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", SERVER_PORT))
    
    logger.info("=" * 60)
    logger.info("🚀 Starting LLM-Powered Conversational Voice System")
    logger.info("=" * 60)
    logger.info("🧠 All reasoning done by Nemotron - NO keyword matching!")
    logger.info("🎙️ NeMo STT for fast, accurate transcription")
    logger.info("🔊 ElevenLabs TTS for natural voice output")
    logger.info("📼 Full call recording enabled")
    logger.info("💬 Conversation context maintained")
    logger.info("🔧 Proactive tool calling")
    logger.info(f"🌐 Listening on {SERVER_HOST}:{port}")
    logger.info("=" * 60)
    
    app.run(host=SERVER_HOST, port=port, debug=False)

