import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "Twilio Voice Server is running! Use the /voice endpoint for call handling."

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Respond to incoming phone calls with a brief message."""
    # Log all incoming request data for debugging
    print("=" * 50)
    print(f"Method: {request.method}")
    print(f"Form Data: {request.form}")
    print(f"Args: {request.args}")
    print("=" * 50)
    
    # Start our TwiML response
    resp = VoiceResponse()
    
    # Greet the caller and ask for input
    resp.say("Hello! Thank you for calling. Please tell me how I can help you.", 
             voice='alice', 
             language='en-US')
    
    # Use <Gather> to collect speech input
    resp.gather(
        input='speech',
        action='/process-speech',
        method='POST',
        speechTimeout='auto',
        language='en-US'
    )
    
    # If no input is detected, say goodbye
    resp.say("I didn't hear anything. Goodbye!", voice='alice', language='en-US')
    
    # Return with proper content type for Twilio
    return str(resp), 200, {'Content-Type': 'text/xml'}

@app.route("/process-speech", methods=['GET', 'POST'])
def process_speech():
    """Process the speech input from the caller."""
    # Get the speech result from Twilio
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '')
    
    # Log what the user said
    print("=" * 50)
    print(f"User said: {speech_result}")
    print(f"Confidence: {confidence}")
    print(f"All form data: {request.form}")
    print("=" * 50)
    
    # Start response
    resp = VoiceResponse()
    
    if speech_result:
        # For now, respond with a placeholder that includes what they said
        resp.say(f"I heard you say: {speech_result}. This is a placeholder response. We will process your request soon.", 
                 voice='alice', 
                 language='en-US')
    else:
        resp.say("I'm sorry, I didn't catch that.", voice='alice', language='en-US')
    
    # Say goodbye
    resp.say("Thank you for calling. Goodbye!", voice='alice', language='en-US')
    resp.hangup()
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    # Use PORT from environment variable (Render sets this) or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
