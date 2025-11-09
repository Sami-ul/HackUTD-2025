#!/usr/bin/env python3
"""
Example script showing how to publish new metrics data to the Flask API.
This simulates publishing call drops and active node counts.
"""

import requests
import time
from datetime import datetime

BASE_URL = 'http://localhost:3001'

def publish_metrics(call_drops=None, active_nodes=None):
    """Publish new metrics data point."""
    data = {}
    
    if call_drops is not None:
        data['call_drops'] = call_drops
    
    if active_nodes is not None:
        data['active_nodes'] = active_nodes
    
    if not data:
        print("Error: Must provide at least call_drops or active_nodes")
        return None
    
    response = requests.post(
        f'{BASE_URL}/api/metrics/publish',
        json=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Published: {result['data_point']}")
        return result
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("Metrics Publishing Example")
    print("=" * 60)
    print()
    
    try:
        # Example 1: Publish call drops only
        print("Example 1: Publishing call drops only...")
        publish_metrics(call_drops=5)
        time.sleep(1)
        print()
        
        # Example 2: Publish both call drops and active nodes
        print("Example 2: Publishing both call drops and active nodes...")
        publish_metrics(call_drops=3, active_nodes=9)
        time.sleep(1)
        print()
        
        # Example 3: Publish active nodes only
        print("Example 3: Publishing active nodes only...")
        publish_metrics(active_nodes=8)
        time.sleep(1)
        print()
        
        # Example 4: Simulate a minute-by-minute data stream
        print("Example 4: Simulating minute-by-minute updates...")
        for i in range(5):
            call_drops = 2 + (i % 3)  # Vary between 2-4
            active_nodes = 8 + (i % 2)  # Vary between 8-9
            publish_metrics(call_drops=call_drops, active_nodes=active_nodes)
            time.sleep(0.5)
        
        print()
        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)
        print()
        print("The graph will update automatically every minute.")
        print("You can publish new data points anytime using:")
        print("  POST http://localhost:3001/api/metrics/publish")
        print("  Body: {\"call_drops\": 5, \"active_nodes\": 9}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask backend is running:")
        print("  python backend/app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

