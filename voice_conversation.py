import os
import json
import base64
from flask import Flask, request, jsonify, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather, Dial
from twilio.rest import Client
from openai import OpenAI
from datetime import datetime
import requests
from dotenv import load_dotenv
from tools import call_tool, AVAILABLE_TOOLS
from customer_db import get_customer_by_phone

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# API Keys and Config
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'AC9056fdc891fed16a55a128f9d14c8bba')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '05c5255761a3e713c44447a532d574ba')
DEEPGRAM_API_KEY = os.environ.get('DEEPGRAM_API_KEY', 'aa55f81e6d4b0de0d7166cb8226c1d5f8301b92a')
HUMAN_AGENT_PHONE = os.environ.get('HUMAN_AGENT_PHONE', '+17202990300')

# Initialize OpenRouter client for Nemotron
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store conversation history and call metadata
conversation_history = {}
call_recordings = {}  # Store recording URLs and metadata
customer_cache = {}  # Cache customer data per call

# Create recordings directory if it doesn't exist
RECORDINGS_DIR = 'recordings'
ANALYSIS_DIR = 'call_analysis'
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

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
    call_recordings[call_sid] = {
        'from': from_number,
        'start_time': datetime.now().isoformat(),
        'recordings': []
    }
    
    # Cache customer data for fast tool calls
    customer = get_customer_by_phone(from_number)
    if customer:
        customer_cache[call_sid] = customer
        customer_cache[f"{call_sid}_phone"] = from_number
        print(f"✅ Customer cached: {customer['name']}")
    else:
        customer_cache[call_sid] = None
        customer_cache[f"{call_sid}_phone"] = from_number
        print(f"ℹ️ Unknown caller: {from_number}")
    
    # Start recording the call using Twilio API (non-blocking)
    try:
        recording = twilio_client.calls(call_sid).recordings.create(
            recording_status_callback=request.url_root + 'recording-status',
            recording_status_callback_method='POST'
        )
        print(f"🎙️ Recording started: {recording.sid}")
    except Exception as e:
        print(f"⚠️ Could not start recording: {e}")
    
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
    
    # Get AI response using Nemotron
    ai_response = get_nemotron_response(call_sid, speech_result)
    print(f"🤖 AI says: {ai_response}")
    
    # Speak the AI response
    resp.say(ai_response, 
             voice='Polly.Joanna', 
             language='en-US')
    
    # Continue listening
    resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

def format_for_speech(text):
    """Format text to be more readable by TTS engines."""
    import re
    
    # Format dollar amounts: $95.00 -> "95 dollars"
    text = re.sub(r'\$(\d+)\.00', r'\1 dollars', text)
    text = re.sub(r'\$(\d+\.\d+)', r'\1 dollars', text)
    text = re.sub(r'\$(\d+)', r'\1 dollars', text)
    
    # Format email addresses: spell them out with pauses
    def format_email(match):
        email = match.group(0)
        # Replace @ and . with spoken words
        email = email.replace('@', ' at ')
        email = email.replace('.', ' dot ')
        return email
    
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', format_email, text)
    
    # Format dates: 2025-11-15 -> "November 15th"
    def format_date(match):
        date_str = match.group(0)
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%B %d")
        except:
            return date_str
    
    text = re.sub(r'\d{4}-\d{2}-\d{2}', format_date, text)
    
    # Format GB: 50GB -> "50 gigabytes"
    text = re.sub(r'(\d+)\s*GB', r'\1 gigabytes', text)
    
    return text

def get_nemotron_response(call_sid, user_message):
    """Get response from Nemotron AI with tool calling support."""
    try:
        # Initialize conversation history if needed
        if call_sid not in conversation_history:
            conversation_history[call_sid] = []
        
        # Get customer data from cache
        customer = customer_cache.get(call_sid)
        from_number = customer_cache.get(f"{call_sid}_phone", "Unknown")
        
        # Build messages
        messages = []
        
        # OPTIMIZED system prompt with tool instructions
        system_prompt = f"""You are a fast, efficient customer service AI for a telecom company. Keep responses to 1-2 SHORT sentences.

CRITICAL: When customer asks about their account, IMMEDIATELY use tools:
- Bill/payment questions → check_bill
- Plan details → check_plan  
- Data usage → check_data_usage
- Call history → get_call_history
- Upgrades → get_upgrade_eligibility
- Account info → get_account_info

Customer calling: {customer['name'] if customer else 'Unknown'} from {from_number}
{"Account ID: " + customer['account_id'] if customer else ""}

Be CONCISE and ACTION-ORIENTED. Use tools proactively."""

        messages.append({'role': 'system', 'content': system_prompt})
        
        # Add history (prune to last 4 exchanges for speed)
        if len(conversation_history[call_sid]) > 8:
            messages.extend(conversation_history[call_sid][-8:])
        else:
            messages.extend(conversation_history[call_sid])
        
        messages.append({'role': 'user', 'content': user_message})
        
        # Define tools for Nemotron
        tools = [
            {"type": "function", "function": {"name": "check_bill", "description": "Get customer's monthly bill amount and due date", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "check_plan", "description": "Get plan details and features", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "check_data_usage", "description": "Get current data usage", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "get_call_history", "description": "Get previous interactions", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "get_upgrade_eligibility", "description": "Check upgrade eligibility", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "get_account_info", "description": "Get account info", "parameters": {"type": "object", "properties": {}, "required": []}}}
        ]
        
        # FAST API call with function calling
        response = openrouter_client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2:free",
            messages=messages,
            max_tokens=60,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if model wants to call a tool
        if message.tool_calls:
            print(f"🔧 Tool call requested: {message.tool_calls[0].function.name}")
            
            # Execute the tool call
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            
            # Call the tool with cached customer phone number
            tool_result = call_tool(tool_name, from_number)
            print(f"✅ Tool result: {json.dumps(tool_result)[:100]}...")
            
            # Add tool call and result to messages
            messages.append({
                'role': 'assistant',
                'content': None,
                'tool_calls': [{'id': tool_call.id, 'type': 'function', 'function': {'name': tool_name, 'arguments': '{}'}}]
            })
            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': json.dumps(tool_result)
            })
            
            # Get final response from model with tool result
            final_response = openrouter_client.chat.completions.create(
                model="nvidia/nemotron-nano-9b-v2:free",
                messages=messages,
                max_tokens=50,
                temperature=0.7
            )
            
            ai_response = final_response.choices[0].message.content.strip()
            
            # Add final response to history
            conversation_history[call_sid].append({'role': 'user', 'content': user_message})
            conversation_history[call_sid].append({'role': 'assistant', 'content': ai_response})
        else:
            # No tool call, use direct response
            ai_response = message.content.strip() if message.content else "I'm here to help!"
            
            # Add to history
            conversation_history[call_sid].append({'role': 'user', 'content': user_message})
            conversation_history[call_sid].append({'role': 'assistant', 'content': ai_response})
        
        # Keep responses ultra-concise - max 2 sentences
        sentences = ai_response.split('.')
        if len(sentences) > 2:
            ai_response = '. '.join(sentences[:2]) + '.'
        
        # Format for speech (dollars, emails, etc.)
        ai_response = format_for_speech(ai_response)
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Nemotron error: {e}")
        import traceback
        traceback.print_exc()
        return "I'm here. What do you need?"

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

@app.route("/recording-status", methods=['GET', 'POST'])
def recording_status():
    """Handle recording status callbacks from Twilio."""
    # Twilio can send GET or POST depending on configuration
    if request.method == 'GET':
        call_sid = request.args.get('CallSid', 'unknown')
        recording_sid = request.args.get('RecordingSid', '')
        recording_url = request.args.get('RecordingUrl', '')
        recording_duration = request.args.get('RecordingDuration', '0')
    else:
        call_sid = request.form.get('CallSid', 'unknown')
        recording_sid = request.form.get('RecordingSid', '')
        recording_url = request.form.get('RecordingUrl', '')
        recording_duration = request.form.get('RecordingDuration', '0')
    
    print(f"🎙️ Recording completed for call: {call_sid}")
    print(f"📼 Recording SID: {recording_sid}")
    print(f"🔗 Recording URL: {recording_url}")
    print(f"⏱️ Duration: {recording_duration} seconds")
    
    # Store recording info
    if call_sid in call_recordings:
        call_recordings[call_sid]['recordings'].append({
            'recording_sid': recording_sid,
            'recording_url': recording_url,
            'duration': recording_duration,
            'completed_at': datetime.now().isoformat()
        })
        
        # Download the recording for later analysis
        try:
            download_recording(call_sid, recording_sid, recording_url)
        except Exception as e:
            print(f"❌ Error downloading recording: {e}")
    
    return '', 200

def download_recording(call_sid, recording_sid, recording_url):
    """Download recording from Twilio for local storage and automatically analyze it."""
    # Add .mp3 extension to get the audio file
    audio_url = f"{recording_url}.mp3"
    
    # Download with Twilio auth
    response = requests.get(
        audio_url,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        stream=True
    )
    
    if response.status_code == 200:
        # Save to local file
        filename = f"{RECORDINGS_DIR}/{call_sid}_{recording_sid}.mp3"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Recording saved: {filename}")
        
        # Update metadata with local file path
        if call_sid in call_recordings:
            for rec in call_recordings[call_sid]['recordings']:
                if rec['recording_sid'] == recording_sid:
                    rec['local_file'] = filename
        
        # Automatically analyze the recording
        print(f"🔍 Starting automatic tonality analysis for call: {call_sid}")
        analysis_result = analyze_tonality_with_nemo(filename)
        
        # Store analysis with call data
        if call_sid in call_recordings:
            call_recordings[call_sid]['tonality_analysis'] = analysis_result
            
            # Save analysis to JSON file for persistence
            save_call_analysis(call_sid, call_recordings[call_sid])
            
            # Print detailed analysis to terminal
            print_analysis_to_terminal(call_sid, call_recordings[call_sid], analysis_result)
        
        return filename
    else:
        print(f"❌ Failed to download recording: {response.status_code}")
        return None

def save_call_analysis(call_sid, call_data):
    """Save call analysis to JSON file for persistence."""
    try:
        analysis_file = f"{ANALYSIS_DIR}/{call_sid}.json"
        with open(analysis_file, 'w') as f:
            json.dump(call_data, f, indent=2)
        print(f"💾 Analysis saved to: {analysis_file}")
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")

def load_call_analysis(call_sid):
    """Load call analysis from JSON file."""
    try:
        analysis_file = f"{ANALYSIS_DIR}/{call_sid}.json"
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"❌ Error loading analysis: {e}")
        return None

def print_analysis_to_terminal(call_sid, call_data, analysis_result):
    """Print detailed analysis results to terminal in a formatted way."""
    print("\n" + "=" * 80)
    print(f"📊 CALL TONALITY ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"📞 Call SID: {call_sid}")
    print(f"📱 From: {call_data.get('from', 'Unknown')}")
    print(f"🕐 Start Time: {call_data.get('start_time', 'Unknown')}")
    
    recordings = call_data.get('recordings', [])
    if recordings:
        print(f"⏱️  Duration: {recordings[0].get('duration', 'N/A')} seconds")
    
    print("-" * 80)
    
    # Check if analysis has errors
    if 'error' in analysis_result:
        print(f"❌ Analysis Error: {analysis_result.get('error')}")
        if 'note' in analysis_result:
            print(f"📝 Note: {analysis_result.get('note')}")
    else:
        # Print emotion classification results
        overall_tone = analysis_result.get('overall_tone', 'unknown')
        predicted_emotions = analysis_result.get('predicted_emotions', [])
        
        print(f"🎭 OVERALL TONE: {overall_tone.upper()}")
        print(f"😊 Predicted Emotions: {', '.join(predicted_emotions)}")
        print("-" * 80)
        
        print("🔊 ACOUSTIC FEATURES:")
        
        features = analysis_result.get('acoustic_features', {})
        if features:
            print(f"   🎵 Average Pitch: {features.get('average_pitch_hz', 0):.2f} Hz")
            print(f"   📈 Pitch Variance: {features.get('pitch_variance', 0):.2f}")
            print(f"   🔉 Average Energy: {features.get('average_energy', 0):.4f}")
            print(f"   ⚡ Energy Variance: {features.get('energy_variance', 0):.6f}")
            print(f"   🎼 Speaking Tempo: {features.get('speaking_tempo_bpm', 0):.2f} BPM")
            print(f"   📊 Zero Crossing Rate: {features.get('average_zero_crossing_rate', 0):.4f}")
            print(f"   🎶 Spectral Centroid: {features.get('average_spectral_centroid', 0):.2f} Hz")
        
        print("-" * 80)
        print("💡 EMOTION INDICATORS (from acoustic features):")
        
        indicators = analysis_result.get('emotion_indicators', {})
        if indicators:
            print(f"   🎚️  Pitch Level: {indicators.get('pitch_level', 'N/A').upper()}")
            print(f"   📉 Pitch Variability: {indicators.get('pitch_variability', 'N/A').upper()}")
            print(f"   🔊 Energy Level: {indicators.get('energy_level', 'N/A').upper()}")
            print(f"   🗣️  Emotional Arousal: {indicators.get('emotional_arousal', 'N/A').upper()}")
            if 'speaking_tempo' in indicators:
                print(f"   ⏩ Speaking Tempo: {indicators.get('speaking_tempo', 0):.1f} BPM")
    
    print("-" * 80)
    print(f"💾 Analysis saved to: call_analysis/{call_sid}.json")
    print(f"🎙️  Recording saved to: recordings/{call_sid}_*.mp3")
    print("=" * 80 + "\n")

@app.route("/analyze-call/<call_sid>", methods=['GET'])
def analyze_call(call_sid):
    """Get call tonality analysis (automatically performed after recording)."""
    # First check in-memory cache
    if call_sid in call_recordings:
        call_data = call_recordings[call_sid]
    else:
        # Try to load from disk
        call_data = load_call_analysis(call_sid)
        if not call_data:
            return jsonify({'error': 'Call not found'}), 404
    
    # Check if analysis exists
    if 'tonality_analysis' not in call_data:
        # If not analyzed yet, check if we have recordings to analyze
        recordings = call_data.get('recordings', [])
        if not recordings:
            return jsonify({'error': 'No recordings available for this call'}), 404
        
        # Get the first recording
        recording = recordings[0]
        local_file = recording.get('local_file')
        
        if not local_file or not os.path.exists(local_file):
            return jsonify({'error': 'Recording file not found'}), 404
        
        try:
            # Perform tonality analysis if not done automatically
            analysis_result = analyze_tonality_with_nemo(local_file)
            call_data['tonality_analysis'] = analysis_result
            
            # Save the analysis
            save_call_analysis(call_sid, call_data)
            
            # Update in-memory cache
            if call_sid in call_recordings:
                call_recordings[call_sid] = call_data
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'call_sid': call_sid,
        'analysis': call_data.get('tonality_analysis'),
        'call_info': {
            'from': call_data.get('from'),
            'start_time': call_data.get('start_time'),
            'recordings': call_data.get('recordings', [])
        }
    })

def analyze_tonality_with_nemo(audio_file):
    """
    Analyze audio tonality using acoustic features.
    This will extract features like pitch, energy, speaking rate, and emotional tone.
    """
    try:
        import librosa
        import numpy as np
        
        # Load audio file
        y, sr = librosa.load(audio_file, sr=16000)
        
        # 1. Pitch analysis
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        avg_pitch = np.mean(pitch_values) if pitch_values else 0
        pitch_variance = np.var(pitch_values) if pitch_values else 0
        
        # 2. Energy analysis
        rms = librosa.feature.rms(y=y)[0]
        avg_energy = np.mean(rms)
        energy_variance = np.var(rms)
        
        # 3. Speaking rate
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # 4. Zero crossing rate (emotional arousal)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        avg_zcr = np.mean(zcr)
        
        # 5. Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        avg_spectral_centroid = np.mean(spectral_centroid)
        
        # Generate emotion indicators from acoustic features
        emotion_indicators = {
            'pitch_level': 'high' if avg_pitch > 200 else 'normal' if avg_pitch > 100 else 'low',
            'pitch_variability': 'high' if pitch_variance > 100000 else 'moderate' if pitch_variance > 10000 else 'low',
            'energy_level': 'high' if avg_energy > 0.05 else 'normal' if avg_energy > 0.02 else 'low',
            'speaking_tempo': tempo,
            'emotional_arousal': 'high' if avg_zcr > 0.15 else 'moderate' if avg_zcr > 0.08 else 'low'
        }
        
        # Improved emotion classification based on features
        emotions = []
        
        # Anger detection: high pitch variance + high arousal + elevated pitch
        if pitch_variance > 100000 and avg_zcr > 0.15 and avg_pitch > 150:
            emotions.append('angry')
        # Excited: high energy + high pitch + high variance
        elif avg_pitch > 200 and pitch_variance > 1000 and avg_energy > 0.05:
            emotions.append('excited')
        # Anxious/stressed: high pitch variance but lower energy
        elif avg_pitch > 200 and pitch_variance > 1000:
            emotions.append('anxious')
        # Calm: low pitch + low energy + low variance
        elif avg_pitch < 100 and avg_energy < 0.03:
            emotions.append('calm' if pitch_variance < 500 else 'bored')
        # Stressed: high energy + high arousal but not extremely high pitch
        elif avg_energy > 0.05 and avg_zcr > 0.1:
            emotions.append('stressed' if pitch_variance > 1000 else 'engaged')
        else:
            emotions.append('neutral')
        
        return {
            'acoustic_features': {
                'average_pitch_hz': float(avg_pitch),
                'pitch_variance': float(pitch_variance),
                'average_energy': float(avg_energy),
                'energy_variance': float(energy_variance),
                'speaking_tempo_bpm': float(tempo),
                'average_zero_crossing_rate': float(avg_zcr),
                'average_spectral_centroid': float(avg_spectral_centroid)
            },
            'emotion_indicators': emotion_indicators,
            'predicted_emotions': emotions,
            'overall_tone': emotions[0] if emotions else 'neutral',
            'analysis_timestamp': datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            'error': 'librosa not installed. Install with: pip install librosa',
            'note': 'Audio analysis requires librosa and numpy'
        }
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': f'Analysis failed: {str(e)}',
            'note': 'Check logs for details'
        }

@app.route("/recordings", methods=['GET'])
def list_recordings():
    """List all recorded calls with their analysis."""
    # Combine in-memory and saved recordings
    all_recordings = dict(call_recordings)
    
    # Load any saved analyses from disk that aren't in memory
    if os.path.exists(ANALYSIS_DIR):
        for filename in os.listdir(ANALYSIS_DIR):
            if filename.endswith('.json'):
                call_sid = filename.replace('.json', '')
                if call_sid not in all_recordings:
                    loaded_data = load_call_analysis(call_sid)
                    if loaded_data:
                        all_recordings[call_sid] = loaded_data
    
    # Create summary view
    summaries = []
    for call_sid, data in all_recordings.items():
        summary = {
            'call_sid': call_sid,
            'from': data.get('from'),
            'start_time': data.get('start_time'),
            'duration': data.get('recordings', [{}])[0].get('duration', 'N/A') if data.get('recordings') else 'N/A',
            'has_recording': len(data.get('recordings', [])) > 0,
            'has_analysis': 'tonality_analysis' in data,
            'overall_tone': data.get('tonality_analysis', {}).get('overall_tone', 'not_analyzed')
        }
        summaries.append(summary)
    
    # Sort by start time (most recent first)
    summaries.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    return jsonify({
        'recordings': summaries,
        'count': len(summaries),
        'detailed_data_available': True
    })

@app.route("/call-details/<call_sid>", methods=['GET'])
def get_call_details(call_sid):
    """Get full details for a specific call including analysis."""
    # Try in-memory first
    if call_sid in call_recordings:
        call_data = call_recordings[call_sid]
    else:
        # Load from disk
        call_data = load_call_analysis(call_sid)
        if not call_data:
            return jsonify({'error': 'Call not found'}), 404
    
    return jsonify({
        'call_sid': call_sid,
        'full_data': call_data
    })

@app.route("/end-call", methods=['POST'])
def end_call():
    """Handle call ending and cleanup."""
    call_sid = request.form.get('CallSid', 'unknown')
    
    print(f"📋 Call ended: {call_sid}")
    if call_sid in conversation_history:
        print(f"Conversation had {len(conversation_history[call_sid])} exchanges")
        # Cleanup conversation history but keep recordings
        del conversation_history[call_sid]
    
    # Cleanup customer cache
    if call_sid in customer_cache:
        del customer_cache[call_sid]
    if f"{call_sid}_phone" in customer_cache:
        del customer_cache[f"{call_sid}_phone"]
    
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
