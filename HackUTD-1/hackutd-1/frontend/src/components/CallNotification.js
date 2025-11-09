import React from 'react';
import './CallNotification.css';

function CallNotification({ call, onAccept, onDismiss }) {
  if (!call) return null;

  return (
    <div className="call-notification">
      <div className="notification-content">
        <div className="notification-header">
          <div className="notification-icon">📞</div>
          <div className="notification-info">
            <h3>New Call Incoming</h3>
            <p>Phone: {call.phoneNumber || 'Unknown'}</p>
            {call.customerName && <p className="customer-name">{call.customerName}</p>}
          </div>
        </div>
        <div className="notification-preview">
          <p className="preview-text">{call.initialText || 'Call routed from agent...'}</p>
          <div className="preview-sentiment">
            <span className={`sentiment-badge sentiment-${call.initialSentiment?.label || 'neutral'}`}>
              {call.initialSentiment?.label || 'neutral'}
            </span>
            <span className={`urgency-badge urgency-${call.initialUrgency?.level?.toLowerCase() || 'low'}`}>
              {call.initialUrgency?.level || 'LOW'} Urgency
            </span>
          </div>
        </div>
        <div className="notification-actions">
          <button onClick={() => onAccept(call)} className="btn btn-primary">
            Accept Call
          </button>
          <button onClick={onDismiss} className="btn btn-secondary">
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

export default CallNotification;

