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
tool_result_cache = {}  # Cache tool results for speed

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
    
    # Get location data from Twilio (based on phone number)
    caller_city = request.form.get('FromCity', '')
    caller_state = request.form.get('FromState', '')
    caller_country = request.form.get('FromCountry', '')
    caller_zip = request.form.get('FromZip', '')
    
    # Store location data
    if call_sid not in customer_cache:
        customer_cache[call_sid] = {}
    customer_cache[call_sid]['phone'] = from_number
    customer_cache[call_sid]['location'] = {
        'city': caller_city,
        'state': caller_state,
        'country': caller_country,
        'zip': caller_zip
    }
    
    if caller_city or caller_state:
        print(f"📍 Caller location: {caller_city}, {caller_state} {caller_zip} ({caller_country})")
    
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
    
    # Set status callback for when call ends
    try:
        twilio_client.calls(call_sid).update(
            status_callback=request.url_root + 'end-call',
            status_callback_method='POST',
            status_callback_event=['completed', 'failed', 'busy', 'no-answer', 'canceled']
        )
        print(f"✅ Status callback configured for call end: {request.url_root}end-call")
    except Exception as e:
        print(f"⚠️ Could not set status callback: {e}")
    
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
    
    # Get conversation history for this call
    if call_sid not in conversation_history:
        conversation_history[call_sid] = []
    
    # Get customer phone number
    from_number = customer_cache.get(f"{call_sid}_phone", request.form.get('From', ''))
    
    # Get location data (from initial call or current request)
    # customer_cache[call_sid] might be the customer dict, so check if it has location as dict
    cache_entry = customer_cache.get(call_sid, {})
    if isinstance(cache_entry, dict):
        caller_location = cache_entry.get('location', {})
        # If location is a string (from customer DB), convert to empty dict
        if isinstance(caller_location, str):
            caller_location = {}
    else:
        caller_location = {}
    
    if not caller_location or not isinstance(caller_location, dict):
        # Try to get from current request
        caller_location = {
            'city': request.form.get('FromCity', ''),
            'state': request.form.get('FromState', ''),
            'country': request.form.get('FromCountry', ''),
            'zip': request.form.get('FromZip', '')
        }
        if caller_location.get('city') or caller_location.get('state'):
            customer_cache[call_sid] = customer_cache.get(call_sid, {})
            customer_cache[call_sid]['location'] = caller_location
    
    # Check for dropped calls in user's speech and auto-report
    dropped_calls_detected = detect_dropped_calls(speech_result)
    if dropped_calls_detected:
        num_dropped = dropped_calls_detected.get('count', 0)
        severity = dropped_calls_detected.get('severity', 'moderate')
        
        print(f"📉 Detected dropped calls report: {num_dropped} calls, severity: {severity}")
        
        # Report dropped calls
        from tools import report_dropped_calls
        drop_result = report_dropped_calls(from_number, severity=severity)
        print(f"   Result: {drop_result.get('message', 'Reported')}")
        
        # Find closest node and mark as degraded (try even if no city, will use fallback)
        from tools import mark_closest_node_degraded
        node_result = mark_closest_node_degraded(caller_location, from_number)
        if node_result.get('success'):
            print(f"   ✅ Marked closest node as degraded: {node_result.get('node_name')} in {node_result.get('node_city', 'Unknown')}")
        else:
            print(f"   ⚠️ Could not mark node: {node_result.get('message', 'Unknown error')}")
    
    # Check if we should transfer to human dashboard
    should_transfer = False
    transfer_reason = ""
    
    # Check explicit request for human
    if should_transfer_to_human(speech_result):
        should_transfer = True
        transfer_reason = "Customer requested human agent"
    
    # Check for complex query
    elif detect_complex_query(speech_result, conversation_history[call_sid]):
        should_transfer = True
        transfer_reason = "Complex query detected"
    
    # Check if AI is struggling (conversation going in circles)
    elif len(conversation_history[call_sid]) > 8:
        # If we've had many exchanges, consider transferring
        recent_responses = [msg['content'].lower() for msg in conversation_history[call_sid][-4:] if msg['role'] == 'assistant']
        if any('sorry' in resp or "i can't" in resp or "i don't" in resp for resp in recent_responses):
            should_transfer = True
            transfer_reason = "AI unable to resolve issue"
    
    if should_transfer:
        print(f"🔄 Transferring call: {transfer_reason}")
        
        # Route call to live dashboard first
        transfer_result = transfer_to_live_dashboard(
            call_sid, 
            from_number, 
            conversation_history[call_sid]
        )
        
        if transfer_result.get('success'):
            # Successfully routed to dashboard, now transfer the call
            resp.say("I understand you need additional assistance. Let me transfer you to a specialist who can help you better.", 
                     voice='Polly.Joanna', 
                     language='en-US')
            
            # Dial the human agent number
            # Use action URL to handle dial status, and increase timeout
            dial = Dial(timeout=60, caller_id=from_number, action='/dial-status', method='POST')
            dial.number(HUMAN_AGENT_PHONE)
            resp.append(dial)
            
            # This message will only play if dial fails (timeout, busy, no answer)
            # But we'll handle it in the action URL instead
            # resp.say("Sorry, no agents are available right now. Please try again later.", 
            #          voice='Polly.Joanna', 
            #          language='en-US')
        else:
            # Dashboard routing failed, but still try to transfer
            print(f"⚠️ Dashboard routing failed, but continuing with call transfer")
            resp.say("Let me transfer you to a human agent.", 
                     voice='Polly.Joanna', 
                     language='en-US')
            
            # Dial the human agent number with longer timeout
            dial = Dial(timeout=60, caller_id=from_number, action='/dial-status', method='POST')
            dial.number(HUMAN_AGENT_PHONE)
            resp.append(dial)
            
            # If dial fails, redirect back to listen (don't say "no agents available")
            resp.redirect('/listen')
        
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    # Get AI response using Nemotron
    ai_response = get_nemotron_response(call_sid, speech_result)
    print(f"🤖 AI says: {ai_response}")
    
    # Check if AI response indicates it can't help
    ai_response_lower = ai_response.lower()
    if any(phrase in ai_response_lower for phrase in ["i can't", "i'm unable", "i don't have", "i'm sorry, i"]):
        # AI is struggling, offer to transfer
        print(f"🤖 AI response suggests inability to help, offering transfer")
        resp.say(ai_response, voice='Polly.Joanna', language='en-US')
        resp.say("Would you like me to transfer you to a human agent who can better assist you?", 
                 voice='Polly.Joanna', 
                 language='en-US')
        resp.redirect('/listen')
        return str(resp), 200, {'Content-Type': 'text/xml'}
    
    # Speak the AI response
    resp.say(ai_response, 
             voice='Polly.Joanna', 
             language='en-US')
    
    # Continue listening
    resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}

def format_for_speech(text):
    """Ultra-fast TTS formatting - critical replacements only."""
    # Fast replacements for common patterns
    text = text.replace('$', '').replace('.00', '')  # "$95.00" → "95"
    text = text.replace('@', ' at ').replace('.com', ' dot com')  # emails
    text = text.replace('GB', ' gigabytes')  # data usage
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
        
        # ULTRA-COMPACT system prompt for maximum speed
        system_prompt = f"""Fast telecom AI. ONE sentence only.
Tools: get_account_info, check_network_status, report_coverage_issue, report_dropped_calls, check_bill, check_plan, check_data_usage, get_upgrade_eligibility
Customer: {customer['name'] if customer else 'Unknown'}
Use tools to get info, then reason from data. Personalize response.
If customer reports coverage issues in a city, use report_coverage_issue with the city name.
If customer reports dropped calls, use report_dropped_calls to update metrics.
Note: Dropped calls are automatically detected and reported when mentioned by the customer."""

        messages.append({'role': 'system', 'content': system_prompt})
        
        # MINIMAL history - last 4 messages only for speed
        if len(conversation_history[call_sid]) > 4:
            messages.extend(conversation_history[call_sid][-4:])
        else:
            messages.extend(conversation_history[call_sid])
        
        messages.append({'role': 'user', 'content': user_message})
        
        # REDUCED tools - only most common for speed
        tools = [
            {"type": "function", "function": {"name": "get_account_info", "description": "Get customer account details (name, email, plan, location)", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "check_network_status", "description": "Check live network status, towers, and outages in customer's area", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "report_coverage_issue", "description": "Report coverage issues for a city (e.g., 'Arlington', 'Dallas', 'Plano'). Marks nodes as degraded with user issues reported. Use when customer says coverage is spotty/bad in a city.", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "City name where coverage issues are reported (e.g., 'Arlington', 'Dallas', 'Plano', 'Irving')"}}, "required": ["city"]}}},
            {"type": "function", "function": {"name": "report_dropped_calls", "description": "Report dropped calls and update network metrics. Use when customer reports dropped calls, calls cutting out, or call quality issues. Updates call_drop_rate metric.", "parameters": {"type": "object", "properties": {"severity": {"type": "string", "description": "Severity of dropped calls: 'low' (occasional), 'moderate' (frequent), or 'high' (constant). Defaults to 'moderate'."}}, "required": []}}},
            {"type": "function", "function": {"name": "check_bill", "description": "Get bill", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "check_plan", "description": "Get plan", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "check_data_usage", "description": "Get data", "parameters": {"type": "object", "properties": {}, "required": []}}},
            {"type": "function", "function": {"name": "get_upgrade_eligibility", "description": "Check upgrade", "parameters": {"type": "object", "properties": {}, "required": []}}}
        ]
        
        # SPEED-OPTIMIZED API call with function calling
        response = openrouter_client.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2:free",
            messages=messages,
            max_tokens=40,        # REDUCED from 60 for speed
            temperature=0.5,      # REDUCED from 0.7 for faster token selection
            top_p=0.85,           # ADDED for speed optimization
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if model wants to call a tool
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            
            # Extract tool arguments if provided
            tool_args = {}
            if tool_call.function.arguments:
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except:
                    tool_args = {}
            
            # CACHED tool execution for speed (but don't cache state-changing tools)
            state_changing_tools = ['report_coverage_issue', 'report_dropped_calls']
            cache_key = f"{call_sid}_{tool_name}_{json.dumps(tool_args, sort_keys=True)}"
            if cache_key in tool_result_cache and tool_name not in state_changing_tools:
                tool_result = tool_result_cache[cache_key]
                print(f"⚡ Tool cached: {tool_name}")
            else:
                # Call tool with arguments
                if tool_name == 'report_coverage_issue' and 'city' in tool_args:
                    from tools import report_coverage_issue
                    tool_result = report_coverage_issue(from_number, city=tool_args.get('city'))
                elif tool_name == 'report_dropped_calls':
                    from tools import report_dropped_calls
                    severity = tool_args.get('severity', 'moderate')
                    tool_result = report_dropped_calls(from_number, severity=severity)
                else:
                    tool_result = call_tool(tool_name, from_number)
                # Don't cache state-changing tools
                if tool_name not in state_changing_tools:
                    tool_result_cache[cache_key] = tool_result
                print(f"🔧 Tool called: {tool_name} with args: {tool_args}")
            
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
            
            # Get final response from model with tool result - SPEED OPTIMIZED
            final_response = openrouter_client.chat.completions.create(
                model="nvidia/nemotron-nano-9b-v2:free",
                messages=messages,
                max_tokens=35,        # REDUCED from 50 for speed
                temperature=0.5,      # REDUCED from 0.7
                top_p=0.85           # ADDED for speed
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
        
        # FAST formatting - minimal processing
        ai_response = format_for_speech(ai_response)
        
        return ai_response
        
    except Exception as e:
        print(f"❌ Nemotron error: {e}")
        import traceback
        traceback.print_exc()
        return "I'm here. What do you need?"

def detect_dropped_calls(user_message):
    """
    Detect if user is reporting dropped calls and extract count.
    
    Returns:
        dict: {'detected': True, 'count': int, 'severity': str} or None
    """
    user_lower = user_message.lower()
    
    # Keywords that indicate dropped calls
    dropped_keywords = ['dropped call', 'call dropped', 'calls dropped', 'dropped', 
                       'call cut out', 'call disconnected', 'call ended', 'lost call',
                       'call failed', 'call dropped', 'dropping calls']
    
    # Check if user mentions dropped calls
    if not any(keyword in user_lower for keyword in dropped_keywords):
        return None
    
    # Try to extract number of dropped calls
    import re
    # Look for patterns like "6 or 7 dropped calls", "5 dropped calls", "several dropped calls"
    number_patterns = [
        r'(\d+)\s*(?:or\s*\d+)?\s*dropped',
        r'(\d+)\s*dropped\s*calls?',
        r'dropped\s*(\d+)\s*calls?',
        r'(\d+)\s*calls?\s*dropped',
    ]
    
    num_dropped = 0
    for pattern in number_patterns:
        match = re.search(pattern, user_lower)
        if match:
            try:
                num_dropped = int(match.group(1))
                break
            except:
                pass
    
    # If no number found, check for severity indicators
    if num_dropped == 0:
        if any(word in user_lower for word in ['many', 'several', 'multiple', 'a lot', 'tons', 'many']):
            num_dropped = 5  # Default to moderate
        elif any(word in user_lower for word in ['few', 'couple', 'some']):
            num_dropped = 2  # Low
        else:
            num_dropped = 3  # Default moderate
    
    # Determine severity based on count
    if num_dropped >= 10:
        severity = 'high'
    elif num_dropped >= 5:
        severity = 'moderate'
    else:
        severity = 'low'
    
    return {
        'detected': True,
        'count': num_dropped,
        'severity': severity
    }

def should_transfer_to_human(user_message):
    """Check if user wants to speak with a human."""
    transfer_keywords = ['human', 'agent', 'person', 'representative', 'speak to someone', 'real person', 'operator', 'supervisor']
    user_lower = user_message.lower()
    return any(keyword in user_lower for keyword in transfer_keywords)

def detect_complex_query(user_message, conversation_history):
    """Detect if the query is too complex for the AI assistant."""
    # Check for complex indicators
    complex_indicators = [
        'refund', 'cancel', 'dispute', 'complaint', 'legal', 'lawsuit',
        'billing error', 'unauthorized charge', 'fraud', 'identity theft',
        'multiple issues', 'escalate', 'manager', 'supervisor'
    ]
    
    user_lower = user_message.lower()
    
    # Check message for complex keywords
    if any(indicator in user_lower for indicator in complex_indicators):
        return True
    
    # Check if conversation has been going in circles (same question asked multiple times)
    if len(conversation_history) > 6:
        recent_user_messages = [msg['content'].lower() for msg in conversation_history[-6:] if msg['role'] == 'user']
        if len(recent_user_messages) >= 3:
            # Check if user is repeating themselves
            unique_messages = set(recent_user_messages)
            if len(unique_messages) < len(recent_user_messages) * 0.6:  # More than 40% repetition
                return True
    
    return False

def transfer_to_live_dashboard(call_sid, from_number, conversation_history):
    """
    Transfer call to live dashboard by routing it through the HackUTD-1 API.
    This creates a notification in the dashboard with conversation history and sentiment.
    
    Args:
        call_sid: Twilio call SID
        from_number: Customer's phone number
        conversation_history: List of conversation messages
        
    Returns:
        dict: Result of routing the call
    """
    try:
        # Build conversation transcript
        transcript_parts = []
        customer_text_parts = []
        
        for msg in conversation_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'user':
                transcript_parts.append(f"customer {content}")
                customer_text_parts.append(content)
            elif role == 'assistant':
                transcript_parts.append(f"agent {content}")
        
        initial_transcript = " ".join(transcript_parts)
        customer_text = " ".join(customer_text_parts)
        
        # Get customer info
        customer = get_customer_by_phone(from_number)
        customer_info = None
        
        # Ensure customer is a dict, not a string
        if customer and not isinstance(customer, dict):
            customer = None
        
        if customer:
            # Get location from Twilio if available, otherwise use customer DB
            cache_entry = customer_cache.get(call_sid, {})
            location_data = {}
            if isinstance(cache_entry, dict):
                location_data = cache_entry.get('location', {})
            
            # Ensure location_data is a dict, not a string
            if isinstance(location_data, str):
                twilio_location = {}
            elif isinstance(location_data, dict):
                twilio_location = location_data
            else:
                twilio_location = {}
            
            location_str = ''
            if twilio_location and isinstance(twilio_location, dict):
                if twilio_location.get('city') or twilio_location.get('state'):
                    location_parts = []
                    if twilio_location.get('city'):
                        location_parts.append(twilio_location['city'])
                    if twilio_location.get('state'):
                        location_parts.append(twilio_location['state'])
                    if twilio_location.get('zip'):
                        location_parts.append(twilio_location['zip'])
                    location_str = ', '.join(location_parts)
            
            # Fallback to customer DB location if no Twilio location
            if not location_str and isinstance(customer, dict):
                location_str = customer.get('location', '')
            
            # Safely get plan name
            plan_name = 'Unknown'
            if isinstance(customer, dict):
                plan = customer.get('plan', {})
                if isinstance(plan, dict):
                    plan_name = plan.get('name', 'Unknown')
                elif isinstance(plan, str):
                    plan_name = plan
            
            customer_info = {
                'name': customer.get('name', 'Unknown') if isinstance(customer, dict) else 'Unknown',
                'phone': from_number,
                'email': customer.get('email', '') if isinstance(customer, dict) else '',
                'account_id': customer.get('account_id', '') if isinstance(customer, dict) else '',
                'location': location_str,
                'location_data': twilio_location if twilio_location else None,  # Include full location data
                'plan': plan_name
            }
            
            if twilio_location and isinstance(twilio_location, dict) and twilio_location.get('city'):
                print(f"📍 Using Twilio location: {twilio_location['city']}, {twilio_location.get('state', '')}")
        
        # Send directly to hack25 backend (port 3002)
        hack25_url = "http://localhost:3002/api/calls/transfer"
        
        # Analyze sentiment from conversation
        sentiment_label = 'neutral'
        sentiment_score = 0.5
        urgency_level = 'MEDIUM'
        urgency_score = 0.5
        
        # Simple sentiment analysis from customer text
        negative_words = ['bad', 'slow', 'dropped', 'terrible', 'awful', 'horrible', 'frustrated', 
                          'frustrating', 'issue', 'problem', 'broken', 'down', 'outage', 'complaint', 'angry']
        positive_words = ['good', 'great', 'love', 'excellent', 'amazing', 'wonderful', 'thanks', 'thank you', 'happy']
        
        text_lower = customer_text.lower()
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            sentiment_label = 'negative'
            sentiment_score = max(0.1, 0.5 - (negative_count * 0.1))
            urgency_level = 'HIGH' if negative_count >= 3 else 'MEDIUM'
            urgency_score = min(0.9, 0.5 + (negative_count * 0.1))
        elif positive_count > negative_count:
            sentiment_label = 'positive'
            sentiment_score = min(0.95, 0.5 + (positive_count * 0.1))
            urgency_level = 'LOW'
            urgency_score = 0.3
        else:
            sentiment_label = 'neutral'
            sentiment_score = 0.5
            urgency_level = 'MEDIUM'
            urgency_score = 0.5
        
        transfer_data = {
            'call_id': call_sid,
            'phone_number': from_number,
            'customer_name': customer_info.get('name', 'Unknown') if customer_info else 'Unknown',
            'customer_info': customer_info,
            'customer_text': customer_text,
            'initial_transcript': initial_transcript,
            'sentiment': {'label': sentiment_label, 'score': sentiment_score},
            'urgency': {'level': urgency_level, 'score': urgency_score},
            'emotion': 'angry' if sentiment_label == 'negative' and sentiment_score < 0.3 else 'neutral'
        }
        
        print(f"🔄 Transferring call {call_sid} to live dashboard...")
        print(f"   Customer: {transfer_data['customer_name']}")
        print(f"   Phone: {from_number}")
        print(f"   Transcript length: {len(initial_transcript)} chars")
        print(f"   Detected sentiment: {sentiment_label} ({sentiment_score:.2f})")
        print(f"   Urgency: {urgency_level}")
        print(f"   Sending to: {hack25_url}")
        
        # Send directly to hack25 backend
        try:
            print(f"📤 POST {hack25_url}")
            print(f"   Data: call_id={call_sid}, customer={transfer_data['customer_name']}")
            response = requests.post(
                hack25_url,
                json=transfer_data,
                timeout=5
            )
            print(f"   Response status: {response.status_code}")
            if response.ok:
                result = response.json()
                print(f"   Response: {result.get('message', 'Success')}")
                print(f"   Call ID: {result.get('call_id', call_sid)}")
            else:
                print(f"   Response text: {response.text[:200]}")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection error: Cannot connect to hack25 backend at {hack25_url}")
            print(f"   Make sure hack25 backend is running on port 3002")
            response = None
        except Exception as e:
            print(f"   ❌ Error sending to hack25 backend: {e}")
            import traceback
            traceback.print_exc()
            response = None
        
        if response and response.ok:
            result = response.json()
            print(f"✅ Call routed to dashboard successfully!")
            print(f"   Dashboard Call ID: {result.get('call_id')}")
            print(f"   Assigned CSR: {result.get('assigned_csr', {}).get('name', 'Unknown') if isinstance(result.get('assigned_csr'), dict) else 'N/A'}")
            print(f"   Transfer stored in backend: {result.get('success', False)}")
            
            # Store transfer info (initialize call_recordings if needed)
            if call_sid not in call_recordings:
                call_recordings[call_sid] = {
                    'from': from_number,
                    'start_time': datetime.now().isoformat(),
                    'recordings': []
                }
            
            call_recordings[call_sid]['transferred_to_dashboard'] = True
            call_recordings[call_sid]['dashboard_call_id'] = result.get('call_id')
            call_recordings[call_sid]['assigned_csr'] = result.get('assigned_csr')
            call_recordings[call_sid]['sentiment_analysis'] = result.get('analysis', {
                'sentiment': {'label': sentiment_label, 'score': sentiment_score},
                'urgency': {'level': urgency_level, 'score': urgency_score}
            })
            
            return {
                'success': True,
                'dashboard_call_id': result.get('call_id'),
                'assigned_csr': result.get('assigned_csr'),
                'analysis': result.get('analysis', {
                    'sentiment': {'label': sentiment_label, 'score': sentiment_score},
                    'urgency': {'level': urgency_level, 'score': urgency_score}
                }),
                'message': 'Call routed to live dashboard'
            }
        else:
            print(f"❌ Failed to route call to HackUTD-1 dashboard")
            if response:
                print(f"   Status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            else:
                print(f"   No response received - backend may not be running")
            print(f"   Falling back to hack25 backend...")
            
            # Fallback: Send to hack25 backend
            try:
                hack25_url = "http://localhost:3002/api/calls/transfer"
                fallback_data = {
                    'call_id': call_sid,
                    'phone_number': from_number,
                    'customer_name': customer_info.get('name', 'Unknown') if customer_info else 'Unknown',
                    'customer_info': customer_info,
                    'customer_text': customer_text,
                    'initial_transcript': initial_transcript,
                    'sentiment': {'label': sentiment_label, 'score': sentiment_score},
                    'urgency': {'level': urgency_level, 'score': urgency_score},
                    'emotion': 'neutral'
                }
                
                print(f"📤 Sending call transfer to hack25 backend...")
                print(f"   URL: {hack25_url}")
                print(f"   Call ID: {call_sid}")
                print(f"   Customer: {fallback_data['customer_name']}")
                
                fallback_response = requests.post(hack25_url, json=fallback_data, timeout=5)
                if fallback_response.ok:
                    print(f"✅ Call transfer sent to hack25 backend successfully!")
                    fallback_result = fallback_response.json()
                    
                    # Store transfer info
                    if call_sid not in call_recordings:
                        call_recordings[call_sid] = {
                            'from': from_number,
                            'start_time': datetime.now().isoformat(),
                            'recordings': []
                        }
                    
                    call_recordings[call_sid]['transferred_to_dashboard'] = True
                    call_recordings[call_sid]['dashboard_call_id'] = fallback_result.get('call_id', call_sid)
                    call_recordings[call_sid]['transferred_via'] = 'hack25_backend'
                    
                    return {
                        'success': True,
                        'dashboard_call_id': fallback_result.get('call_id', call_sid),
                        'message': 'Call routed to hack25 backend',
                        'via': 'hack25_backend'
                    }
            except Exception as fallback_error:
                print(f"⚠️ Fallback to hack25 backend error: {fallback_error}")
            
            return {
                'success': False,
                'error': f'Dashboard API returned {response.status_code if response else "no response"}',
                'message': 'Failed to route call to dashboard'
            }
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to HackUTD-1 dashboard API at {dashboard_api_url}")
        print(f"   Falling back to hack25 backend for call transfer...")
        
        # Fallback: Send to hack25 backend instead
        try:
            hack25_url = "http://localhost:3002/api/calls/transfer"
            fallback_data = {
                'call_id': call_sid,
                'phone_number': from_number,
                'customer_name': customer_info.get('name', 'Unknown') if customer_info else 'Unknown',
                'customer_info': customer_info,
                'customer_text': customer_text,
                'initial_transcript': initial_transcript,
                'sentiment': {'label': 'neutral', 'score': 0.5},  # Will be analyzed by backend if needed
                'urgency': {'level': 'MEDIUM', 'score': 0.5},
                'emotion': 'neutral'
            }
            
            fallback_response = requests.post(hack25_url, json=fallback_data, timeout=5)
            if fallback_response.ok:
                print(f"✅ Call transfer sent to hack25 backend successfully!")
                result = fallback_response.json()
                
                # Store transfer info
                if call_sid not in call_recordings:
                    call_recordings[call_sid] = {
                        'from': from_number,
                        'start_time': datetime.now().isoformat(),
                        'recordings': []
                    }
                
                call_recordings[call_sid]['transferred_to_dashboard'] = True
                call_recordings[call_sid]['dashboard_call_id'] = result.get('call_id', call_sid)
                call_recordings[call_sid]['transferred_via'] = 'hack25_backend'
                
                return {
                    'success': True,
                    'dashboard_call_id': result.get('call_id', call_sid),
                    'message': 'Call routed to hack25 backend',
                    'via': 'hack25_backend'
                }
            else:
                print(f"⚠️ Fallback to hack25 backend also failed: {fallback_response.status_code}")
        except Exception as fallback_error:
            print(f"⚠️ Fallback to hack25 backend error: {fallback_error}")
        
        return {
            'success': False,
            'error': 'Dashboard API not available',
            'message': 'Live dashboard is not running'
        }
    except Exception as e:
        print(f"❌ Error routing call to dashboard: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'message': 'Error during transfer'
        }

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
    
    dial = Dial(timeout=60, caller_id=from_number, action='/dial-status', method='POST')
    dial.number(HUMAN_AGENT_PHONE)
    resp.append(dial)
    
    # Don't say "no agents available" - let the action URL handle it
    # resp.say("Sorry, no agents are available right now.", 
    #          voice='Polly.Joanna', 
    #          language='en-US')
    
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
        
        # Trigger call completion when recording finishes (call has ended)
        print(f"📋 Recording completed - triggering call completion logic...")
        try:
            trigger_call_completion(call_sid)
        except Exception as e:
            print(f"⚠️ Could not trigger call completion from recording callback: {e}")
            import traceback
            traceback.print_exc()
    
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
        try:
            analysis_result = analyze_tonality_with_nemo(filename)
            
            # Convert numpy arrays to native types before storing
            analysis_result_clean = convert_numpy_to_native(analysis_result)
            
            # Store analysis with call data
            if call_sid in call_recordings:
                call_recordings[call_sid]['tonality_analysis'] = analysis_result_clean
                
                # Save analysis to JSON file for persistence
                save_call_analysis(call_sid, call_recordings[call_sid])
                
                # Print detailed analysis to terminal
                print_analysis_to_terminal(call_sid, call_recordings[call_sid], analysis_result_clean)
        except Exception as e:
            print(f"⚠️ Error during tonality analysis: {e}")
            import traceback
            traceback.print_exc()
            # Continue even if analysis fails - we can still send call data
        
        return filename
    else:
        print(f"❌ Failed to download recording: {response.status_code}")
        return None

def calculate_csat_from_sentiment(sentiment_data, tonality_data=None):
    """
    Calculate CSat score (1-5) from sentiment analysis and tonality data.
    
    Mapping:
    - Positive sentiment → 4-5 (higher if very positive)
    - Neutral sentiment → 3
    - Negative sentiment → 1-2 (lower if very negative)
    
    Also considers emotion from tonality analysis if available.
    
    Args:
        sentiment_data: Dict with sentiment info (from dashboard API or text analysis)
        tonality_data: Optional dict with tonality/emotion analysis from audio
    
    Returns:
        int: CSat score from 1-5
    """
    # Default to neutral if no data
    if not sentiment_data and not tonality_data:
        return 3
    
    # Extract sentiment label and score
    sentiment_label = 'neutral'
    sentiment_score = 0.5
    
    if sentiment_data:
        if isinstance(sentiment_data, dict):
            sentiment_label = sentiment_data.get('label', 'neutral').lower()
            sentiment_score = sentiment_data.get('score', 0.5)
        elif isinstance(sentiment_data, str):
            sentiment_label = sentiment_data.lower()
    
    # Extract emotion from tonality if available
    emotion = None
    if tonality_data:
        emotion = tonality_data.get('overall_tone', '').lower()
        predicted_emotions = tonality_data.get('predicted_emotions', [])
        if predicted_emotions:
            emotion = predicted_emotions[0].lower()
    
    # Base CSat calculation from sentiment
    if sentiment_label == 'positive' or sentiment_label == 'very_positive':
        # Positive sentiment: 4-5
        if sentiment_score > 0.7 or emotion in ['excited', 'engaged', 'calm', 'relaxed']:
            return 5
        else:
            return 4
    elif sentiment_label == 'negative' or sentiment_label == 'very_negative':
        # Negative sentiment: 1-2
        if sentiment_score < 0.3 or emotion in ['angry', 'anxious']:
            return 1
        else:
            return 2
    else:
        # Neutral sentiment: 3, but adjust based on emotion
        if emotion == 'angry':
            return 2
        elif emotion in ['excited', 'engaged', 'calm']:
            return 4
        elif emotion == 'anxious':
            return 2
        else:
            return 3

def convert_numpy_to_native(obj):
    """Recursively convert numpy arrays and scalars to native Python types for JSON serialization."""
    import numpy as np
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_native(item) for item in obj]
    else:
        return obj

def save_call_analysis(call_sid, call_data):
    """Save call analysis to JSON file for persistence."""
    try:
        # Convert numpy arrays to native Python types
        call_data_serializable = convert_numpy_to_native(call_data)
        
        analysis_file = f"{ANALYSIS_DIR}/{call_sid}.json"
        with open(analysis_file, 'w') as f:
            json.dump(call_data_serializable, f, indent=2)
        print(f"💾 Analysis saved to: {analysis_file}")
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")
        import traceback
        traceback.print_exc()

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
            
            # Convert numpy arrays to native types
            analysis_result_clean = convert_numpy_to_native(analysis_result)
            call_data['tonality_analysis'] = analysis_result_clean
            
            # Save the analysis
            save_call_analysis(call_sid, call_data)
            
            # Update in-memory cache
            if call_sid in call_recordings:
                call_recordings[call_sid] = call_data
        except Exception as e:
            print(f"⚠️ Error analyzing call: {e}")
            import traceback
            traceback.print_exc()
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
        tempo_result = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo_result[0]) if isinstance(tempo_result, tuple) else float(tempo_result)
        
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
        # ADJUSTED THRESHOLDS: More conservative to reduce false positives
        emotions = []
        
        # Anger detection: MUCH STRICTER - requires very high pitch variance + high arousal + elevated pitch
        # Increased thresholds significantly to avoid false positives
        if pitch_variance > 250000 and avg_zcr > 0.20 and avg_pitch > 180 and avg_energy > 0.06:
            emotions.append('angry')
        # Excited: high energy + high pitch + high variance
        elif avg_pitch > 220 and pitch_variance > 2000 and avg_energy > 0.06:
            emotions.append('excited')
        # Anxious/stressed: high pitch variance but lower energy
        elif avg_pitch > 220 and pitch_variance > 2000:
            emotions.append('anxious')
        # Calm: low pitch + low energy + low variance
        elif avg_pitch < 100 and avg_energy < 0.03:
            emotions.append('calm' if pitch_variance < 500 else 'relaxed')
        # Engaged/active: moderate energy and pitch (normal conversation)
        elif avg_energy > 0.04 and avg_zcr > 0.09 and avg_pitch > 120:
            emotions.append('engaged' if pitch_variance > 1500 else 'conversational')
        # Default to neutral for most cases
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

@app.route("/api/calls", methods=['GET'])
def get_calls_with_csat():
    """
    Get all calls with calculated CSat scores for the sentiment dashboard.
    Returns call data with sentiment, CSat, and summary.
    """
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
    
    # Build call list with CSat scores
    calls = []
    for call_sid, data in all_recordings.items():
        # Get customer info
        from_number = data.get('from', 'Unknown')
        customer = get_customer_by_phone(from_number)
        caller_name = customer.get('name', 'Unknown') if customer else 'Unknown'
        
        # Get duration
        recordings = data.get('recordings', [])
        duration_seconds = int(recordings[0].get('duration', 0)) if recordings else 0
        duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds > 0 else '0:00'
        
        # Get sentiment data
        sentiment_analysis = data.get('sentiment_analysis', {})
        tonality_data = data.get('tonality_analysis', {})
        
        # Extract sentiment label and data structure
        sentiment_label = 'neutral'
        sentiment_for_csat = None
        
        if sentiment_analysis:
            if isinstance(sentiment_analysis, dict):
                # Try different possible structures
                if 'sentiment' in sentiment_analysis:
                    sentiment_for_csat = sentiment_analysis.get('sentiment', {})
                    sentiment_label = sentiment_for_csat.get('label', 'neutral')
                elif 'label' in sentiment_analysis:
                    sentiment_for_csat = sentiment_analysis
                    sentiment_label = sentiment_analysis.get('label', 'neutral')
                else:
                    # Use the whole dict as sentiment data
                    sentiment_for_csat = sentiment_analysis
                    sentiment_label = sentiment_analysis.get('label', 'neutral')
            elif isinstance(sentiment_analysis, str):
                sentiment_label = sentiment_analysis
                sentiment_for_csat = sentiment_analysis
        
        # Calculate CSat score
        csat_score = calculate_csat_from_sentiment(sentiment_for_csat, tonality_data)
        
        # Generate summary from conversation history or sentiment
        summary = 'Call completed'
        if call_sid in conversation_history:
            # Try to extract key info from conversation
            user_messages = [msg.get('content', '') for msg in conversation_history[call_sid] if msg.get('role') == 'user']
            if user_messages:
                first_message = user_messages[0][:50] if user_messages[0] else ''
                summary = f"{first_message}..." if len(user_messages[0]) > 50 else first_message
        
        # Add call to list
        calls.append({
            'id': call_sid,
            'caller': caller_name,
            'duration': duration_str,
            'sentiment': sentiment_label,
            'csat': csat_score,
            'summary': summary,
            'phone': from_number,
            'start_time': data.get('start_time', ''),
            'transferred': data.get('transferred_to_dashboard', False)
        })
    
    # Sort by start time (most recent first)
    calls.sort(key=lambda x: x.get('start_time', ''), reverse=True)
    
    return jsonify({
        'calls': calls,
        'count': len(calls)
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

def trigger_call_completion(call_sid):
    """
    Internal function to trigger call completion logic.
    Can be called from status callback or recording callback.
    """
    print(f"📋 ========== TRIGGERING CALL COMPLETION ==========")
    print(f"   Call SID: {call_sid}")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"==================================================")
    
    # Import the completion logic
    process_call_completion(call_sid)

def process_call_completion(call_sid):
    """
    Process call completion and send data to sentiment dashboard.
    This is the core logic extracted from end_call.
    """
    print(f"📋 Processing call completion and sending to sentiment dashboard...")
    
    # IMPORTANT: Extract conversation summary BEFORE deleting conversation_history
    conversation_summary = None
    if call_sid in conversation_history:
        user_messages = [msg.get('content', '') for msg in conversation_history[call_sid] if msg.get('role') == 'user']
        if user_messages:
            first_message = user_messages[0][:50] if user_messages[0] else ''
            conversation_summary = f"{first_message}..." if len(user_messages[0]) > 50 else first_message
    
    # Check if call was transferred to dashboard
    was_transferred = call_sid in call_recordings and call_recordings[call_sid].get('transferred_to_dashboard', False)
    
    # Continue with the rest of the completion logic...
    
    if was_transferred:
        print(f"ℹ️ Call was transferred to dashboard")
        print(f"   Dashboard should handle call completion via /api/calls/transferred/<call_id>/end")
        print(f"   If dashboard doesn't end the call, sending fallback data...")
        
        # Fallback: If dashboard doesn't end the call properly, send data anyway
        # This ensures we don't lose call data if user hangs up without clicking "End Call"
        dashboard_call_id = call_recordings[call_sid].get('dashboard_call_id', call_sid)
        
        # Try to get the call from the backend to see if it was already ended
        try:
            check_response = requests.get(f'http://localhost:3002/api/calls/transferred/{dashboard_call_id}', timeout=2)
            if check_response.ok:
                result = check_response.json()
                transferred_call = result.get('call', {})
                if transferred_call.get('status') == 'ended':
                    print(f"   ✅ Call already ended by dashboard - skipping duplicate")
                    return jsonify({'status': 'ok', 'message': 'Call already ended by dashboard'})
                else:
                    print(f"   ℹ️ Call status: {transferred_call.get('status', 'unknown')} - sending fallback data")
        except Exception as check_error:
            print(f"   ℹ️ Could not check call status (will send fallback): {check_error}")
            # Continue with fallback
        
        # Fallback: Send data anyway to ensure it's recorded
        print(f"   📤 Sending fallback call data to sentiment dashboard...")
        try:
            from_number = call_recordings.get(call_sid, {}).get('from', 'Unknown')
            customer = get_customer_by_phone(from_number)
            customer_name = customer.get('name', 'Unknown') if customer and isinstance(customer, dict) else 'Unknown'
            
            # Get sentiment from transfer data
            sentiment_analysis = call_recordings.get(call_sid, {}).get('sentiment_analysis', {})
            sentiment_label = 'neutral'
            if isinstance(sentiment_analysis, dict):
                if 'sentiment' in sentiment_analysis:
                    sentiment_label = sentiment_analysis.get('sentiment', {}).get('label', 'neutral')
                elif 'label' in sentiment_analysis:
                    sentiment_label = sentiment_analysis.get('label', 'neutral')
            
            # Calculate CSat
            csat_score = calculate_csat_from_sentiment(sentiment_analysis, {})
            
            # Get duration
            recordings = call_recordings.get(call_sid, {}).get('recordings', [])
            duration_seconds = int(recordings[0].get('duration', 0)) if recordings else 0
            duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds > 0 else '0:00'
            
            # Generate summary
            summary = conversation_summary if conversation_summary else f"Call from {customer_name} (transferred)"
            
            fallback_data = {
                'call_id': dashboard_call_id,
                'name': customer_name,
                'phone': from_number,
                'sentiment': sentiment_label,
                'csat': csat_score,
                'summary': summary,
                'duration': duration_str,
                'start_time': call_recordings.get(call_sid, {}).get('start_time', datetime.now().isoformat()),
                'end_time': datetime.now().isoformat(),
                'source': 'voice_assistant_transferred'
            }
            
            print(f"   📤 POST http://localhost:3002/api/calls/complete")
            print(f"   📦 Data: {fallback_data}")
            response = requests.post('http://localhost:3002/api/calls/complete', json=fallback_data, timeout=10)
            if response.ok:
                result = response.json()
                print(f"   ✅ Fallback call data sent successfully!")
                print(f"   Response: {result.get('message', 'Success')}")
                print(f"   Total calls: {result.get('total_calls', 'N/A')}")
            else:
                print(f"   ⚠️ Fallback failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ⚠️ Fallback error: {e}")
            import traceback
            traceback.print_exc()
        
        return  # Exit early for transferred calls
    else:
        # Call was NOT transferred - handle normally
        print(f"ℹ️ Call was NOT transferred - sending data directly to sentiment dashboard")
        # Call was handled by agent - send data to sentiment dashboard
        # Give analysis a moment to complete if it's still running
        import time
        time.sleep(2)  # Wait 2 seconds for any ongoing analysis to complete
        
        # Ensure we have call_recordings entry
        if call_sid not in call_recordings:
            call_recordings[call_sid] = {
                'from': request.form.get('From', 'Unknown'),
                'start_time': datetime.now().isoformat(),
                'recordings': []
            }
        
        try:
            from_number = call_recordings.get(call_sid, {}).get('from', 'Unknown')
            customer = get_customer_by_phone(from_number)
            # Ensure customer is a dict
            if customer and not isinstance(customer, dict):
                customer = None
            customer_name = customer.get('name', 'Unknown') if customer else 'Unknown'
            
            # Get sentiment data (may not exist if call wasn't transferred)
            sentiment_analysis = call_recordings.get(call_sid, {}).get('sentiment_analysis', {})
            tonality_data = call_recordings.get(call_sid, {}).get('tonality_analysis', {})
            
            # If no sentiment analysis, try to analyze from conversation
            if not sentiment_analysis and call_sid in conversation_history:
                # Simple sentiment from conversation text
                all_user_text = ' '.join([msg.get('content', '') for msg in conversation_history[call_sid] if msg.get('role') == 'user'])
                if all_user_text:
                    # Simple heuristic sentiment
                    negative_words = ['bad', 'slow', 'dropped', 'terrible', 'awful', 'horrible', 'frustrated', 
                                      'frustrating', 'issue', 'problem', 'broken', 'down', 'outage', 'complaint']
                    positive_words = ['good', 'great', 'love', 'excellent', 'amazing', 'wonderful', 'thanks', 'thank you']
                    
                    text_lower = all_user_text.lower()
                    negative_count = sum(1 for word in negative_words if word in text_lower)
                    positive_count = sum(1 for word in positive_words if word in text_lower)
                    
                    if negative_count > positive_count:
                        sentiment_analysis = {'label': 'negative', 'score': max(0.1, 0.5 - (negative_count * 0.1))}
                    elif positive_count > negative_count:
                        sentiment_analysis = {'label': 'positive', 'score': min(0.95, 0.5 + (positive_count * 0.1))}
                    else:
                        sentiment_analysis = {'label': 'neutral', 'score': 0.5}
            
            # Extract sentiment
            sentiment_label = 'neutral'
            sentiment_for_csat = None
            
            if sentiment_analysis:
                if isinstance(sentiment_analysis, dict):
                    if 'sentiment' in sentiment_analysis:
                        sentiment_for_csat = sentiment_analysis.get('sentiment', {})
                        sentiment_label = sentiment_for_csat.get('label', 'neutral')
                    elif 'label' in sentiment_analysis:
                        sentiment_for_csat = sentiment_analysis
                        sentiment_label = sentiment_analysis.get('label', 'neutral')
                    else:
                        sentiment_for_csat = sentiment_analysis
                        sentiment_label = sentiment_analysis.get('label', 'neutral')
                elif isinstance(sentiment_analysis, str):
                    sentiment_label = sentiment_analysis
                    sentiment_for_csat = sentiment_analysis
            
            # Calculate CSat
            csat_score = calculate_csat_from_sentiment(sentiment_for_csat, tonality_data)
            
            # Get duration
            recordings = call_recordings.get(call_sid, {}).get('recordings', [])
            duration_seconds = int(recordings[0].get('duration', 0)) if recordings else 0
            duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds > 0 else '0:00'
            
            # Use pre-extracted summary or generate fallback
            summary = conversation_summary if conversation_summary else f"Call from {customer_name}"
            if not summary or summary == 'Call completed':
                summary = f"Call from {customer_name}"
            
            # Send to sentiment dashboard
            dashboard_api_url = 'http://localhost:3002/api/calls/complete'
            call_data = {
                'call_id': call_sid,
                'name': customer_name,
                'phone': from_number,
                'sentiment': sentiment_label,
                'csat': csat_score,
                'summary': summary,
                'duration': duration_str,
                'start_time': call_recordings.get(call_sid, {}).get('start_time', datetime.now().isoformat()),
                'end_time': datetime.now().isoformat(),
                'source': 'voice_assistant'
            }
            
            print(f"📤 Sending call data to sentiment dashboard...")
            print(f"   Customer: {customer_name}")
            print(f"   Sentiment: {sentiment_label}")
            print(f"   CSat: {csat_score}/5")
            print(f"   Duration: {duration_str}")
            
            # Always send call data - retry if needed
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"📤 Attempt {attempt + 1}/{max_retries}: Sending call data to sentiment dashboard...")
                    print(f"   URL: {dashboard_api_url}")
                    print(f"   Data: call_id={call_data.get('call_id')}, name={call_data.get('name')}, sentiment={call_data.get('sentiment')}, csat={call_data.get('csat')}")
                    response = requests.post(dashboard_api_url, json=call_data, timeout=10)
                    print(f"   Response status: {response.status_code}")
                    if response.ok:
                        result = response.json()
                        print(f"✅ Call data sent to sentiment dashboard successfully!")
                        print(f"   Response: {result.get('message', 'Success')}")
                        print(f"   Call ID: {result.get('call_id', call_sid)}")
                        print(f"   Total calls stored: {result.get('total_calls', 'N/A')}")
                        break  # Success, exit retry loop
                    else:
                        error_text = response.text
                        print(f"⚠️ Attempt {attempt + 1} failed: {response.status_code}")
                        print(f"   Error: {error_text[:500]}")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Wait before retry
                except requests.exceptions.ConnectionError:
                    print(f"❌ Attempt {attempt + 1}: Cannot connect to sentiment dashboard at {dashboard_api_url}")
                    print(f"   Make sure hack25 backend is running on port 3002")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait longer before retry
                except Exception as e:
                    print(f"❌ Attempt {attempt + 1}: Error sending call data: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        import traceback
                        traceback.print_exc()
            
            # Verify the data was stored by checking the API
            try:
                verify_response = requests.get('http://localhost:3002/api/calls', timeout=5)
                if verify_response.ok:
                    stored_calls = verify_response.json().get('calls', [])
                    found = any(c.get('id') == call_sid for c in stored_calls)
                    if found:
                        print(f"✅ Verified: Call data is stored in sentiment dashboard")
                    else:
                        print(f"⚠️ Warning: Call data may not be stored (call not found in API response)")
            except Exception as e:
                print(f"⚠️ Could not verify call data storage: {e}")
        
        except Exception as e:
            print(f"❌ Error preparing call data: {e}")
            import traceback
            traceback.print_exc()
            # Try to send basic call data even if extraction fails
            print(f"🔄 Attempting to send fallback call data...")
            try:
                from_number = call_recordings.get(call_sid, {}).get('from', request.form.get('From', 'Unknown'))
                customer = get_customer_by_phone(from_number)
                customer_name = customer.get('name', 'Unknown') if customer else 'Unknown'
                
                recordings = call_recordings.get(call_sid, {}).get('recordings', [])
                duration_seconds = int(recordings[0].get('duration', 0)) if recordings else 0
                duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds > 0 else '0:00'
                
                fallback_data = {
                    'call_id': call_sid,
                    'name': customer_name,
                    'phone': from_number,
                    'sentiment': 'neutral',
                    'csat': 3,
                    'summary': f'Call from {customer_name}',
                    'duration': duration_str,
                    'start_time': call_recordings.get(call_sid, {}).get('start_time', datetime.now().isoformat()),
                    'end_time': datetime.now().isoformat(),
                    'source': 'voice_assistant'
                }
                
                print(f"📤 Sending fallback call data: {customer_name}")
                for attempt in range(3):
                    try:
                        response = requests.post('http://localhost:3002/api/calls/complete', json=fallback_data, timeout=10)
                        if response.ok:
                            print(f"✅ Sent fallback call data to sentiment dashboard (attempt {attempt + 1})")
                            break
                        else:
                            print(f"⚠️ Fallback attempt {attempt + 1} failed: {response.status_code}")
                            if attempt < 2:
                                time.sleep(1)
                    except Exception as retry_error:
                        print(f"⚠️ Fallback attempt {attempt + 1} error: {retry_error}")
                        if attempt < 2:
                            time.sleep(2)
            except Exception as fallback_error:
                print(f"❌ Failed to send fallback call data: {fallback_error}")
                import traceback
                traceback.print_exc()
    
    # Cleanup conversation history but keep recordings
    if call_sid in conversation_history:
        print(f"Conversation had {len(conversation_history[call_sid])} exchanges")
        del conversation_history[call_sid]
    
    # Cleanup customer cache
    if call_sid in customer_cache:
        del customer_cache[call_sid]
    
    print(f"✅ Call completion processing finished for {call_sid}")

@app.route("/end-call", methods=['GET', 'POST'])
def end_call():
    """Handle call ending and cleanup - called by Twilio status callback."""
    # Get call_sid from form (POST) or args (GET)
    call_sid = request.form.get('CallSid') or request.args.get('CallSid') or 'unknown'
    
    print(f"📋 ========== CALL ENDED (STATUS CALLBACK) ==========")
    print(f"   Call SID: {call_sid}")
    print(f"   Time: {datetime.now().isoformat()}")
    print(f"   Call Status: {request.form.get('CallStatus', request.args.get('CallStatus', 'unknown'))}")
    print(f"   Form data keys: {list(request.form.keys())}")
    print(f"   Args keys: {list(request.args.keys())}")
    print(f"======================================================")
    
    # Process the call completion
    process_call_completion(call_sid)
    
    return jsonify({'status': 'ok', 'message': 'Call ended successfully'})


@app.route("/dial-status", methods=['POST'])
def dial_status():
    """
    Handle the status callback from a Dial action.
    This is called when a Dial completes (successfully or not).
    """
    from twilio.twiml.voice_response import VoiceResponse
    
    resp = VoiceResponse()
    call_sid = request.form.get('CallSid', 'unknown')
    dial_call_status = request.form.get('DialCallStatus', 'unknown')
    dial_call_duration = request.form.get('DialCallDuration', '0')
    
    print(f"📞 Dial status callback for call {call_sid}")
    print(f"   Dial status: {dial_call_status}")
    print(f"   Duration: {dial_call_duration} seconds")
    
    # DialCallStatus can be: completed, answered, busy, no-answer, failed, canceled
    if dial_call_status in ['completed', 'answered']:
        # Call was successfully connected
        print(f"✅ Call successfully transferred to human agent")
        # Don't say anything, just hang up or let the call continue
        resp.say("You have been connected to a specialist.", voice='Polly.Joanna', language='en-US')
    elif dial_call_status == 'busy':
        print(f"⚠️ Human agent line is busy")
        resp.say("I'm sorry, all our specialists are currently busy. Please try again in a few moments, or I can continue helping you.", 
                 voice='Polly.Joanna', language='en-US')
        resp.redirect('/listen')
    elif dial_call_status == 'no-answer':
        print(f"⚠️ Human agent did not answer")
        resp.say("I'm sorry, no one is available to take your call right now. Would you like me to continue helping you, or would you prefer to call back later?", 
                 voice='Polly.Joanna', language='en-US')
        resp.redirect('/listen')
    elif dial_call_status == 'failed':
        print(f"❌ Dial failed - check phone number configuration")
        resp.say("I'm having trouble connecting you right now. Let me continue helping you instead.", 
                 voice='Polly.Joanna', language='en-US')
        resp.redirect('/listen')
    else:
        # canceled or unknown status
        print(f"⚠️ Dial status: {dial_call_status}")
        resp.say("Let me continue helping you.", voice='Polly.Joanna', language='en-US')
        resp.redirect('/listen')
    
    return str(resp), 200, {'Content-Type': 'text/xml'}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Conversational AI Voice Server on port {port}")
    print(f"📞 Ready to handle calls!")
    app.run(host="0.0.0.0", port=port, debug=False)
