"""
Call Manager - Manages incoming calls and routes them to human responders
Simulates the system where calls are routed from agents to human responders
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


class CallManager:
    """Manages incoming calls and notifications"""
    
    def __init__(self):
        self.pending_calls = []  # Calls waiting to be accepted
        self.active_calls = {}  # Currently active calls
        self.call_history = []  # All calls (for history)
    
    def create_incoming_call(self, phone_number: str, initial_transcript: str, 
                            initial_analysis: Dict, customer_info: Optional[Dict] = None) -> str:
        """
        Create a new incoming call notification
        This simulates a call being routed from an agent to a human responder
        
        Args:
            phone_number: Customer's phone number
            initial_transcript: Initial transcript from agent interaction
            initial_analysis: Sentiment analysis of initial interaction
            customer_info: Optional customer information
        
        Returns:
            call_id: Unique call identifier
        """
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        call_data = {
            'call_id': call_id,
            'phone_number': phone_number,
            'customer_info': customer_info,
            'initial_transcript': initial_transcript,
            'initial_analysis': initial_analysis,
            'initial_sentiment': initial_analysis.get('sentiment', {}),
            'initial_urgency': initial_analysis.get('urgency', {}),
            'initial_emotion': initial_analysis.get('emotion', 'neutral'),
            'status': 'pending',  # pending, active, ended
            'created_at': datetime.now().isoformat(),
            'transcript': [],
            'sentiment_history': []
        }
        
        self.pending_calls.append(call_data)
        
        return call_id
    
    def get_pending_calls(self) -> List[Dict]:
        """Get all pending calls waiting to be accepted"""
        return [call for call in self.pending_calls if call['status'] == 'pending']
    
    def accept_call(self, call_id: str) -> Optional[Dict]:
        """Accept a pending call and move it to active"""
        call = next((c for c in self.pending_calls if c['call_id'] == call_id), None)
        
        if not call:
            return None
        
        # Remove from pending
        self.pending_calls = [c for c in self.pending_calls if c['call_id'] != call_id]
        
        # Add to active
        call['status'] = 'active'
        call['accepted_at'] = datetime.now().isoformat()
        self.active_calls[call_id] = call
        
        return call
    
    def add_transcript_chunk(self, call_id: str, speaker: str, text: str, 
                            analysis: Optional[Dict] = None) -> bool:
        """Add a new transcript chunk from speech-to-text"""
        if call_id not in self.active_calls:
            return False
        
        call = self.active_calls[call_id]
        
        # Add to transcript
        transcript_entry = {
            'speaker': speaker,
            'text': text,
            'timestamp': datetime.now().isoformat()
        }
        call['transcript'].append(transcript_entry)
        
        # Add to sentiment history if analysis provided
        if analysis and speaker == 'customer':
            sentiment_entry = {
                'timestamp': datetime.now().isoformat(),
                'sentiment': analysis.get('sentiment', {}),
                'emotion': analysis.get('emotion', 'neutral'),
                'urgency': analysis.get('urgency', {})
            }
            call['sentiment_history'].append(sentiment_entry)
        
        return True
    
    def get_active_call(self, call_id: str) -> Optional[Dict]:
        """Get an active call by ID"""
        return self.active_calls.get(call_id)
    
    def end_call(self, call_id: str):
        """End an active call"""
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            call['status'] = 'ended'
            call['ended_at'] = datetime.now().isoformat()
            
            # Move to history
            self.call_history.append(call)
            del self.active_calls[call_id]
    
    def get_call_summary(self, call_id: str) -> Optional[Dict]:
        """Get a summary of a call for notifications"""
        # Check pending first
        call = next((c for c in self.pending_calls if c['call_id'] == call_id), None)
        if call:
            initial_transcript = call.get('initial_transcript', '')
            return {
                'call_id': call['call_id'],
                'phone_number': call.get('phone_number', 'Unknown'),
                'customer_name': call.get('customer_info', {}).get('name', 'Unknown') if call.get('customer_info') else 'Unknown',
                'initial_text': (initial_transcript[:100] + '...') if len(initial_transcript) > 100 else initial_transcript,
                'initial_sentiment': call.get('initial_sentiment', {}),
                'initial_urgency': call.get('initial_urgency', {}),
                'created_at': call.get('created_at', datetime.now().isoformat())
            }
        
        # Check active
        call = self.active_calls.get(call_id)
        if call:
            initial_transcript = call.get('initial_transcript', '')
            return {
                'call_id': call['call_id'],
                'phone_number': call.get('phone_number', 'Unknown'),
                'customer_name': call.get('customer_info', {}).get('name', 'Unknown') if call.get('customer_info') else 'Unknown',
                'initial_text': (initial_transcript[:100] + '...') if len(initial_transcript) > 100 else initial_transcript,
                'initial_sentiment': call.get('initial_sentiment', {}),
                'initial_urgency': call.get('initial_urgency', {}),
                'created_at': call.get('created_at', datetime.now().isoformat())
            }
        
        return None

