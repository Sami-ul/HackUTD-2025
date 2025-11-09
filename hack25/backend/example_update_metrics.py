"""
Example script to update network metrics via API.

This demonstrates how to update:
- Network health metrics (avg_latency, call_drop_rate, signal_quality)
- Region latency data
- Traffic volume data
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:3001'

def update_metrics():
    """Update network health metrics."""
    print("\n=== Updating Network Health Metrics ===")
    
    # Update all metrics at once
    data = {
        'avg_latency': 42.5,
        'call_drop_rate': 1.8,
        'signal_quality': 8.9
    }
    
    response = requests.put(f'{BASE_URL}/api/metrics', json=data)
    if response.ok:
        print(f"✓ Updated metrics: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def update_single_metric():
    """Update a single metric."""
    print("\n=== Updating Single Metric ===")
    
    # Update only call drop rate
    data = {
        'call_drop_rate': 2.1
    }
    
    response = requests.put(f'{BASE_URL}/api/metrics', json=data)
    if response.ok:
        print(f"✓ Updated call_drop_rate: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def update_region_latency():
    """Update latency for regions."""
    print("\n=== Updating Region Latency ===")
    
    # Update multiple regions at once
    data = [
        {'region': 'Dallas', 'latency': 38.5},
        {'region': 'Fort Worth', 'latency': 45.2},
        {'region': 'Plano', 'latency': 52.0}
    ]
    
    response = requests.put(f'{BASE_URL}/api/regions/latency', json=data)
    if response.ok:
        print(f"✓ Updated region latency: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def update_single_region():
    """Update latency for a single region."""
    print("\n=== Updating Single Region ===")
    
    # Update single region
    data = {
        'region': 'Irving',
        'latency': 41.3
    }
    
    response = requests.put(f'{BASE_URL}/api/regions/latency', json=data)
    if response.ok:
        print(f"✓ Updated Irving latency: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def add_traffic_volume():
    """Add a new traffic volume data point."""
    print("\n=== Adding Traffic Volume Data Point ===")
    
    data = {
        'volume': 1450,
        'timestamp': datetime.now().isoformat()
    }
    
    response = requests.post(f'{BASE_URL}/api/traffic', json=data)
    if response.ok:
        print(f"✓ Added traffic volume: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def publish_call_drops():
    """Publish call drops and active nodes."""
    print("\n=== Publishing Call Drops ===")
    
    data = {
        'call_drops': 5,
        'active_nodes': 10  # Optional, will use current count if not provided
    }
    
    response = requests.post(f'{BASE_URL}/api/metrics/publish', json=data)
    if response.ok:
        print(f"✓ Published metrics: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

def get_current_metrics():
    """Get current metrics."""
    print("\n=== Current Metrics ===")
    
    response = requests.get(f'{BASE_URL}/api/metrics')
    if response.ok:
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"✗ Error: {response.status_code} - {response.text}")

if __name__ == '__main__':
    print("Network Metrics API Examples")
    print("=" * 50)
    
    try:
        # Get current state
        get_current_metrics()
        
        # Update metrics
        update_metrics()
        update_single_metric()
        
        # Update region latency
        update_region_latency()
        update_single_region()
        
        # Add traffic volume
        add_traffic_volume()
        
        # Publish call drops
        publish_call_drops()
        
        # Get updated state
        get_current_metrics()
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to backend server.")
        print("   Make sure the Flask backend is running on http://localhost:3001")
        print("   Run: python backend/run.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")

