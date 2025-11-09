import sys
import os
from pathlib import Path
from datetime import datetime
import importlib.util

# Get the parent directory (hackutd-1)
current_dir = Path(__file__).parent
parent_dir = current_dir.parent

# Change to parent directory for imports
os.chdir(parent_dir)

# Add parent directory to path for src imports
sys.path.insert(0, str(parent_dir))

# Import RealTimeSentimentAnalyzer from scripts
realtime_spec = importlib.util.spec_from_file_location("realtime_analyzer", parent_dir / "scripts" / "realtime_analyzer.py")
realtime_module = importlib.util.module_from_spec(realtime_spec)
realtime_spec.loader.exec_module(realtime_module)
RealTimeSentimentAnalyzer = realtime_module.RealTimeSentimentAnalyzer

# Import from api directory (need to add it back to path after chdir)
sys.path.insert(0, str(current_dir))
from csr_router import CSRRouter
from customer_db import CustomerDB
from call_manager import CallManager

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Enable CORS for React frontend - allow all origins and methods
CORS(app, 
     resources={r"/api/*": {
         "origins": "*",
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
     }},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

socketio = SocketIO(app, 
                   cors_allowed_origins="*",  # Allow all origins
                   cors_credentials=False,  # Disable credentials to avoid CORS issues
                   async_mode='threading',
                   logger=False,
                   engineio_logger=False,
                   allow_upgrades=True,
                   transports=['polling', 'websocket'])

# Add CORS headers to all responses (backup in case flask-cors doesn't catch everything)
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    return response

# Initialize components
analyzer = RealTimeSentimentAnalyzer()
csr_router = CSRRouter()
customer_db = CustomerDB()
call_manager = CallManager()

# Store active calls (legacy - for backward compatibility)
active_calls = {}


@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'status': 'ok', 'message': 'API is running'})


@app.route('/api/analyze', methods=['POST', 'OPTIONS'])
def analyze_transcript():
    """Analyze a transcript and return sentiment analysis"""
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json or {}
    
    customer_text = data.get('customer_text', '')
    agent_text = data.get('agent_text', '')
    transcript_id = data.get('transcript_id', f"call_{datetime.now().timestamp()}")
    
    if not customer_text:
        return jsonify({'error': 'customer_text is required'}), 400
    
    # Analyze transcript
    result = analyzer.analyze_transcript({
        'transcript_id': transcript_id,
        'customer_text': customer_text,
        'agent_text': agent_text,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'transcript_id': result['transcript_id'],
        'sentiment': result['sentiment'],
        'emotion': result['emotion'],
        'urgency': result['urgency'],
        'routing': result['routing'],
        'keywords': result.get('keywords', []),
        'issue_category': result.get('issue_category', 'general'),
        'timestamp': result['timestamp']
    })


@app.route('/api/customer/<phone>', methods=['GET', 'OPTIONS'])
def get_customer(phone):
    """Get customer information by phone number"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        print(f"Looking up customer with phone: {phone}")
        customer = customer_db.get_customer(phone)
        
        if not customer:
            print(f"Customer not found for phone: {phone}")
            return jsonify({'error': 'Customer not found', 'phone': phone}), 404
        
        print(f"Found customer: {customer.get('name', 'Unknown')}")
        return jsonify(customer)
    except Exception as e:
        print(f"Error in get_customer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'phone': phone}), 500


@app.route('/api/csrs', methods=['GET', 'OPTIONS'])
def get_csrs():
    """Get list of available CSRs"""
    if request.method == 'OPTIONS':
        return '', 200
    csrs = csr_router.get_all_csrs()
    return jsonify(csrs)


@app.route('/api/route', methods=['POST', 'OPTIONS'])
def route_call():
    """Route a call to the appropriate CSR based on analysis"""
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json or {}
    
    customer_text = data.get('customer_text', '')
    phone_number = data.get('phone_number')
    call_id = data.get('call_id', f"call_{datetime.now().timestamp()}")
    initial_transcript = data.get('initial_transcript', customer_text)
    
    if not customer_text:
        return jsonify({'error': 'customer_text is required'}), 400
    
    # Analyze transcript
    analysis = analyzer.analyze_transcript({
        'transcript_id': call_id,
        'customer_text': customer_text,
        'timestamp': datetime.now().isoformat()
    })
    
    # Get customer info if phone provided
    customer_info = None
    if phone_number:
        customer_info = customer_db.get_customer(phone_number)
    
    # Route to appropriate CSR
    csr = csr_router.route_call(
        sentiment_score=analysis['sentiment']['score'],
        urgency_score=analysis['urgency']['score'],
        emotion=analysis['emotion'],
        issue_category=analysis.get('issue_category', 'general'),
        customer_info=customer_info
    )
    
    # Create incoming call notification (simulates call being routed to human responder)
    new_call_id = call_manager.create_incoming_call(
        phone_number=phone_number or 'Unknown',
        initial_transcript=initial_transcript,
        initial_analysis=analysis,
        customer_info=customer_info
    )
    
    # Broadcast new call notification via WebSocket
    call_summary = call_manager.get_call_summary(new_call_id)
    if call_summary:
        socketio.emit('new_call', call_summary, namespace='/')
    
    # Store active call (legacy support)
    active_calls[call_id] = {
        'call_id': call_id,
        'phone_number': phone_number,
        'customer_info': customer_info,
        'assigned_csr': csr,
        'transcript': [],
        'sentiment_history': [],
        'start_time': datetime.now().isoformat(),
        'current_sentiment': analysis['sentiment']
    }
    
    return jsonify({
        'call_id': new_call_id,  # Return the actual call_id from call_manager
        'assigned_csr': csr,
        'analysis': analysis,
        'customer_info': customer_info,
        'notification_created': True
    })


@app.route('/api/calls/pending', methods=['GET', 'OPTIONS'])
def get_pending_calls():
    """Get all pending calls waiting to be accepted"""
    if request.method == 'OPTIONS':
        return '', 200
    pending = call_manager.get_pending_calls()
    summaries = [call_manager.get_call_summary(call['call_id']) for call in pending]
    return jsonify(summaries)


@app.route('/api/calls/<call_id>/accept', methods=['POST', 'OPTIONS'])
def accept_call(call_id):
    """Accept a pending call"""
    if request.method == 'OPTIONS':
        return '', 200
    call = call_manager.accept_call(call_id)
    
    if not call:
        return jsonify({'error': 'Call not found or already accepted'}), 404
    
    return jsonify({
        'call_id': call.get('call_id'),
        'phone_number': call.get('phone_number', 'Unknown'),
        'customer_info': call.get('customer_info'),
        'initial_transcript': call.get('initial_transcript', ''),
        'initial_analysis': call.get('initial_analysis'),
        'transcript': call.get('transcript', []),
        'sentiment_history': call.get('sentiment_history', [])
    })


@app.route('/api/calls/<call_id>/transcript', methods=['POST', 'OPTIONS'])
def add_transcript_chunk(call_id):
    """Add a real-time transcript chunk from speech-to-text"""
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json or {}
    
    speaker = data.get('speaker', 'customer')
    text = data.get('text', '')
    is_partial = data.get('is_partial', False)
    
    if not text:
        return jsonify({'error': 'text is required'}), 400
    
    # Analyze if it's customer text (and not partial)
    # IMPORTANT: Only analyze customer text, never agent/CSR text
    analysis = None
    if speaker == 'customer' and not is_partial:
        analysis_result = analyzer.analyze_transcript({
            'transcript_id': call_id,
            'customer_text': text,
            'timestamp': datetime.now().isoformat()
        })
        analysis = {
            'sentiment': analysis_result['sentiment'],
            'emotion': analysis_result['emotion'],
            'urgency': analysis_result['urgency']
        }
    
    # Add to call manager
    success = call_manager.add_transcript_chunk(call_id, speaker, text, analysis)
    
    if not success:
        return jsonify({'error': 'Call not found or not active'}), 404
    
    # Emit real-time update via WebSocket
    socketio.emit('transcript_chunk', {
        'call_id': call_id,
        'speaker': speaker,
        'text': text,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat(),
        'is_partial': is_partial
    }, room=call_id, namespace='/')
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })


@app.route('/api/call/<call_id>', methods=['GET', 'OPTIONS'])
def get_call_status(call_id):
    """Get current status of an active call"""
    if request.method == 'OPTIONS':
        return '', 200
    
    # Try call_manager first
    call = call_manager.get_active_call(call_id)
    if call:
        return jsonify({
            'call_id': call['call_id'],
            'phone_number': call['phone_number'],
            'customer_info': call.get('customer_info'),
            'transcript': call['transcript'],
            'sentiment_history': call['sentiment_history'],
            'current_sentiment': call.get('initial_analysis', {}).get('sentiment', {})
        })
    
    # Fallback to legacy active_calls
    if call_id not in active_calls:
        return jsonify({'error': 'Call not found'}), 404
    
    call_data = active_calls[call_id]
    
    # Build sentiment history
    sentiment_history = []
    if call_data.get('sentiment_history'):
        sentiment_history = call_data['sentiment_history']
    
    # Calculate sentiment change
    if sentiment_history:
        initial_sentiment = sentiment_history[0]['sentiment']['score'] if sentiment_history else 0
        current_sentiment = sentiment_history[-1]['sentiment']['score'] if sentiment_history else 0
        sentiment_change = current_sentiment - initial_sentiment
    else:
        sentiment_change = 0
    
    return jsonify({
        'call_id': call_id,
        'assigned_csr': call_data['assigned_csr'],
        'customer_info': call_data['customer_info'],
        'transcript': call_data['transcript'],
        'current_sentiment': call_data['current_sentiment'],
        'sentiment_history': sentiment_history,
        'sentiment_change': sentiment_change,
        'start_time': call_data['start_time']
    })


@socketio.on('join_call')
def handle_join_call(data):
    """Join a WebSocket room for a specific call"""
    call_id = data.get('call_id')
    if call_id:
        socketio.enter_room(request.sid, call_id)
        emit('joined', {'call_id': call_id, 'status': 'connected'})
        
        # Send current call state to the newly joined client
        call = call_manager.get_active_call(call_id)
        if call:
            emit('call_state', {
                'call_id': call_id,
                'transcript': call['transcript'],
                'sentiment_history': call['sentiment_history']
            })


@socketio.on('new_call_created')
def handle_new_call_created(data):
    """Broadcast new call to all connected clients"""
    call_id = data.get('call_id')
    if call_id:
        summary = call_manager.get_call_summary(call_id)
        if summary:
            socketio.emit('new_call', summary, namespace='/')


@socketio.on('leave_call')
def handle_leave_call(data):
    """Leave a WebSocket room"""
    call_id = data.get('call_id')
    if call_id:
        socketio.leave_room(request.sid, call_id)


if __name__ == '__main__':
    # Use port 5001 instead of 5000 to avoid conflict with macOS AirPlay Receiver
    PORT = 5001
    print("=" * 60)
    print("🚀 Starting T-Mobile Human Responder Dashboard API")
    print("=" * 60)
    print(f"📍 API will be available at: http://localhost:{PORT}")
    print(f"📡 WebSocket support enabled")
    print("=" * 60)
    socketio.run(app, debug=True, port=PORT, use_reloader=False)
