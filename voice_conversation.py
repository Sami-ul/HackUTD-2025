import os
import json
import base64
from flask import Flask, request, jsonify, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
import google.generativeai as genai
from datetime import datetime
import requests

app = Flask(__name__)

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

# Store conversation history
conversation_history = {}

@app.route("/", methods=['GET'])
def home():
    """Home endpoint to verify the server is running."""
    return "🤖 Twilio AI Voice Assistant is running!"

@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Handle incoming phone calls - start conversation loop."""
    call_sid = request.form.get('CallSid', 'unknown')
    from_number = request.form.get('From', '')
    
    print("=" * 50)
    print(f"🎙️ Incoming call: {call_sid}")
    print(f"📞 From: {from_number}")
    print(f"⏰ Time: {datetime.now()}")
    print("=" * 50)
    
    # Initialize conversation history for this call
    conversation_history[call_sid] = []
    
    # Start TwiML response
    resp = VoiceResponse()
    
    # Greet the caller
    resp.say("Hello! I'm your A I assistant. How can I help you today?", 
             voice='Polly.Joanna',
             language='en-US')
    
    # Start listening loop
    resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

@app.route("/listen", methods=['GET', 'POST'])
def listen():
    """Listen for user speech using Gather with speech recognition."""
    resp = VoiceResponse()
    
    # Use Gather to capture speech
    gather = resp.gather(
        input='speech',
        action='/process',
        method='POST',
        speechTimeout='auto',  # Auto-detect when user stops speaking
        language='en-US',
        speechModel='phone_call',  # Optimized for phone calls
    )
    
    # If no speech detected, prompt again
    resp.say("I'm still here. What would you like to know?", 
             voice='Polly.Joanna', 
             language='en-US')
    resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

@app.route("/process", methods=['POST'])
def process():
    """Process user's speech and respond with AI."""
    call_sid = request.form.get('CallSid', 'unknown')
    speech_result = request.form.get('SpeechResult', '')
    confidence = request.form.get('Confidence', '0')
    
    print(f"👤 User said: {speech_result} (confidence: {confidence})")
    
    resp = VoiceResponse()
    
    if not speech_result:
        resp.say("I didn't catch that. Could you please repeat?", 
                 voice='Polly.Joanna', 
                 language='en-US')
        resp.redirect('/listen')
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    # Check for handoff to human
    if should_transfer_to_human(speech_result):
        resp.say("I understand you'd like to speak with a human agent. Let me transfer you.", 
                 voice='Polly.Joanna', 
                 language='en-US')
        
        dial = Dial(timeout=30)
        dial.number(HUMAN_AGENT_PHONE)
        resp.append(dial)
        
        resp.say("Sorry, no agents are available right now. I'll continue helping you.", 
                 voice='Polly.Joanna', 
                 language='en-US')
        resp.redirect('/listen')
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    # Get AI response using Gemini
    ai_response = get_gemini_response(call_sid, speech_result)
    print(f"🤖 AI says: {ai_response}")
    
    # Speak the AI response
    resp.say(ai_response, 
             voice='Polly.Joanna', 
             language='en-US')
    
    # Continue listening
    resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

def get_gemini_response(call_sid, user_message):
    """Get conversational response from Gemini AI."""
    try:
        # Initialize conversation history if needed
        if call_sid not in conversation_history:
            conversation_history[call_sid] = []
        
        # Add system prompt on first message
        if len(conversation_history[call_sid]) == 0:
            conversation_history[call_sid].append({
                'role': 'user',
                'parts': ['You are a helpful AI assistant on a phone call. Keep responses concise, friendly, and conversational. Limit responses to 2-3 sentences max since this is a voice conversation.']
            })
            conversation_history[call_sid].append({
                'role': 'model',
                'parts': ['Understood! I will keep my responses brief and conversational.']
            })
        
        # Add user message to history
        conversation_history[call_sid].append({
            'role': 'user',
            'parts': [user_message]
        })
        
        # Create chat with history
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        chat = model.start_chat(history=conversation_history[call_sid][:-1])
        
        # Get response
        response = chat.send_message(user_message)
        ai_response = response.text
        
        # Keep responses concise for phone conversations
        # If response is too long, truncate it
        sentences = ai_response.split('.')
        if len(sentences) > 3:
            ai_response = '. '.join(sentences[:3]) + '.'
        
        # Add to history
        conversation_history[call_sid].append({
            'role': 'model',
            'parts': [ai_response]
        })
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return "I apologize, I'm having trouble processing that right now. Could you try rephrasing your question?"

def should_transfer_to_human(user_message):
    """Check if user wants to speak with a human."""
    transfer_keywords = ['human', 'agent', 'person', 'representative', 'speak to someone', 'real person', 'operator', 'supervisor']
    user_lower = user_message.lower()
    return any(keyword in user_lower for keyword in transfer_keywords)

@app.route("/transfer-to-human", methods=['POST'])
def transfer_to_human():
    """API endpoint to transfer call to human agent."""
    data = request.get_json() or {}
    call_sid = data.get('call_sid')
    from_number = data.get('from_number', '')
    
    if not call_sid:
        return jsonify({'error': 'call_sid required'}), 400
    
    resp = VoiceResponse()
    resp.say("Please hold while I transfer you to a human agent.", 
             voice='Polly.Joanna', 
             language='en-US')
    
    dial = Dial(timeout=30, caller_id=from_number)
    dial.number(HUMAN_AGENT_PHONE)
    resp.append(dial)
    
    resp.say("Sorry, no agents are available right now.", 
             voice='Polly.Joanna', 
             language='en-US')
    
    return jsonify({
        'success': True,
        'message': 'Transfer initiated',
        'twiml': str(resp)
    })

@app.route("/end-call", methods=['POST'])
def end_call():
    """Handle call ending and cleanup."""
    call_sid = request.form.get('CallSid', 'unknown')
    
    print(f"📋 Call ended: {call_sid}")
    if call_sid in conversation_history:
        print(f"Conversation had {len(conversation_history[call_sid])} exchanges")
        # Cleanup
        del conversation_history[call_sid]
    
    resp = VoiceResponse()
    resp.say("Thank you for calling. Goodbye!", 
             voice='Polly.Joanna', 
             language='en-US')
    resp.hangup()
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Conversational AI Voice Server on port {port}")
    print(f"📞 Ready to handle calls!")
    app.run(host="0.0.0.0", port=port, debug=False)
