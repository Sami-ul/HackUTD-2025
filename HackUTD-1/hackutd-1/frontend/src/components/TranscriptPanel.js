import React, { useState, useRef, useEffect } from 'react';
import './TranscriptPanel.css';

function TranscriptPanel({ transcript, onAddLine }) {
  const [newLine, setNewLine] = useState('');
  const [speaker, setSpeaker] = useState('customer');
  const transcriptEndRef = useRef(null);
  const transcriptContainerRef = useRef(null);
  const userHasScrolledUpRef = useRef(false);

  const scrollToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkIfNearBottom = () => {
    if (!transcriptContainerRef.current) return true;
    const container = transcriptContainerRef.current;
    const threshold = 100; // pixels from bottom
    const isNearBottom = 
      container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
    return isNearBottom;
  };

  // Track if user manually scrolls up
  useEffect(() => {
    const container = transcriptContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      userHasScrolledUpRef.current = !checkIfNearBottom();
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Only auto-scroll if user is near the bottom (hasn't scrolled up)
  useEffect(() => {
    // If user hasn't scrolled up, auto-scroll to bottom
    if (!userHasScrolledUpRef.current) {
      scrollToBottom();
    }
    // If new final (non-partial) line is added and user is near bottom, scroll
    else if (transcript.length > 0) {
      const lastLine = transcript[transcript.length - 1];
      if (!lastLine.isPartial && checkIfNearBottom()) {
        userHasScrolledUpRef.current = false;
        scrollToBottom();
      }
    }
  }, [transcript]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newLine.trim()) {
      onAddLine({
        speaker: speaker,
        text: newLine.trim(),
        timestamp: new Date().toISOString(),
        isPartial: false
      });
      setNewLine('');
    }
  };

  return (
    <div className="card transcript-panel">
      <div className="card-header">
        <h3 className="card-title">Live Transcript</h3>
      </div>
      
      <div className="transcript-container" ref={transcriptContainerRef}>
        {transcript.length === 0 ? (
          <div className="transcript-empty">
            <p>No transcript yet. Start the conversation...</p>
          </div>
        ) : (
          transcript.map((line, idx) => (
            <div
              key={idx}
              className={`transcript-line transcript-${line.speaker} ${line.isPartial ? 'transcript-partial' : ''}`}
            >
              <div className="transcript-speaker">
                {line.speaker === 'customer' ? '👤 Customer' : '💼 Agent'}
                {line.isPartial && <span className="partial-indicator"> (typing...)</span>}
              </div>
              <div className="transcript-text">{line.text}</div>
              {!line.isPartial && (
                <div className="transcript-time">
                  {new Date(line.timestamp).toLocaleTimeString()}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={transcriptEndRef} />
      </div>

      {/* Removed manual input - using speech-to-text instead */}
    </div>
  );
}

export default TranscriptPanel;

