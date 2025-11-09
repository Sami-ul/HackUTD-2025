import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './Dashboard.css';
import CustomerInfo from './CustomerInfo';
import TranscriptPanel from './TranscriptPanel';
import SentimentPanel from './SentimentPanel';
import AISuggestions from './AISuggestions';
import SpeechToText from './SpeechToText';

// Use proxy from package.json (empty string uses proxy) or direct URL
const API_URL = process.env.REACT_APP_API_URL || '';

function Dashboard({ callId, phoneNumber, customerInfo, assignedCSR, initialAnalysis, initialTranscript, initialSentimentHistory, socket, onCallEnd }) {
  // Auto-load customer info if phone number provided but info not loaded
  const [loadedCustomerInfo, setLoadedCustomerInfo] = useState(customerInfo);
  const [transcript, setTranscript] = useState(initialTranscript || []);
  const [sentimentHistory, setSentimentHistory] = useState(initialSentimentHistory || []);
  const [currentSentiment, setCurrentSentiment] = useState(
    initialAnalysis?.sentiment || { label: 'neutral', score: 0 }
  );
  const [currentEmotion, setCurrentEmotion] = useState(initialAnalysis?.emotion || 'neutral');
  const [currentUrgency, setCurrentUrgency] = useState(
    initialAnalysis?.urgency || { level: 'LOW', score: 0 }
  );

  const loadCallStatus = React.useCallback(async () => {
    try {
      // Use proxy if API_URL is empty, otherwise use direct URL
      const apiBase = API_URL || '/api';
      const response = await axios.get(`${apiBase}/call/${callId}`);
      setTranscript(response.data.transcript || []);
      setSentimentHistory(response.data.sentiment_history.map((item, idx) => ({
        time: new Date(item.timestamp).toLocaleTimeString(),
        score: item.sentiment.score,
        label: item.sentiment.label
      })));
      if (response.data.current_sentiment) {
        setCurrentSentiment(response.data.current_sentiment);
      }
    } catch (error) {
      console.error('Error loading call status:', error);
    }
  }, [callId]);

  // Auto-load customer info when call is accepted
  useEffect(() => {
    if (phoneNumber && phoneNumber !== 'Unknown' && !loadedCustomerInfo) {
      const loadCustomerInfo = async () => {
        try {
          // Use proxy if API_URL is empty, otherwise use direct URL
          const apiBase = API_URL || '/api';
          const response = await axios.get(`${apiBase}/customer/${phoneNumber}`);
          setLoadedCustomerInfo(response.data);
        } catch (error) {
          console.log('Could not load customer info:', error.message);
        }
      };
      loadCustomerInfo();
    }
  }, [phoneNumber, loadedCustomerInfo]);

  useEffect(() => {
    // If we have initial transcript and sentiment history, use them
    if (initialTranscript && initialTranscript.length > 0) {
      setTranscript(initialTranscript);
    }
    if (initialSentimentHistory && initialSentimentHistory.length > 0) {
      // Format sentiment history for display
      const formatted = initialSentimentHistory.map(item => {
        if (item.sentiment) {
          // Already formatted with sentiment object
          return {
            timestamp: item.timestamp || new Date().toISOString(),
            sentiment: item.sentiment,
            emotion: item.emotion || 'neutral',
            urgency: item.urgency || { level: 'LOW', score: 0 }
          };
        } else {
          // Legacy format - convert
          return {
            timestamp: item.timestamp || new Date().toISOString(),
            sentiment: { 
              label: item.label || 'neutral', 
              score: typeof item.score === 'number' ? item.score : 0 
            },
            emotion: item.emotion || 'neutral',
            urgency: item.urgency || { level: 'LOW', score: 0 }
          };
        }
      });
      setSentimentHistory(formatted);
      
      // Set current sentiment from last item
      if (formatted.length > 0) {
        const last = formatted[formatted.length - 1];
        setCurrentSentiment(last.sentiment);
        setCurrentEmotion(last.emotion);
        setCurrentUrgency(last.urgency);
      }
    }
    
    // Only load call status if we don't have initial data
    if (!initialTranscript || initialTranscript.length === 0) {
      loadCallStatus();
    }

    // Set up WebSocket listeners for real-time transcript chunks
    if (socket) {
      // Join the call room
      socket.emit('join_call', { call_id: callId });

      socket.on('transcript_chunk', (data) => {
        if (data.call_id === callId) {
          // Add to transcript (both partial and final)
          if (data.is_partial) {
            // Update last partial entry or add new
            setTranscript(prev => {
              const newTranscript = [...prev];
              const lastIndex = newTranscript.length - 1;
              if (lastIndex >= 0 && 
                  newTranscript[lastIndex].speaker === data.speaker && 
                  newTranscript[lastIndex].isPartial) {
                newTranscript[lastIndex] = {
                  speaker: data.speaker,
                  text: data.text,
                  timestamp: data.timestamp,
                  isPartial: true
                };
                return newTranscript;
              } else {
                return [...newTranscript, {
                  speaker: data.speaker,
                  text: data.text,
                  timestamp: data.timestamp,
                  isPartial: true
                }];
              }
            });
          } else {
            // Final transcript - replace partial if exists, otherwise add
            setTranscript(prev => {
              const newTranscript = [...prev];
              const filtered = newTranscript.filter(
                (item, idx) => !(item.speaker === data.speaker && item.isPartial && idx === newTranscript.length - 1)
              );
              return [...filtered, {
                speaker: data.speaker,
                text: data.text,
                timestamp: data.timestamp,
                isPartial: false
              }];
            });

            // Update sentiment if analysis provided (customer text only)
            if (data.analysis && data.speaker === 'customer') {
              setCurrentSentiment(data.analysis.sentiment);
              setCurrentEmotion(data.analysis.emotion);
              setCurrentUrgency(data.analysis.urgency);
              
              // Add to sentiment history
              setSentimentHistory(prev => [...prev, {
                timestamp: data.timestamp,
                sentiment: data.analysis.sentiment,
                emotion: data.analysis.emotion,
                urgency: data.analysis.urgency
              }]);
            }
          }
        }
      });

      socket.on('call_state', (data) => {
        if (data.call_id === callId) {
          // Update with current call state
          setTranscript(data.transcript || []);
          setSentimentHistory(data.sentiment_history || []);
        }
      });

      socket.on('joined', (data) => {
        console.log('Joined call room:', data);
      });
    }

    return () => {
      if (socket) {
        socket.off('transcript_chunk');
        socket.off('call_state');
        socket.off('joined');
      }
    };
  }, [socket, callId, initialTranscript, initialSentimentHistory, loadCallStatus]);

  const handleTranscriptChunk = async (chunkData) => {
    // Update transcript immediately (for both partial and final)
    if (chunkData.isPartial) {
      // For interim results, always update the last transcript line if it's partial
      // This ensures we see every word as it's spoken
      setTranscript(prev => {
        const newTranscript = [...prev];
        const lastIndex = newTranscript.length - 1;
        
        // If last entry is partial for same speaker, update it
        if (lastIndex >= 0 && 
            newTranscript[lastIndex].speaker === chunkData.speaker && 
            newTranscript[lastIndex].isPartial) {
          newTranscript[lastIndex] = {
            speaker: chunkData.speaker,
            text: chunkData.text, // This includes accumulated final + interim
            timestamp: chunkData.timestamp,
            isPartial: true
          };
          return newTranscript;
        } else {
          // Add new partial entry
          return [...newTranscript, {
            speaker: chunkData.speaker,
            text: chunkData.text,
            timestamp: chunkData.timestamp,
            isPartial: true
          }];
        }
      });
      return; // Don't send partial results to API
    }

    // For final results, add to transcript and send to API for sentiment analysis
    try {
      // Add to transcript immediately (replace partial if exists)
      setTranscript(prev => {
        const newTranscript = [...prev];
        // Remove any partial entry for this speaker (check last few entries)
        const filtered = [];
        let foundPartial = false;
        for (let i = newTranscript.length - 1; i >= 0; i--) {
          const item = newTranscript[i];
          if (!foundPartial && item.speaker === chunkData.speaker && item.isPartial) {
            foundPartial = true;
            // Skip this partial entry
            continue;
          }
          filtered.unshift(item);
        }
        // Add final entry
        return [...filtered, {
          speaker: chunkData.speaker,
          text: chunkData.text,
          timestamp: chunkData.timestamp,
          isPartial: false
        }];
      });

      // IMPORTANT: Only analyze sentiment for customer text, NOT agent text
      // Send to API for sentiment analysis (only for customer text)
      if (chunkData.speaker === 'customer') {
        const apiBase = API_URL || '/api';
        const response = await axios.post(`${apiBase}/calls/${callId}/transcript`, {
          speaker: chunkData.speaker,
          text: chunkData.text,
          is_partial: false
        });

        // Update sentiment if analysis provided (only for customer)
        if (response.data && response.data.analysis) {
          setCurrentSentiment(response.data.analysis.sentiment);
          setCurrentEmotion(response.data.analysis.emotion);
          setCurrentUrgency(response.data.analysis.urgency);
          
          // Add to sentiment history
          setSentimentHistory(prev => [...prev, {
            timestamp: chunkData.timestamp,
            sentiment: response.data.analysis.sentiment,
            emotion: response.data.analysis.emotion,
            urgency: response.data.analysis.urgency
          }]);
        }
      } else {
        // For agent/CSR text, just send to API for storage (NO sentiment analysis)
        // This ensures agent statements don't affect sentiment scores
        const apiBase = API_URL || '/api';
        await axios.post(`${apiBase}/calls/${callId}/transcript`, {
          speaker: chunkData.speaker,
          text: chunkData.text,
          is_partial: false
        });
        // Explicitly do NOT update sentiment for agent text
      }
    } catch (error) {
      // Transcript is already updated, so continue
      // If API fails, we still show the transcript
    }
  };

  // Calculate sentiment change from history
  const sentimentChange = sentimentHistory.length > 1
    ? (sentimentHistory[sentimentHistory.length - 1]?.sentiment?.score || currentSentiment.score) - 
      (sentimentHistory[0]?.sentiment?.score || currentSentiment.score)
    : 0;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Active Call Dashboard</h1>
          <p>Call ID: {callId}</p>
        </div>
        <button onClick={onCallEnd} className="btn btn-danger">
          End Call
        </button>
      </div>

      <div className="dashboard-grid">
        {/* Left Column */}
        <div className="dashboard-left">
          <CustomerInfo customerInfo={loadedCustomerInfo || customerInfo} phoneNumber={phoneNumber} />
          <AISuggestions 
            customerInfo={loadedCustomerInfo || customerInfo}
            currentSentiment={currentSentiment}
            currentEmotion={currentEmotion}
            currentUrgency={currentUrgency}
            recentTranscript={transcript}
          />
        </div>

        {/* Center Column */}
        <div className="dashboard-center">
          <SpeechToText
            onTranscriptUpdate={handleTranscriptChunk}
            isActive={true}
            callId={callId}
          />
          <TranscriptPanel
            transcript={transcript}
            onAddLine={handleTranscriptChunk}
          />
        </div>

        {/* Right Column */}
        <div className="dashboard-right">
          <SentimentPanel
            currentSentiment={currentSentiment}
            currentEmotion={currentEmotion}
            currentUrgency={currentUrgency}
            sentimentHistory={sentimentHistory}
            sentimentChange={sentimentChange}
          />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

