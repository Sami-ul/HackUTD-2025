import React, { useEffect, useRef, useState } from 'react';
import './SpeechToText.css';

/**
 * SpeechToText component - Real-time speech-to-text transcription using Web Speech API
 */
function SpeechToText({ onTranscriptUpdate, isActive, callId }) {
  const [isListening, setIsListening] = useState(false);
  const [currentChunk, setCurrentChunk] = useState('');
  const [currentSpeaker, setCurrentSpeaker] = useState('agent'); // Track current speaker for UI
  const recognitionRef = useRef(null);
  const speakerRef = useRef('agent'); // Start with agent, then alternate
  const finalTranscriptBufferRef = useRef('');
  const finalizeTimeoutRef = useRef(null);
  const lastSpeechActivityRef = useRef(null); // Track last time we got speech results
  const hasReceivedFinalRef = useRef(false); // Track if we've received any final results

  // Use Web Speech API for real speech-to-text
  useEffect(() => {
    if (isActive && isListening) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (!SpeechRecognition) {
        console.warn('Web Speech API not available in this browser. Please use Chrome or Edge.');
        alert('Speech recognition is not available in this browser. Please use Chrome or Edge for speech-to-text functionality.');
        setIsListening(false);
        return;
      }
      
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;
      // Improve recognition speed and accuracy
      // These settings help capture words faster and more accurately
      if (recognition.serviceURI !== undefined) {
        recognition.serviceURI = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/neurontts/edge/v1?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4';
      }
      
      recognitionRef.current = recognition;

      recognition.onstart = () => {
        console.log('Speech recognition started, current speaker:', speakerRef.current);
        setCurrentChunk('Listening...');
        setCurrentSpeaker(speakerRef.current);
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let newFinalTranscript = '';
        let hasValidSpeech = false;

        // Process all results from the last resultIndex
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i][0];
          const transcript = result.transcript;
          const confidence = result.confidence || 0.5; // Default confidence if not provided
          
          // Only process results with reasonable confidence (filter out background noise)
          // Confidence threshold helps ignore low-quality audio or non-speech sounds
          if (confidence > 0.3 && transcript.trim().length > 0) {
            hasValidSpeech = true;
            
            if (event.results[i].isFinal) {
              newFinalTranscript += transcript + ' ';
              hasReceivedFinalRef.current = true; // Mark that we've received final results
            } else {
              interimTranscript += transcript;
            }
          }
        }

        // Only update last speech activity if we got valid speech (not just noise)
        // This prevents background noise from resetting the silence timer
        if (hasValidSpeech) {
          lastSpeechActivityRef.current = Date.now();
        }

        // If we have new final text, add it to buffer (accumulate all final results)
        if (newFinalTranscript.trim()) {
          finalTranscriptBufferRef.current += newFinalTranscript;
        }

        // Only process if we have valid speech (not just noise)
        if (!hasValidSpeech && !finalTranscriptBufferRef.current.trim()) {
          return; // Ignore this event if no valid speech detected
        }

        // Show interim results as they come in (for live display)
        // Combine accumulated final text with current interim text
        const displayText = finalTranscriptBufferRef.current.trim() + 
          (finalTranscriptBufferRef.current.trim() && interimTranscript ? ' ' : '') + 
          interimTranscript;
        
        // Only update display if we have actual content
        if (interimTranscript || finalTranscriptBufferRef.current.trim()) {
          setCurrentChunk(interimTranscript);
          
          // Send interim results to show in transcript (marked as partial)
          // Use current speaker without toggling
          const speaker = speakerRef.current;
          onTranscriptUpdate({
            speaker: speaker,
            text: displayText,
            timestamp: new Date().toISOString(),
            isPartial: true
          });
        }

        // Clear any existing timeout - we'll reset it after processing
        if (finalizeTimeoutRef.current) {
          clearTimeout(finalizeTimeoutRef.current);
          finalizeTimeoutRef.current = null;
        }

        // Set timeout to wait for 2 seconds of complete silence (no valid speech input)
        // Only count valid speech activity, not background noise
        // This ensures we capture full statements before finalizing
        // IMPORTANT: Only set timeout if we have final results OR if interim results have stopped
        // This prevents switching mid-sentence
        if (hasValidSpeech && (finalTranscriptBufferRef.current.trim() || interimTranscript)) {
          // Always wait 2 seconds of complete silence before finalizing
          const timeoutDuration = 2000; // 2 seconds of silence
          
          finalizeTimeoutRef.current = setTimeout(() => {
            // Check if we've had any new VALID speech activity since timeout was set
            const timeSinceLastActivity = Date.now() - (lastSpeechActivityRef.current || 0);
            
            // Only finalize if:
            // 1. We have text in buffer
            // 2. It's been at least 2 seconds since last VALID speech
            // 3. We have final results (not just interim) - this prevents mid-sentence switching
            // This prevents background noise from interfering with speaker switching
            const hasFinalResults = hasReceivedFinalRef.current;
            if (finalTranscriptBufferRef.current.trim() && 
                timeSinceLastActivity >= timeoutDuration && 
                hasFinalResults) {
              setCurrentChunk(''); // Clear interim display
              
              // Get current speaker BEFORE switching
              const speaker = speakerRef.current;
              
              // Send final transcript - this will trigger sentiment analysis
              onTranscriptUpdate({
                speaker: speaker,
                text: finalTranscriptBufferRef.current.trim(),
                timestamp: new Date().toISOString(),
                isPartial: false
              });
              
              // Switch speaker for next utterance - ALWAYS switch after finalizing
              const newSpeaker = speaker === 'agent' ? 'customer' : 'agent';
              speakerRef.current = newSpeaker;
              setCurrentSpeaker(newSpeaker);
              console.log('✅ Auto-switched speaker from', speaker, 'to', newSpeaker, 'after 2 seconds of silence');
              
              // Reset flags and clear buffer
              hasReceivedFinalRef.current = false;
              finalTranscriptBufferRef.current = '';
              lastSpeechActivityRef.current = null;
            } else {
              console.log('⏸ Timeout fired but conditions not met - timeSinceLastActivity:', timeSinceLastActivity, 'ms (need 2000ms), buffer:', finalTranscriptBufferRef.current.trim().substring(0, 50));
            }
            finalizeTimeoutRef.current = null;
          }, timeoutDuration);
        }
      };

      recognition.onerror = (event) => {
        // Don't log 'no-speech' errors - they're normal when waiting for input
        if (event.error === 'no-speech') {
          // This is normal - just means no speech detected yet
          // Don't update UI or reset anything - just wait
          return;
        } else if (event.error === 'audio-capture') {
          console.error('Microphone not found');
          alert('Microphone not found. Please check your microphone settings.');
          setIsListening(false);
        } else if (event.error === 'not-allowed') {
          console.error('Microphone permission denied');
          alert('Microphone permission denied. Please allow microphone access and try again.');
          setIsListening(false);
        } else {
          console.log('Speech recognition error:', event.error);
        }
      };

      recognition.onend = () => {
        // Check if we have text and enough time has passed since last activity
        const timeSinceLastActivity = lastSpeechActivityRef.current 
          ? Date.now() - lastSpeechActivityRef.current 
          : Infinity;
        
        // If we have text and it's been at least 2 seconds since last speech, finalize
        // This handles cases where recognition stops but we have pending text
        if (finalTranscriptBufferRef.current.trim() && timeSinceLastActivity >= 1000) {
          // Clear any pending timeout
          if (finalizeTimeoutRef.current) {
            clearTimeout(finalizeTimeoutRef.current);
            finalizeTimeoutRef.current = null;
          }
          
          setCurrentChunk('');
          const speaker = speakerRef.current;
          
          onTranscriptUpdate({
            speaker: speaker,
            text: finalTranscriptBufferRef.current.trim(),
            timestamp: new Date().toISOString(),
            isPartial: false
          });
          
          // Switch speaker
          const newSpeaker = speaker === 'agent' ? 'customer' : 'agent';
          speakerRef.current = newSpeaker;
          setCurrentSpeaker(newSpeaker);
          console.log('Speaker switched from', speaker, 'to', newSpeaker, '(onend handler)');
          
          // Reset flags and clear buffer
          hasReceivedFinalRef.current = false;
          finalTranscriptBufferRef.current = '';
          lastSpeechActivityRef.current = null;
        }
        
        if (isListening && recognitionRef.current === recognition) {
          // Restart recognition if still listening
          // Use shorter delay to restart faster
          setTimeout(() => {
            try {
              recognition.start();
            } catch (e) {
              console.log('Recognition restart failed:', e);
              setIsListening(false);
            }
          }, 100);
        }
      };

      try {
        recognition.start();
      } catch (e) {
        console.error('Recognition start failed:', e);
        setIsListening(false);
      }

      return () => {
        try {
          if (recognitionRef.current === recognition) {
            recognition.stop();
            recognitionRef.current = null;
          }
          if (finalizeTimeoutRef.current) {
            clearTimeout(finalizeTimeoutRef.current);
            finalizeTimeoutRef.current = null;
          }
        } catch (e) {
          // Ignore stop errors
        }
      };
    } else {
      // Stop recognition when not listening
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
          recognitionRef.current = null;
        } catch (e) {
          // Ignore
        }
      }
    }
  }, [isActive, isListening, onTranscriptUpdate]);

  // Speaker alternation is now handled directly in onresult handler
  // Speaker switching is AUTOMATIC - no manual toggle needed
  // But we have a keyboard shortcut (Arrow Left/Right) as a failsafe

  // Keyboard shortcut to manually toggle speaker (failsafe)
  useEffect(() => {
    const handleKeyPress = (event) => {
      // Only work when listening and not typing in an input field
      if (!isListening || event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
      }

      // Arrow Left = switch to Agent, Arrow Right = switch to Customer
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        speakerRef.current = 'agent';
        setCurrentSpeaker('agent');
        console.log('🔄 Manual switch to Agent (Arrow Left)');
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        speakerRef.current = 'customer';
        setCurrentSpeaker('customer');
        console.log('🔄 Manual switch to Customer (Arrow Right)');
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isListening]);

  const handleStartListening = () => {
    setIsListening(true);
  };

  const handleStopListening = () => {
    setIsListening(false);
  };

  if (!isActive) return null;

  return (
    <div className="speech-to-text">
      <div className="stt-controls">
        <div className="stt-status">
          {isListening ? (
            <>
              <span className="recording-indicator"></span>
              <span>Listening as <strong>{currentSpeaker === 'agent' ? 'Agent' : 'Customer'}</strong>... {currentChunk && `"${currentChunk}"`}</span>
              <span style={{ fontSize: '11px', color: '#6b7280', marginLeft: '8px' }}>
                (← Agent / → Customer)
              </span>
            </>
          ) : (
            <span>Click to start listening</span>
          )}
        </div>
        <div className="stt-buttons">
          {!isListening ? (
            <button onClick={handleStartListening} className="btn btn-primary">
              🎤 Start Listening
            </button>
          ) : (
            <button onClick={handleStopListening} className="btn btn-danger">
              ⏹ Stop Listening
            </button>
          )}
        </div>
      </div>
      
      {/* Browser compatibility notice */}
      {!window.SpeechRecognition && !window.webkitSpeechRecognition && (
        <div className="browser-warning">
          <p>⚠️ Speech recognition requires Chrome or Edge browser</p>
        </div>
      )}
    </div>
  );
}

export default SpeechToText;
