import React, { useState } from 'react';
import './TranscriptLoader.css';

function TranscriptLoader({ onLoadTranscript }) {
  const [transcriptText, setTranscriptText] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLoad = () => {
    if (!transcriptText.trim()) {
      alert('Please paste or enter a transcript');
      return;
    }

    setLoading(true);
    
    // Parse the transcript to extract customer and agent text
    const lines = transcriptText.split('\n');
    const customerLines = [];
    const agentLines = [];
    
    let currentSpeaker = null;
    let currentText = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      const lower = trimmed.toLowerCase();
      
      if (lower.startsWith('customer:') || lower.startsWith('customer ')) {
        if (currentSpeaker && currentText.length > 0) {
          if (currentSpeaker === 'customer') {
            customerLines.push(currentText.join(' '));
          } else {
            agentLines.push(currentText.join(' '));
          }
        }
        currentSpeaker = 'customer';
        const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(8).trim();
        currentText = text ? [text] : [];
      } else if (lower.startsWith('agent:') || lower.startsWith('agent ')) {
        if (currentSpeaker && currentText.length > 0) {
          if (currentSpeaker === 'customer') {
            customerLines.push(currentText.join(' '));
          } else {
            agentLines.push(currentText.join(' '));
          }
        }
        currentSpeaker = 'agent';
        const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(5).trim();
        currentText = text ? [text] : [];
      } else if (currentSpeaker) {
        currentText.push(trimmed);
      } else {
        // No speaker label - assume customer
        currentSpeaker = 'customer';
        currentText = [trimmed];
      }
    }
    
    // Add last speaker's text
    if (currentSpeaker && currentText.length > 0) {
      if (currentSpeaker === 'customer') {
        customerLines.push(currentText.join(' '));
      } else {
        agentLines.push(currentText.join(' '));
      }
    }
    
    const customerText = customerLines.join(' ');
    const agentText = agentLines.join(' ');
    
    // Parse lines with proper timestamps (second pass for structured output)
    const parsedLines = [];
    let lineIndex = 0;
    let parsedSpeaker = null;
    let parsedText = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      const lower = trimmed.toLowerCase();
      
      if (lower.startsWith('customer:') || lower.startsWith('customer ')) {
        // Save previous speaker's text
        if (parsedSpeaker && parsedText.length > 0) {
          parsedLines.push({
            speaker: parsedSpeaker,
            text: parsedText.join(' '),
            timestamp: new Date(Date.now() - (lines.length - lineIndex) * 1000).toISOString()
          });
        }
        parsedSpeaker = 'customer';
        const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(8).trim();
        parsedText = text ? [text] : [];
      } else if (lower.startsWith('agent:') || lower.startsWith('agent ')) {
        // Save previous speaker's text
        if (parsedSpeaker && parsedText.length > 0) {
          parsedLines.push({
            speaker: parsedSpeaker,
            text: parsedText.join(' '),
            timestamp: new Date(Date.now() - (lines.length - lineIndex) * 1000).toISOString()
          });
        }
        parsedSpeaker = 'agent';
        const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(5).trim();
        parsedText = text ? [text] : [];
      } else if (parsedSpeaker) {
        parsedText.push(trimmed);
      } else {
        // No speaker label - assume customer
        parsedSpeaker = 'customer';
        parsedText = [trimmed];
      }
      lineIndex++;
    }
    
    // Add last speaker's text
    if (parsedSpeaker && parsedText.length > 0) {
      parsedLines.push({
        speaker: parsedSpeaker,
        text: parsedText.join(' '),
        timestamp: new Date().toISOString()
      });
    }
    
    // Create call data
    const callData = {
      callId: `call_${Date.now()}`,
      phoneNumber: phoneNumber || 'Unknown',
      transcript: transcriptText,
      customerText: customerText,
      agentText: agentText,
      parsedLines: parsedLines
    };
    
    onLoadTranscript(callData);
    setLoading(false);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setTranscriptText(event.target.result);
    };
    reader.readAsText(file);
  };

  return (
    <div className="transcript-loader">
      <div className="loader-container">
        <div className="loader-header">
          <h1>Load Call Transcript</h1>
          <p>Paste or upload an existing call transcript to analyze</p>
        </div>

        <div className="loader-card">
          <div className="form-group">
            <label htmlFor="phone">Phone Number (Optional)</label>
            <input
              type="text"
              id="phone"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="555-123-4567"
              className="phone-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="transcript">Call Transcript</label>
            <div className="file-upload-section">
              <input
                type="file"
                id="file-upload"
                accept=".txt,.json"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <label htmlFor="file-upload" className="file-upload-btn">
                📁 Upload File
              </label>
            </div>
            <textarea
              id="transcript"
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              placeholder={`customer I'm frustrated with the service!
agent I understand your frustration. Let me help you.
customer This is the third time I've called about this issue.
agent I apologize for the inconvenience.`}
              className="transcript-textarea"
              rows={15}
            />
          </div>

          <button
            onClick={handleLoad}
            disabled={loading || !transcriptText.trim()}
            className="btn btn-primary btn-large"
          >
            {loading ? 'Loading...' : 'Load & Analyze Transcript'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TranscriptLoader;

