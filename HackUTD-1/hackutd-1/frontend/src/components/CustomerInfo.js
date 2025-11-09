import React from 'react';
import './CustomerInfo.css';

function CustomerInfo({ customerInfo, phoneNumber }) {
  if (!customerInfo) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Customer Information</h3>
        </div>
        <div className="customer-info">
          <p><strong>Phone:</strong> {phoneNumber}</p>
          <p className="info-note">Customer not found in database</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Customer Information</h3>
      </div>
      <div className="customer-info">
        <div className="info-row">
          <span className="info-label">Name:</span>
          <span className="info-value">{customerInfo.name}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Phone:</span>
          <span className="info-value">{customerInfo.phone_number}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Account ID:</span>
          <span className="info-value">{customerInfo.account_id}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Plan:</span>
          <span className="info-value">{customerInfo.plan}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Monthly Bill:</span>
          <span className="info-value">${customerInfo.monthly_bill.toFixed(2)}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Location:</span>
          <span className="info-value">{customerInfo.location}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Account Age:</span>
          <span className="info-value">{customerInfo.account_age_months} months</span>
        </div>
        <div className="info-row">
          <span className="info-label">Previous Calls:</span>
          <span className="info-value">{customerInfo.previous_calls}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Last Sentiment:</span>
          <span className={`info-value sentiment-badge sentiment-${customerInfo.previous_sentiment}`}>
            {customerInfo.previous_sentiment}
          </span>
        </div>
        {customerInfo.notes && (
          <div className="info-notes">
            <strong>Notes:</strong>
            <p>{customerInfo.notes}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default CustomerInfo;

