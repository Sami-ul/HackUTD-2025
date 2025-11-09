#!/usr/bin/env python3
"""
Example script showing how to update node status via the Flask API.
"""

import requests
import time

BASE_URL = 'http://localhost:3001'

def update_node_status(node_id, status):
    """Update a node's status."""
    response = requests.put(
        f'{BASE_URL}/api/nodes/{node_id}',
        json={'status': status}
    )
    if response.status_code == 200:
        node = response.json()
        print(f"✅ Updated {node['name']} (ID: {node_id}) to {status}")
        return node
    else:
        print(f"❌ Error updating node {node_id}: {response.text}")
        return None

def toggle_node(node_id):
    """Toggle a node's status."""
    response = requests.post(f'{BASE_URL}/api/nodes/{node_id}/toggle')
    if response.status_code == 200:
        node = response.json()
        print(f"🔄 Toggled {node['name']} (ID: {node_id}) to {node['status']}")
        return node
    else:
        print(f"❌ Error toggling node {node_id}: {response.text}")
        return None

def get_all_nodes():
    """Get all nodes."""
    response = requests.get(f'{BASE_URL}/api/nodes')
    if response.status_code == 200:
        return response.json()
    return None

if __name__ == '__main__':
    print("=" * 60)
    print("DFW Network Map - Node Status Update Example")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        nodes = get_all_nodes()
        if not nodes:
            print("❌ Could not connect to Flask server.")
            print("Make sure the Flask backend is running: python backend/app.py")
            exit(1)
        
        print(f"📡 Connected! Found {len(nodes)} nodes.")
        print()
        
        # Example 1: Update a specific node to offline
        print("Example 1: Setting Tower Alpha to offline...")
        update_node_status(1, 'offline')
        time.sleep(1)
        print()
        
        # Example 2: Toggle a node's status
        print("Example 2: Toggling Tower Beta's status...")
        toggle_node(2)
        time.sleep(1)
        print()
        
        # Example 3: Set multiple nodes offline
        print("Example 3: Setting multiple nodes offline...")
        for node_id in [3, 4, 5]:
            update_node_status(node_id, 'offline')
        time.sleep(1)
        print()
        
        # Example 4: Set them back online
        print("Example 4: Setting them back online...")
        for node_id in [1, 3, 4, 5]:
            update_node_status(node_id, 'online')
        print()
        
        # Show final status
        print("=" * 60)
        print("Final node statuses:")
        print("=" * 60)
        nodes = get_all_nodes()
        for node in nodes:
            status_emoji = "🟢" if node['status'] == 'online' else "🔴"
            print(f"{status_emoji} {node['name']}: {node['status']}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Flask server.")
        print("Make sure the Flask backend is running:")
        print("  python backend/app.py")
    except Exception as e:
        print(f"❌ Error: {e}")

