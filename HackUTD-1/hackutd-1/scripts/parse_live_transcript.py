"""
Parse live transcripts that come with speaker labels (Customer/Agent)
Extracts customer text only for sentiment analysis
"""

import re
from typing import Dict, List, Tuple

def parse_transcript_with_speakers(transcript_text: str) -> Dict[str, str]:
    """
    Parse a transcript that has speaker labels like:
    "customer I'm frustrated with the service
     agent I understand your frustration..."
    or
    "Customer: I'm frustrated with the service
     Agent: I understand your frustration..."
    
    Supports both formats:
    - "customer" or "Customer:" followed by text
    - "agent" or "Agent:" followed by text
    
    Returns:
        Dictionary with 'customer_text' and 'agent_text' separated
    """
    customer_parts = []
    agent_parts = []
    
    # Split by lines
    lines = transcript_text.split('\n')
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line_lower = line.lower()
        
        # Check for speaker labels - support both "customer" and "customer:" formats
        if line_lower.startswith('customer:') or (line_lower.startswith('customer ') and len(line) > 8):
            # Save previous speaker's text
            if current_speaker == 'agent' and current_text:
                agent_parts.append(' '.join(current_text))
            elif current_speaker == 'customer' and current_text:
                customer_parts.append(' '.join(current_text))
            
            # Start new customer text
            current_speaker = 'customer'
            # Remove "customer:" or "customer " prefix
            if ':' in line[:15]:
                text = line.split(':', 1)[1].strip()
            else:
                text = line[8:].strip()  # Remove "customer "
            current_text = [text] if text else []
            
        elif line_lower.startswith('agent:') or (line_lower.startswith('agent ') and len(line) > 5):
            # Save previous speaker's text
            if current_speaker == 'customer' and current_text:
                customer_parts.append(' '.join(current_text))
            elif current_speaker == 'agent' and current_text:
                agent_parts.append(' '.join(current_text))
            
            # Start new agent text
            current_speaker = 'agent'
            # Remove "agent:" or "agent " prefix
            if ':' in line[:10]:
                text = line.split(':', 1)[1].strip()
            else:
                text = line[5:].strip()  # Remove "agent "
            current_text = [text] if text else []
            
        else:
            # Continuation of current speaker's text
            if current_speaker:
                current_text.append(line)
            else:
                # No speaker label yet - assume it's customer text
                current_speaker = 'customer'
                current_text = [line]
    
    # Save last speaker's text
    if current_speaker == 'customer' and current_text:
        customer_parts.append(' '.join(current_text))
    elif current_speaker == 'agent' and current_text:
        agent_parts.append(' '.join(current_text))
    
    return {
        'customer_text': ' '.join(customer_parts).strip(),
        'agent_text': ' '.join(agent_parts).strip()
    }


def parse_transcript_by_lines(transcript_text: str) -> List[Dict[str, str]]:
    """
    Parse a transcript and return each customer line separately with its line number
    
    Returns:
        List of dictionaries, each with:
        - 'line_number': int
        - 'customer_text': str
        - 'agent_text': str (if agent spoke before this customer line)
        - 'full_line': str (original line)
    """
    lines = transcript_text.split('\n')
    parsed_lines = []
    current_agent_text = ""
    line_num = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line_lower = line.lower()
        
        # Check for customer line
        if line_lower.startswith('customer:') or (line_lower.startswith('customer ') and len(line) > 8):
            line_num += 1
            # Remove "customer:" or "customer " prefix
            if ':' in line[:15]:
                customer_text = line.split(':', 1)[1].strip()
            else:
                customer_text = line[8:].strip()  # Remove "customer "
            
            parsed_lines.append({
                'line_number': line_num,
                'customer_text': customer_text,
                'agent_text': current_agent_text.strip(),
                'full_line': line
            })
            current_agent_text = ""  # Reset agent text after customer line
            
        # Check for agent line
        elif line_lower.startswith('agent:') or (line_lower.startswith('agent ') and len(line) > 5):
            # Remove "agent:" or "agent " prefix
            if ':' in line[:10]:
                agent_text = line.split(':', 1)[1].strip()
            else:
                agent_text = line[5:].strip()  # Remove "agent "
            
            # Accumulate agent text (will be associated with next customer line)
            if current_agent_text:
                current_agent_text += " " + agent_text
            else:
                current_agent_text = agent_text
    
    return parsed_lines


def parse_realtime_chunk(text_chunk: str, previous_context: Dict = None) -> Dict[str, str]:
    """
    Parse a real-time chunk of text that may have speaker labels
    
    Args:
        text_chunk: New text chunk from live transcript
        previous_context: Previous customer/agent text for context
    
    Returns:
        Dictionary with 'customer_text' and 'agent_text'
    """
    if previous_context is None:
        previous_context = {'customer_text': '', 'agent_text': ''}
    
    # Check if chunk has speaker label
    if text_chunk.lower().startswith('customer:'):
        customer_text = text_chunk[9:].strip()
        return {
            'customer_text': customer_text,
            'agent_text': previous_context.get('agent_text', '')
        }
    elif text_chunk.lower().startswith('agent:'):
        agent_text = text_chunk[6:].strip()
        return {
            'customer_text': previous_context.get('customer_text', ''),
            'agent_text': agent_text
        }
    else:
        # No label - assume it's continuation of last speaker
        # In real-time, you'd track the last speaker
        # For now, append to customer_text if no agent text exists
        if not previous_context.get('agent_text'):
            return {
                'customer_text': previous_context.get('customer_text', '') + ' ' + text_chunk,
                'agent_text': ''
            }
        else:
            # Could be either - default to customer for sentiment analysis
            return {
                'customer_text': previous_context.get('customer_text', '') + ' ' + text_chunk,
                'agent_text': previous_context.get('agent_text', '')
            }


if __name__ == "__main__":
    # Test
    test_transcript = """Customer: I'm extremely frustrated with the service!
Agent: I understand your frustration. Let me help you.
Customer: This is the third time I've called about this issue.
Agent: I apologize for the inconvenience."""
    
    result = parse_transcript_with_speakers(test_transcript)
    print("Parsed transcript:")
    print(f"Customer: {result['customer_text']}")
    print(f"Agent: {result['agent_text']}")
    
    print("\nParsed by lines:")
    lines = parse_transcript_by_lines(test_transcript)
    for line_data in lines:
        print(f"Line {line_data['line_number']}: {line_data['customer_text']}")
