import os
import json
import base64
from flask import Flask, request
from flask_sock import Sock
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

app = Flask(__name__)
sock = Sock(app)

# Store for audio data and transcriptions
call_data = {}

@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Twilio Voice Server with WebSocket streaming is running!"

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
        'transcriptions': [],
        'sentiment': []
    }
    
    # Start TwiML response
    resp = VoiceResponse()
    
    # Greet the caller
    resp.say("Hello! Thank you for calling. Your call is now being monitored for sentiment analysis. Please speak naturally.", 
             voice='alice', 
             language='en-US')
    
    # Start bi-directional media stream
    connect = Connect()
    stream = Stream(url=f'wss://{request.host}/media-stream')
    connect.append(stream)
    resp.append(connect)
    
    # Keep the call alive
    resp.say("Thank you for your call. Goodbye!", voice='alice', language='en-US')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

@sock.route('/media-stream')
def media_stream(ws):
    """Handle WebSocket connection for real-time audio streaming."""
    call_sid = None
    stream_sid = None
    
    print("WebSocket connection established")
    
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
                print(f"Stream started: {stream_sid} for call: {call_sid}")
                
            elif event_type == 'media':
                # Audio data received
                media = data['media']
                audio_payload = media['payload']  # Base64 encoded audio (mulaw)
                
                # Decode audio (this is mulaw encoded audio at 8kHz)
                # audio_bytes = base64.b64decode(audio_payload)
                
                # Store audio chunk for processing
                if call_sid and call_sid in call_data:
                    call_data[call_sid]['audio_chunks'].append(audio_payload)
                
                # TODO: Send audio to sentiment analysis
                # For now, just log that we received audio
                if len(call_data.get(call_sid, {}).get('audio_chunks', [])) % 100 == 0:
                    print(f"Received {len(call_data[call_sid]['audio_chunks'])} audio chunks")
                
                # PLACEHOLDER: Perform sentiment analysis
                sentiment_score = analyze_sentiment_placeholder(audio_payload)
                if sentiment_score and call_sid in call_data:
                    call_data[call_sid]['sentiment'].append(sentiment_score)
                
            elif event_type == 'stop':
                # Stream stopped
                print(f"Stream stopped: {stream_sid}")
                if call_sid and call_sid in call_data:
                    print(f"Total audio chunks received: {len(call_data[call_sid]['audio_chunks'])}")
                    print(f"Sentiment data: {call_data[call_sid]['sentiment']}")
                break
                
        except Exception as e:
            print(f"Error in WebSocket: {str(e)}")
            break
    
    print("WebSocket connection closed")

def analyze_sentiment_placeholder(audio_chunk):
    """
    PLACEHOLDER function for sentiment analysis.
    Replace this with actual sentiment analysis using:
    - Speech-to-text (Deepgram, AssemblyAI, Google Speech-to-Text)
    - Sentiment analysis (OpenAI, Anthropic, HuggingFace)
    
    Returns: dict with sentiment score (positive/negative/neutral)
    """
    # For now, return a random placeholder
    # In production, you would:
    # 1. Convert audio to text
    # 2. Analyze text for sentiment
    # 3. Return sentiment score
    
    return {
        'sentiment': 'neutral',
        'score': 0.5,
        'timestamp': 'placeholder'
    }

@app.route("/sentiment/<call_sid>", methods=['GET'])
def get_sentiment(call_sid):
    """API endpoint to retrieve sentiment data for a call."""
    if call_sid in call_data:
        return {
            'call_sid': call_sid,
            'total_chunks': len(call_data[call_sid]['audio_chunks']),
            'sentiment_data': call_data[call_sid]['sentiment']
        }
    return {'error': 'Call not found'}, 404

if __name__ == "__main__":
    # Use PORT from environment variable (Render sets this) or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
