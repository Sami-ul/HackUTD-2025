import os
import json
import base64
from flask import Flask, request, jsonify
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Dial
from twilio.rest import Client
import google.generativeai as genai
from datetime import datetime
from deepgram import DeepgramClient
import audioop
import threading
import websocket as ws_client
import ssl

app = Flask(__name__)
sock = Sock(app)

# API Keys and Config
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDpJ5bEKUQWnoIOYuUb0lAKl2HcDhfzYDg')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'AC9056fdc891fed16a55a128f9d14c8bba')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '05c5255761a3e713c44447a532d574ba')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY', 'aa55f81e6d4b0de0d7166cb8226c1d5f8301b92a')
HUMAN_AGENT_PHONE = os.environ.get('HUMAN_AGENT_PHONE', '+17202990300')

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Deepgram
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

# Store for call data and conversation history
call_data = {}
conversation_history = {}

@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Twilio Voice Server with WebSocket streaming is running!"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and set up media stream with AI conversation."""
    call_sid = request.form.get('CallSid', 'unknown')
    from_number = request.form.get('From', '')
    
    print("=" * 50)
    print(f"Incoming call: {call_sid}")
    print(f"From: {from_number}")
    print(f"Time: {datetime.now()}")
    print("=" * 50)
    
    # Initialize conversation history for this call
    conversation_history[call_sid] = []
    
    # Initialize call data storage
    call_data[call_sid] = {
        'audio_chunks': [],
        'transcriptions': [],
        'is_speaking': False,  # Track if AI is currently speaking
        'interrupt_requested': False,  # Track if user interrupted
        'from_number': from_number
    }
    
    # Start TwiML response
    resp = VoiceResponse()
    
    # Brief greeting
    resp.say("Hello! I'm your AI assistant. How can I help you today?", 
             voice='Polly.Joanna',  # More natural voice
             language='en-US')
    
    # Start bi-directional media stream for real-time conversation
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

@sock.route('/media-stream')
def media_stream(ws):
    """Handle WebSocket connection for real-time conversational AI with Deepgram."""
    call_sid = None
    stream_sid = None
    transcript_buffer = ""
    
    print("WebSocket connection established")
    
    # Initialize Deepgram live transcription
    dg_connection = None
    
    try:
        dg_connection = deepgram.listen.websocket.v("1")
        
        def on_open(self, open, **kwargs):
            print("✅ Deepgram connection opened")
        
        def on_message(self, result, **kwargs):
            nonlocal transcript_buffer
            
            sentence = result.channel.alternatives[0].transcript
            
            if len(sentence) > 0:
                print(f"🎤 Deepgram transcript: {sentence}")
                transcript_buffer += sentence + " "
                
                # If this is a final transcript, process it
                if result.is_final:
                    process_user_input(call_sid, transcript_buffer.strip())
                    transcript_buffer = ""
        
        def on_error(self, error, **kwargs):
            print(f"❌ Deepgram error: {error}")
        
        def on_close(self, close, **kwargs):
            print("🔒 Deepgram connection closed")
        
        # Register event handlers
        dg_connection.on("open", on_open)
        dg_connection.on("message", on_message)
        dg_connection.on("error", on_error)
        dg_connection.on("close", on_close)
        
        # Start Deepgram connection
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            interim_results=True,
            utterance_end_ms=1000,
            vad_events=True,
            endpointing=300,
            encoding="mulaw",
            sample_rate=8000,
        )
        
        if not dg_connection.start(options):
            print("Failed to start Deepgram connection")
            return
        
        print("✅ Deepgram connection started")
        
    except Exception as e:
        print(f"❌ Error initializing Deepgram: {e}")
        dg_connection = None
    
    def process_user_input(call_sid, transcription):
        """Process user's transcribed speech and get AI response."""
        if not transcription or len(transcription.strip()) < 3:
            return
            
        print(f"👤 User said: {transcription}")
        
        # Check if AI is currently speaking and user interrupted
        if call_sid in call_data and call_data[call_sid].get('is_speaking', False):
            print("⚠️ User interrupted AI - stopping current response")
            call_data[call_sid]['interrupt_requested'] = True
            call_data[call_sid]['is_speaking'] = False
        
        # Get AI response
        ai_response = get_gemini_response(call_sid, transcription)
        print(f"🤖 AI responding: {ai_response}")
        
        # Send AI response back to caller
        send_ai_response_to_caller(call_sid, ai_response, twilio_client)
        
        if call_sid in call_data:
            call_data[call_sid]['is_speaking'] = True
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type == 'start':
                # Stream started
                stream_sid = data['streamSid']
                call_sid = data['start']['callSid']
                print(f"🎙️ Stream started: {stream_sid} for call: {call_sid}")
                
                # Initialize conversation for this call
                if call_sid not in conversation_history:
                    conversation_history[call_sid] = []
                
            elif event_type == 'media' and dg_connection:
                # Audio data received from caller (mulaw at 8kHz)
                media = data['media']
                audio_payload = media['payload']
                
                # Decode base64
                audio_bytes = base64.b64decode(audio_payload)
                
                # Send mulaw audio directly to Deepgram (it handles mulaw)
                dg_connection.send(audio_bytes)
                
            elif event_type == 'stop':
                # Stream stopped
                print(f"🛑 Stream stopped: {stream_sid}")
                
                # Process any remaining transcript
                if transcript_buffer.strip():
                    process_user_input(call_sid, transcript_buffer.strip())
                
                # Close Deepgram connection
                if dg_connection:
                    dg_connection.finish()
                
                if call_sid and call_sid in conversation_history:
                    print(f"📋 Conversation summary for {call_sid}:")
                    print(json.dumps(conversation_history[call_sid], indent=2))
                break
                
    except Exception as e:
        print(f"❌ Error in WebSocket: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if dg_connection:
                dg_connection.finish()
        except:
            pass
    
    print("WebSocket connection closed")

def get_gemini_response(call_sid, user_message):
    """Get conversational response from Gemini AI."""
    try:
        # Add user message to conversation history
        if call_sid not in conversation_history:
            conversation_history[call_sid] = []
        
        conversation_history[call_sid].append({
            'role': 'user',
            'parts': [user_message]
        })
        
        # Create chat with history
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat(history=conversation_history[call_sid][:-1])
        
        # Get response
        response = chat.send_message(user_message)
        ai_response = response.text
        
        # Add AI response to history
        conversation_history[call_sid].append({
            'role': 'model',
            'parts': [ai_response]
        })
        
        # Check if user wants to transfer to human
        if should_transfer_to_human(user_message, ai_response):
            return "I understand you'd like to speak with a human agent. Let me transfer you now."
        
        return ai_response
        
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        return "I apologize, I'm having trouble processing that. Could you please repeat?"

def should_transfer_to_human(user_message, ai_response):
    """Determine if call should be transferred to human."""
    transfer_keywords = ['human', 'agent', 'person', 'representative', 'speak to someone', 'real person']
    user_lower = user_message.lower()
    
    return any(keyword in user_lower for keyword in transfer_keywords)

def send_ai_response_to_caller(call_sid, response_text, client):
    """Send AI response back to the caller via Twilio."""
    try:
        # Use Twilio's Say verb to speak the response
        # This would need to be integrated with the active call
        # For now, just log it
        print(f"📢 Sending to caller: {response_text}")
        
        # TODO: Use Twilio's Media Streams to send audio back
        # This requires TTS (Text-to-Speech) integration
        # Options: Google TTS, ElevenLabs, Play.ht
        
    except Exception as e:
        print(f"Error sending AI response: {e}")

@app.route("/transfer-to-human", methods=['POST'])
def transfer_to_human():
    """
    API endpoint to transfer a call to a human agent.
    Call this when AI can't handle the request.
    
    POST body: {"call_sid": "CA...", "from_number": "+1..."}
    """
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    from_number = data.get('from_number', '')
    
    if not call_sid:
        return jsonify({'error': 'call_sid required'}), 400
    
    # Create TwiML to transfer the call
    resp = VoiceResponse()
    resp.say("Please hold while I transfer you to a human agent.", voice='alice', language='en-US')
    
    # Dial the human agent
    dial = Dial(timeout=30, caller_id=from_number)
    dial.number(HUMAN_AGENT_PHONE)
    resp.append(dial)
    
    # If agent doesn't answer
    resp.say("Sorry, no agents are available right now. Please try again later.", voice='alice', language='en-US')
    
    return jsonify({
        'success': True,
        'message': 'Transfer initiated',
        'twiml': str(resp)
    })

if __name__ == "__main__":
    # Use PORT from environment variable or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
