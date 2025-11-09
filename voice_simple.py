import os
import json
import base64
from flask import Flask, request, jsonify
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Dial
from twilio.rest import Client
import google.generativeai as genai
from datetime import datetime
import requests

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

# Store for call data and conversation history
call_data = {}
conversation_history = {}

@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Twilio Voice AI Server is running! 🤖"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls and set up media stream with AI conversation."""
    call_sid = request.form.get('CallSid', 'unknown')
    from_number = request.form.get('From', '')
    
    print("=" * 50)
    print(f"🎙️ Incoming call: {call_sid}")
    print(f"📞 From: {from_number}")
    print(f"⏰ Time: {datetime.now()}")
    print("=" * 50)
    
    # Initialize conversation history for this call
    conversation_history[call_sid] = []
    
    # Initialize call data storage
    call_data[call_sid] = {
        'audio_buffer': [],
        'transcriptions': [],
        'is_speaking': False,
        'from_number': from_number
    }
    
    # Start TwiML response
    resp = VoiceResponse()
    
    # Brief greeting
    resp.say("Hello! I'm your A I assistant powered by Gemini. How can I help you today?", 
             voice='Polly.Joanna',
             language='en-US')
    
    # Start bi-directional media stream for real-time conversation
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

@sock.route('/media-stream')
def media_stream(ws):
    """Handle WebSocket connection for real-time conversational AI."""
    call_sid = None
    stream_sid = None
    audio_buffer = []
    silence_count = 0
    SILENCE_THRESHOLD = 15  # Reduced - process faster after user stops talking
    MIN_AUDIO_LENGTH = 30   # Reduced - minimum audio chunks before processing
    
    print("✅ WebSocket connection established")
    
    def transcribe_with_deepgram(audio_chunks):
        """Use Deepgram API to transcribe audio."""
        try:
            # Combine audio chunks
            audio_data = b''.join([base64.b64decode(chunk) for chunk in audio_chunks])
            
            # Call Deepgram API
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/mulaw"
            }
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "language": "en-US",
                "encoding": "mulaw",
                "sample_rate": "8000"
            }
            
            response = requests.post(url, headers=headers, params=params, data=audio_data)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                return transcript.strip()
            else:
                print(f"❌ Deepgram error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None
    
    def speak_response_to_caller(call_sid, text):
        """Make the AI speak using Twilio's Say command by redirecting the call."""
        try:
            # Create a temporary endpoint that will return the TwiML
            response_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            
            # Redirect the call to speak the response and return to streaming
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{response_text}</Say>
    <Connect>
        <Stream url="wss://{request.host}/media-stream" />
    </Connect>
</Response>'''
            
            # Update the call with new TwiML
            call = twilio_client.calls(call_sid).update(twiml=twiml)
            print(f"✅ Speaking to caller: {text[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error speaking to caller: {e}")
            return False
    
    def process_user_input(call_sid, transcription):
        """Process user's transcribed speech and get AI response."""
        if not transcription or len(transcription.strip()) < 3:
            return
            
        print(f"👤 User said: {transcription}")
        
        # Get AI response
        ai_response = get_gemini_response(call_sid, transcription)
        print(f"🤖 AI responding: {ai_response}")
        
        # Speak the response back
        speak_response_to_caller(call_sid, ai_response)
    
    try:
        while True:
            message = ws.receive()
            if message is None:
                break
                
            data = json.loads(message)
            event_type = data.get('event')
            
            if event_type == 'start':
                stream_sid = data['streamSid']
                call_sid = data['start']['callSid']
                print(f"🎙️ Stream started for call: {call_sid}")
                
            elif event_type == 'media':
                media = data['media']
                audio_payload = media['payload']
                
                if call_sid in call_data:
                    # Add to buffer
                    audio_buffer.append(audio_payload)
                    
                    # Simple voice activity detection
                    audio_bytes = base64.b64decode(audio_payload)
                    # Check if there's actual sound (very simple check)
                    if sum(audio_bytes) < 100:  # Silence threshold
                        silence_count += 1
                    else:
                        silence_count = 0
                    
                    # Process when we have enough audio and detect silence
                    if len(audio_buffer) >= MIN_AUDIO_LENGTH and silence_count >= SILENCE_THRESHOLD:
                        print(f"🎤 Processing {len(audio_buffer)} audio chunks...")
                        
                        # Transcribe with Deepgram
                        transcription = transcribe_with_deepgram(audio_buffer)
                        
                        if transcription:
                            process_user_input(call_sid, transcription)
                        
                        # Reset
                        audio_buffer = []
                        silence_count = 0
                
            elif event_type == 'stop':
                print(f"🛑 Stream stopped for: {call_sid}")
                
                # Process any remaining audio
                if len(audio_buffer) > 20:  # Reduced threshold
                    transcription = transcribe_with_deepgram(audio_buffer)
                    if transcription:
                        process_user_input(call_sid, transcription)
                
                break
                
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    
    print("🔒 WebSocket connection closed")

def get_gemini_response(call_sid, user_message):
    """Get conversational response from Gemini AI."""
    try:
        # Add user message to history
        if call_sid not in conversation_history:
            conversation_history[call_sid] = []
        
        conversation_history[call_sid].append({
            'role': 'user',
            'parts': [user_message]
        })
        
        # Create chat - use gemini-2.5-flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        chat = model.start_chat(history=conversation_history[call_sid][:-1])
        
        # Get response
        response = chat.send_message(user_message)
        ai_response = response.text
        
        # Add to history
        conversation_history[call_sid].append({
            'role': 'model',
            'parts': [ai_response]
        })
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "I apologize, I'm having trouble processing that. Could you please repeat?"

@app.route("/transfer-to-human", methods=['POST'])
def transfer_to_human():
    """Transfer call to human agent."""
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    from_number = data.get('from_number', '')
    
    if not call_sid:
        return jsonify({'error': 'call_sid required'}), 400
    
    resp = VoiceResponse()
    resp.say("Please hold while I transfer you to a human agent.", voice='Polly.Joanna', language='en-US')
    
    dial = Dial(timeout=30, caller_id=from_number)
    dial.number(HUMAN_AGENT_PHONE)
    resp.append(dial)
    
    resp.say("Sorry, no agents are available right now.", voice='Polly.Joanna', language='en-US')
    
    return jsonify({
        'success': True,
        'message': 'Transfer initiated',
        'twiml': str(resp)
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
