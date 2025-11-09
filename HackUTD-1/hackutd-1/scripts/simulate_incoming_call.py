#!/usr/bin/env python3
"""
Simulate an incoming call being routed to a human responder
This simulates the scenario where an agent routes a call to a human responder
"""

import sys
import requests
import json
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

API_URL = "http://localhost:5001"

def simulate_incoming_call(phone_number: str, initial_transcript: str):
    """
    Simulate a call being routed from an agent to a human responder
    
    Args:
        phone_number: Customer's phone number
        initial_transcript: Initial conversation transcript with agent
    """
    print(f"📞 Simulating incoming call from {phone_number}...")
    
    # Route the call (this creates the notification)
    response = requests.post(f"{API_URL}/api/route", json={
        'phone_number': phone_number,
        'customer_text': initial_transcript,
        'initial_transcript': initial_transcript
    })
    
    print(response)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Call routed successfully!")
        print(f"   Call ID: {data['call_id']}")
        print(f"   Assigned CSR: {data['assigned_csr']['name']}")
        print(f"   Initial Sentiment: {data['analysis']['sentiment']['label']}")
        print(f"\n📢 Notification should appear in the dashboard!")
        return data['call_id']
    else:
        print(f"❌ Error routing call: {response.text}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulate an incoming call')
    parser.add_argument('--phone', type=str, default='5551234567',
                       help='Customer phone number')
    parser.add_argument('--transcript', type=str,
                       default="customer I'm extremely frustrated with the service! This is the third time I've called. agent I understand. Let me transfer you to a specialist.",
                       help='Initial transcript with agent')
    parser.add_argument('--file', type=str,
                       help='File containing initial transcript')
    
    args = parser.parse_args()
    
    # Load transcript from file if provided
    if args.file:
        with open(args.file, 'r') as f:
            transcript = f.read()
    else:
        transcript = args.transcript
    
    simulate_incoming_call(args.phone, transcript)

