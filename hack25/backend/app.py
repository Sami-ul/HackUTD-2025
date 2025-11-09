from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import requests as http_requests
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initial node data - same as frontend mock data
INITIAL_NODES = [
    {'id': 1, 'name': 'Tower Alpha', 'lat': 32.7767, 'lon': -96.7970, 'status': 'online'},
    {'id': 2, 'name': 'Tower Beta', 'lat': 32.8500, 'lon': -96.8500, 'status': 'online'},
    {'id': 3, 'name': 'Tower Gamma', 'lat': 32.7500, 'lon': -96.7500, 'status': 'offline'},
    {'id': 4, 'name': 'Tower Delta', 'lat': 32.8000, 'lon': -96.9000, 'status': 'online'},
    {'id': 5, 'name': 'Tower Epsilon', 'lat': 32.7200, 'lon': -96.8200, 'status': 'online'},
    {'id': 6, 'name': 'Tower Zeta', 'lat': 32.8800, 'lon': -96.7800, 'status': 'offline'},
    {'id': 7, 'name': 'Tower Eta', 'lat': 32.7000, 'lon': -96.9500, 'status': 'online'},
    {'id': 8, 'name': 'Tower Theta', 'lat': 32.8200, 'lon': -96.7000, 'status': 'online'},
    {'id': 9, 'name': 'Tower Iota', 'lat': 32.7300, 'lon': -96.8800, 'status': 'offline'},
    {'id': 10, 'name': 'Tower Kappa', 'lat': 32.7900, 'lon': -96.7200, 'status': 'online'},
    {'id': 11, 'name': 'Tower Lambda', 'lat': 32.7600, 'lon': -96.8000, 'status': 'online'},
    {'id': 12, 'name': 'Tower Mu', 'lat': 32.8100, 'lon': -96.8300, 'status': 'offline'},
    {'id': 13, 'name': 'Tower Nu', 'lat': 32.7400, 'lon': -96.7600, 'status': 'online'},
    {'id': 14, 'name': 'Tower Xi', 'lat': 32.8600, 'lon': -96.9200, 'status': 'online'},
    {'id': 15, 'name': 'Tower Omicron', 'lat': 32.7100, 'lon': -96.9000, 'status': 'offline'},
]

# In-memory storage for nodes
nodes = {node['id']: node.copy() for node in INITIAL_NODES}

# Current metrics storage (can be updated via API)
current_metrics = {
    'avg_latency': 45.0,
    'call_drop_rate': 1.2,
    'signal_quality': 8.6,
    'uptime': 99.4,
}

# Region latency data
region_latency = {
    'Dallas': 45,
    'Fort Worth': 48,
    'Arlington': 42,
    'Plano': 50,
    'Irving': 44,
}

# Traffic volume history
traffic_volume_history = []

# History data for metrics chart - stores actual data points
history_data = []

# Initialize with some default history data
def initialize_history():
    """Initialize history with current state."""
    now = datetime.now()
    active_nodes = sum(1 for node in nodes.values() if node['status'] == 'online')
    history_data.append({
        'timestamp': now.isoformat(),
        'call_drops': 0,
        'active_nodes': active_nodes
    })
    
    # Initialize traffic volume with some data
    for i in range(6):
        traffic_volume_history.append({
            'timestamp': (now - timedelta(minutes=5 * (6 - i))).isoformat(),
            'volume': 1000 + random.randint(0, 600)
        })

# Initialize on startup
initialize_history()


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes with their current status."""
    return jsonify(list(nodes.values()))


@app.route('/api/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    """Get a specific node by ID."""
    if node_id not in nodes:
        return jsonify({'error': 'Node not found'}), 404
    return jsonify(nodes[node_id])


@app.route('/api/nodes/<int:node_id>', methods=['PUT', 'PATCH'])
def update_node(node_id):
    """Update a node's status."""
    if node_id not in nodes:
        return jsonify({'error': 'Node not found'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate status if provided
    if 'status' in data:
        if data['status'] not in ['online', 'offline']:
            return jsonify({'error': 'Status must be "online" or "offline"'}), 400
        nodes[node_id]['status'] = data['status']
    
    # Allow updating other fields (name, lat, lon) if needed
    if 'name' in data:
        nodes[node_id]['name'] = data['name']
    if 'lat' in data:
        nodes[node_id]['lat'] = data['lat']
    if 'lon' in data:
        nodes[node_id]['lon'] = data['lon']
    
    return jsonify(nodes[node_id])


@app.route('/api/nodes/<int:node_id>/toggle', methods=['POST'])
def toggle_node_status(node_id):
    """Toggle a node's status between online and offline."""
    if node_id not in nodes:
        return jsonify({'error': 'Node not found'}), 404
    
    current_status = nodes[node_id]['status']
    nodes[node_id]['status'] = 'online' if current_status == 'offline' else 'offline'
    
    return jsonify(nodes[node_id])


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current network health metrics."""
    active_nodes = sum(1 for node in nodes.values() if node['status'] == 'online')
    total_nodes = len(nodes)
    
    # Calculate uptime based on node status
    uptime = (active_nodes / total_nodes) * 100 if total_nodes > 0 else 0
    
    # Return stored metrics (can be updated via PUT/PATCH)
    return jsonify({
        'avg_latency': round(current_metrics['avg_latency'], 1),
        'call_drop_rate': round(current_metrics['call_drop_rate'], 1),
        'signal_quality': round(current_metrics['signal_quality'], 1),
        'uptime': round(uptime, 1),  # Calculated from nodes
        'active_nodes': active_nodes,  # Calculated from nodes
        'total_nodes': total_nodes  # Calculated from nodes
    })


@app.route('/api/metrics', methods=['PUT', 'PATCH'])
def update_metrics():
    """Update network health metrics."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update metrics that are provided
    if 'avg_latency' in data:
        try:
            value = float(data['avg_latency'])
            if value < 0:
                return jsonify({'error': 'avg_latency must be non-negative'}), 400
            current_metrics['avg_latency'] = value
        except (ValueError, TypeError):
            return jsonify({'error': 'avg_latency must be a number'}), 400
    
    if 'call_drop_rate' in data:
        try:
            value = float(data['call_drop_rate'])
            if value < 0:
                return jsonify({'error': 'call_drop_rate must be non-negative'}), 400
            current_metrics['call_drop_rate'] = value
        except (ValueError, TypeError):
            return jsonify({'error': 'call_drop_rate must be a number'}), 400
    
    if 'signal_quality' in data:
        try:
            value = float(data['signal_quality'])
            if value < 0 or value > 10:
                return jsonify({'error': 'signal_quality must be between 0 and 10'}), 400
            current_metrics['signal_quality'] = value
        except (ValueError, TypeError):
            return jsonify({'error': 'signal_quality must be a number'}), 400
    
    # Get current calculated values
    active_nodes = sum(1 for node in nodes.values() if node['status'] == 'online')
    total_nodes = len(nodes)
    uptime = (active_nodes / total_nodes) * 100 if total_nodes > 0 else 0
    
    return jsonify({
        'avg_latency': round(current_metrics['avg_latency'], 1),
        'call_drop_rate': round(current_metrics['call_drop_rate'], 1),
        'signal_quality': round(current_metrics['signal_quality'], 1),
        'uptime': round(uptime, 1),
        'active_nodes': active_nodes,
        'total_nodes': total_nodes
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical metrics data for the chart."""
    # Return stored history data (last 60 data points max)
    # Sort by timestamp to ensure chronological order
    sorted_history = sorted(history_data, key=lambda x: x['timestamp'])
    
    # Return last 60 points (or all if less than 60)
    return jsonify(sorted_history[-60:])


@app.route('/api/metrics/publish', methods=['POST'])
def publish_metrics():
    """Publish new metrics data point (call drops and/or active nodes)."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get current active nodes count
    active_nodes = sum(1 for node in nodes.values() if node['status'] == 'online')
    
    # Create new data point
    new_point = {
        'timestamp': datetime.now().isoformat(),
        'call_drops': data.get('call_drops', 0),
        'active_nodes': data.get('active_nodes', active_nodes)  # Use provided or current count
    }
    
    # Validate call_drops
    if 'call_drops' in data:
        if not isinstance(data['call_drops'], int) or data['call_drops'] < 0:
            return jsonify({'error': 'call_drops must be a non-negative integer'}), 400
    
    # Validate active_nodes if provided
    if 'active_nodes' in data:
        if not isinstance(data['active_nodes'], int) or data['active_nodes'] < 0:
            return jsonify({'error': 'active_nodes must be a non-negative integer'}), 400
    
    # Add to history
    history_data.append(new_point)
    
    # Keep only last 1000 data points to prevent memory issues
    if len(history_data) > 1000:
        history_data.pop(0)
    
    return jsonify({
        'success': True,
        'data_point': new_point,
        'total_points': len(history_data)
    })


@app.route('/api/regions/latency', methods=['GET'])
def get_region_latency():
    """Get latency data by region."""
    return jsonify([
        {'region': region, 'latency': latency}
        for region, latency in region_latency.items()
    ])


@app.route('/api/regions/latency', methods=['PUT', 'PATCH'])
def update_region_latency():
    """Update latency for one or more regions."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # If it's a list of regions
    if isinstance(data, list):
        for item in data:
            if 'region' in item and 'latency' in item:
                region = item['region']
                try:
                    latency = float(item['latency'])
                    if latency < 0:
                        return jsonify({'error': f'Latency for {region} must be non-negative'}), 400
                    if region in region_latency:
                        region_latency[region] = latency
                except (ValueError, TypeError):
                    return jsonify({'error': f'Latency for {region} must be a number'}), 400
    # If it's a single region update
    elif isinstance(data, dict):
        if 'region' in data and 'latency' in data:
            region = data['region']
            try:
                latency = float(data['latency'])
                if latency < 0:
                    return jsonify({'error': f'Latency for {region} must be non-negative'}), 400
                if region in region_latency:
                    region_latency[region] = latency
                else:
                    return jsonify({'error': f'Region {region} not found'}), 404
            except (ValueError, TypeError):
                return jsonify({'error': 'Latency must be a number'}), 400
        else:
            return jsonify({'error': 'Must provide "region" and "latency"'}), 400
    
    return jsonify([
        {'region': region, 'latency': latency}
        for region, latency in region_latency.items()
    ])


@app.route('/api/traffic', methods=['GET'])
def get_traffic_volume():
    """Get traffic volume history."""
    # Return last 60 data points
    sorted_traffic = sorted(traffic_volume_history, key=lambda x: x['timestamp'])
    return jsonify(sorted_traffic[-60:])


@app.route('/api/traffic', methods=['POST'])
def add_traffic_volume():
    """Add a new traffic volume data point."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        volume = int(data.get('volume', 0))
        if volume < 0:
            return jsonify({'error': 'Volume must be non-negative'}), 400
        
        timestamp = data.get('timestamp')
        if timestamp:
            try:
                # Validate timestamp format
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid timestamp format'}), 400
        else:
            timestamp = datetime.now().isoformat()
        
        new_point = {
            'timestamp': timestamp,
            'volume': volume
        }
        
        traffic_volume_history.append(new_point)
        
        # Keep only last 1000 data points
        if len(traffic_volume_history) > 1000:
            traffic_volume_history.pop(0)
        
        return jsonify({
            'success': True,
            'data_point': new_point,
            'total_points': len(traffic_volume_history)
        })
    except (ValueError, TypeError):
        return jsonify({'error': 'Volume must be an integer'}), 400


@app.route('/api/reddit', methods=['GET'])
def get_reddit_posts():
    """Fetch latest Reddit posts from r/TMobile."""
    subreddit = request.args.get('subreddit', 'TMobile')
    
    try:
        url = f'https://www.reddit.com/r/{subreddit}/new.json?limit=10'
        headers = {
            'User-Agent': 'NetPulse Dashboard/1.0 (Educational Project)'
        }
        
        response = http_requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = []
        
        for child in data.get('data', {}).get('children', []):
            post_data = child.get('data', {})
            posts.append({
                'id': post_data.get('id'),
                'title': post_data.get('title', ''),
                'author': post_data.get('author', ''),
                'ups': post_data.get('ups', 0),
                'selftext': post_data.get('selftext', ''),
                'permalink': f"https://www.reddit.com{post_data.get('permalink', '')}",
                'created_utc': post_data.get('created_utc', 0),
            })
        
        return jsonify(posts)
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch Reddit data: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/sentiment', methods=['POST'])
def analyze_sentiment():
    """Analyze sentiment of text using simple heuristic."""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text'].lower()
    
    # Negative words
    negative_words = ['bad', 'slow', 'dropped', 'terrible', 'awful', 'horrible', 'frustrated', 
                      'frustrating', 'issue', 'problem', 'broken', 'down', 'outage', 'complaint',
                      'disappointed', 'hate', 'worst', 'fail', 'failed', 'error', 'bug']
    
    # Positive words
    positive_words = ['good', 'great', 'love', 'excellent', 'amazing', 'wonderful', 'fantastic',
                     'perfect', 'awesome', 'satisfied', 'happy', 'pleased', 'best', 'outstanding',
                     'smooth', 'fast', 'reliable', 'helpful', 'thanks', 'thank you', 'appreciate']
    
    # Count matches
    negative_count = sum(1 for word in negative_words if word in text)
    positive_count = sum(1 for word in positive_words if word in text)
    
    # Determine sentiment
    if negative_count > positive_count:
        sentiment = 'negative'
        score = max(0.1, 0.3 - (negative_count * 0.1))
    elif positive_count > negative_count:
        sentiment = 'positive'
        score = min(0.95, 0.7 + (positive_count * 0.1))
    else:
        sentiment = 'neutral'
        score = 0.5
    
    return jsonify({
        'sentiment': sentiment,
        'score': round(score, 2)
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'node_count': len(nodes),
        'history_points': len(history_data),
        'traffic_points': len(traffic_volume_history)
    })


if __name__ == '__main__':
    print('Starting Flask backend server...')
    print('API endpoints:')
    print('  GET  /api/nodes - Get all nodes')
    print('  GET  /api/nodes/<id> - Get specific node')
    print('  PUT  /api/nodes/<id> - Update node (body: {"status": "online|offline"})')
    print('  POST /api/nodes/<id>/toggle - Toggle node status')
    print('  GET  /api/metrics - Get network health metrics')
    print('  PUT  /api/metrics - Update metrics (body: {"avg_latency": float, "call_drop_rate": float, "signal_quality": float})')
    print('  GET  /api/history - Get historical metrics data')
    print('  POST /api/metrics/publish - Publish new metrics (body: {"call_drops": int, "active_nodes": int})')
    print('  GET  /api/regions/latency - Get latency by region')
    print('  PUT  /api/regions/latency - Update region latency (body: [{"region": str, "latency": float}] or {"region": str, "latency": float})')
    print('  GET  /api/traffic - Get traffic volume history')
    print('  POST /api/traffic - Add traffic volume point (body: {"volume": int, "timestamp": str?})')
    print('  GET  /api/reddit - Get Reddit posts from r/TMobile (query param: subreddit)')
    print('  POST /api/sentiment - Analyze sentiment (body: {"text": str})')
    print('  GET  /api/health - Health check')
    app.run(host='0.0.0.0', port=3001, debug=True)

