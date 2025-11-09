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
    
    # Read a message aloud to the caller
    resp.say("Hello! Thank you for calling. This is a Twilio powered voice response. Have a great day!", 
             voice='alice', 
             language='en-US')
    
    return str(resp)

if __name__ == "__main__":
    # Use PORT from environment variable (Render sets this) or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
