#!/usr/bin/env python3
"""
Simple test script to verify the Flask API endpoints.
Run this after starting the Flask server.
"""

import requests
import json

BASE_URL = 'http://localhost:3001'

def test_get_all_nodes():
    """Test getting all nodes."""
    print("Testing GET /api/nodes...")
    response = requests.get(f'{BASE_URL}/api/nodes')
    print(f"Status: {response.status_code}")
    print(f"Nodes: {json.dumps(response.json(), indent=2)}")
    print()

def test_get_node(node_id):
    """Test getting a specific node."""
    print(f"Testing GET /api/nodes/{node_id}...")
    response = requests.get(f'{BASE_URL}/api/nodes/{node_id}')
    print(f"Status: {response.status_code}")
    print(f"Node: {json.dumps(response.json(), indent=2)}")
    print()

def test_update_node(node_id, status):
    """Test updating a node's status."""
    print(f"Testing PUT /api/nodes/{node_id} with status={status}...")
    response = requests.put(
        f'{BASE_URL}/api/nodes/{node_id}',
        json={'status': status}
    )
    print(f"Status: {response.status_code}")
    print(f"Updated Node: {json.dumps(response.json(), indent=2)}")
    print()

def test_toggle_node(node_id):
    """Test toggling a node's status."""
    print(f"Testing POST /api/nodes/{node_id}/toggle...")
    response = requests.post(f'{BASE_URL}/api/nodes/{node_id}/toggle')
    print(f"Status: {response.status_code}")
    print(f"Toggled Node: {json.dumps(response.json(), indent=2)}")
    print()

def test_health():
    """Test health check endpoint."""
    print("Testing GET /api/health...")
    response = requests.get(f'{BASE_URL}/api/health')
    print(f"Status: {response.status_code}")
    print(f"Health: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("Flask API Test Suite")
        print("=" * 50)
        print()
        
        test_health()
        test_get_all_nodes()
        test_get_node(1)
        test_update_node(1, 'offline')
        test_update_node(1, 'online')
        test_toggle_node(2)
        test_get_all_nodes()
        
        print("=" * 50)
        print("All tests completed!")
        print("=" * 50)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask server.")
        print("Make sure the Flask backend is running on http://localhost:3001")
    except Exception as e:
        print(f"Error: {e}")

