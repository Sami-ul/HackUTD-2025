import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import './App.css';
import Dashboard from './components/Dashboard';
import CallNotification from './components/CallNotification';

// Use proxy from package.json (empty string uses proxy) or direct URL
const API_URL = process.env.REACT_APP_API_URL || '';

function App() {
  const [activeCall, setActiveCall] = useState(null);
  const [pendingCalls, setPendingCalls] = useState([]);
  const [currentNotification, setCurrentNotification] = useState(null);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Initialize socket connection
    // Use proxy (window.location.origin) so Socket.IO goes through the proxy
    // This avoids CORS issues since the browser sees it as same-origin
    const socketUrl = API_URL || window.location.origin;
    const newSocket = io(socketUrl, {
      transports: ['polling', 'websocket'], // Try polling first, then upgrade to websocket
      withCredentials: false, // Disable credentials for CORS
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      path: '/socket.io'  // Explicit path
    });
    setSocket(newSocket);

    // Listen for new incoming calls
    newSocket.on('new_call', (callData) => {
      setPendingCalls(prev => [...prev, callData]);
      setCurrentNotification(callData);
    });

    // Poll for pending calls (fallback if WebSocket doesn't work)
    const pollPendingCalls = async () => {
      try {
        // Use proxy if API_URL is empty, otherwise use direct URL
        const apiBase = API_URL || '/api';
        const response = await axios.get(`${apiBase}/calls/pending`);
        if (response.data && response.data.length > 0) {
          const latestCall = response.data[0];
          // Only show if we don't already have it
          if (!pendingCalls.find(c => c.call_id === latestCall.call_id)) {
            setPendingCalls(prev => [...prev, latestCall]);
            if (!currentNotification) {
              setCurrentNotification(latestCall);
            }
          }
        }
      } catch (error) {
        console.log('Error polling pending calls:', error.message);
      }
    };

    // Poll every 3 seconds for new calls
    const pollInterval = setInterval(pollPendingCalls, 3000);
    pollPendingCalls(); // Initial poll

    return () => {
      clearInterval(pollInterval);
      newSocket.close();
    };
  }, []);

  const handleAcceptCall = async (call) => {
    try {
      // Accept the call via API
      // Use proxy if API_URL is empty, otherwise use direct URL
      const apiBase = API_URL || '/api';
      const response = await axios.post(`${apiBase}/calls/${call.call_id}/accept`);
      const callData = response.data;
      
      // Join WebSocket room for this call
      if (socket) {
        socket.emit('join_call', { call_id: call.call_id });
      }

      // Parse initial transcript into structured format
      const parseInitialTranscript = (text) => {
        if (!text) return [];
        const lines = text.split('\n');
        const parsed = [];
        let currentSpeaker = null;
        let currentText = [];
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          
          const lower = trimmed.toLowerCase();
          if (lower.startsWith('customer:') || lower.startsWith('customer ')) {
            if (currentSpeaker && currentText.length > 0) {
              parsed.push({
                speaker: currentSpeaker,
                text: currentText.join(' '),
                timestamp: new Date().toISOString()
              });
            }
            currentSpeaker = 'customer';
            const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(8).trim();
            currentText = text ? [text] : [];
          } else if (lower.startsWith('agent:') || lower.startsWith('agent ')) {
            if (currentSpeaker && currentText.length > 0) {
              parsed.push({
                speaker: currentSpeaker,
                text: currentText.join(' '),
                timestamp: new Date().toISOString()
              });
            }
            currentSpeaker = 'agent';
            const text = trimmed.includes(':') ? trimmed.split(':', 2)[1].trim() : trimmed.substring(5).trim();
            currentText = text ? [text] : [];
          } else if (currentSpeaker) {
            currentText.push(trimmed);
          }
        }
        
        if (currentSpeaker && currentText.length > 0) {
          parsed.push({
            speaker: currentSpeaker,
            text: currentText.join(' '),
            timestamp: new Date().toISOString()
          });
        }
        
        return parsed;
      };
      
      const parsedInitialTranscript = parseInitialTranscript(callData.initial_transcript || '');
      
      // Build sentiment history from initial analysis
      const initialSentimentHistory = [];
      if (callData.initial_analysis) {
        initialSentimentHistory.push({
          timestamp: new Date().toISOString(),
          sentiment: callData.initial_analysis.sentiment || { label: 'neutral', score: 0 },
          emotion: callData.initial_analysis.emotion || 'neutral',
          urgency: callData.initial_analysis.urgency || { level: 'LOW', score: 0 }
        });
      }
      
      // Combine with existing sentiment history (ensure proper format)
      const existingHistory = (callData.sentiment_history || []).map(item => {
        if (typeof item === 'object' && item !== null) {
          return {
            timestamp: item.timestamp || new Date().toISOString(),
            sentiment: item.sentiment || { label: 'neutral', score: 0 },
            emotion: item.emotion || 'neutral',
            urgency: item.urgency || { level: 'LOW', score: 0 }
          };
        }
        return item;
      });
      
      const allSentimentHistory = [
        ...initialSentimentHistory,
        ...existingHistory
      ];

      // Set as active call
      setActiveCall({
        callId: callData.call_id || call.call_id,
        phoneNumber: callData.phone_number || call.phone_number || 'Unknown',
        customerInfo: callData.customer_info || null,
        initialAnalysis: callData.initial_analysis || null,
        initialTranscript: [...parsedInitialTranscript, ...(callData.transcript || [])],
        initialSentimentHistory: allSentimentHistory,
        fullTranscript: callData.initial_transcript || call.initial_transcript || ''
      });

      // Remove from pending and notification
      setPendingCalls(prev => prev.filter(c => c.call_id !== call.call_id));
      setCurrentNotification(null);
    } catch (error) {
      console.error('Error accepting call:', error);
      alert(`Error accepting call: ${error.message || 'Unknown error'}`);
    }
  };

  const handleDismissNotification = () => {
    setCurrentNotification(null);
  };

  const handleCallEnd = () => {
    if (socket && activeCall) {
      socket.emit('leave_call', { call_id: activeCall.callId });
    }
    setActiveCall(null);
    
    // Show next pending call if available
    if (pendingCalls.length > 0) {
      const nextCall = pendingCalls.find(c => c.call_id !== currentNotification?.call_id) || pendingCalls[0];
      setCurrentNotification(nextCall);
    }
  };

  return (
    <div className="App">
      {/* Show notification for pending calls */}
      {currentNotification && !activeCall && (
        <CallNotification
          call={currentNotification}
          onAccept={handleAcceptCall}
          onDismiss={handleDismissNotification}
        />
      )}

      {/* Show dashboard for active call */}
      {activeCall ? (
        <Dashboard
          callId={activeCall.callId}
          phoneNumber={activeCall.phoneNumber}
          customerInfo={activeCall.customerInfo}
          initialAnalysis={activeCall.initialAnalysis}
          initialTranscript={activeCall.initialTranscript}
          initialSentimentHistory={activeCall.initialSentimentHistory}
          socket={socket}
          onCallEnd={handleCallEnd}
        />
      ) : (
        <div className="waiting-screen">
          <div className="waiting-content">
            <h1>Human Responder Dashboard</h1>
            <p>Waiting for incoming calls...</p>
            {pendingCalls.length > 0 && (
              <p className="pending-count">
                {pendingCalls.length} call{pendingCalls.length > 1 ? 's' : ''} pending
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
