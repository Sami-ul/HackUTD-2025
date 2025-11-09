import React, { useEffect, useState } from 'react';
import './AISuggestions.css';
import { getRelevantPolicies, getPolicyText } from '../data/tmobile_policies';

function AISuggestions({ customerInfo, currentSentiment, currentEmotion, currentUrgency, recentTranscript }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Debounce to avoid regenerating on every tiny transcript change
    const timeoutId = setTimeout(() => {
      generateSuggestions();
    }, 300); // Wait 300ms after transcript changes before regenerating
    
    return () => clearTimeout(timeoutId);
  }, [customerInfo, currentSentiment, currentEmotion, currentUrgency, recentTranscript]);

  const generateSuggestions = () => {
    setLoading(true);
    
    // Get last few customer statements for context
    const customerStatements = recentTranscript
      .filter(line => line.speaker === 'customer' && !line.isPartial)
      .slice(-3)
      .map(line => line.text)
      .join(' ');

    // Extract keywords from customer statements
    const keywords = customerStatements.toLowerCase().split(/\s+/).filter(word => 
      word.length > 3 && !['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'].includes(word)
    );

    // Determine category based on keywords
    let category = 'general';
    if (keywords.some(k => ['bill', 'charge', 'payment', 'refund', 'cost', 'price', 'fee'].includes(k))) {
      category = 'billing';
    } else if (keywords.some(k => ['coverage', 'signal', 'network', 'connection', 'data', 'internet'].includes(k))) {
      category = 'network';
    } else if (keywords.some(k => ['phone', 'device', 'upgrade', 'warranty', 'broken', 'screen'].includes(k))) {
      category = 'device';
    } else if (keywords.some(k => ['cancel', 'switch', 'leave', 'port', 'disconnect'].includes(k))) {
      category = 'cancellation';
    }

    // Generate AI-powered suggestions based on context
    const newSuggestions = [];

    // Analyze sentiment and emotion
    const sentimentLabel = currentSentiment?.label || 'neutral';
    const emotion = currentEmotion || 'neutral';
    const urgency = currentUrgency?.level || 'LOW';
    const urgencyScore = currentUrgency?.score || 0;

    // Get relevant T-Mobile policies
    // Pass urgency level as string, not the whole urgency object
    const relevantPolicies = getRelevantPolicies({ 
      category, 
      keywords, 
      sentiment: currentSentiment, 
      urgency: urgency // This is already extracted as 'LOW', 'MEDIUM', or 'HIGH'
    });

    // Get customer context
    const customerName = customerInfo?.name || 'the customer';
    const accountType = customerInfo?.account_type || 'standard';
    const hasIssues = customerInfo?.recent_issues?.length > 0;

    // Suggestion 1: Empathy and acknowledgment
    if (sentimentLabel.includes('negative') || emotion === 'frustrated' || emotion === 'angry') {
      newSuggestions.push({
        type: 'empathy',
        priority: 'high',
        text: `Acknowledge ${customerName}'s frustration: "I completely understand your frustration, and I'm here to help resolve this for you today."`,
        reasoning: 'Customer is showing negative sentiment - start with empathy'
      });
    }

    // Suggestion 2: Urgency-based response
    if (urgencyScore > 0.7 || urgency === 'HIGH') {
      newSuggestions.push({
        type: 'urgency',
        priority: 'high',
        text: 'Offer immediate escalation: "I can escalate this to our priority support team right away to get this resolved quickly."',
        reasoning: 'High urgency detected - offer immediate action'
      });
    }

    // Suggestion 3: Service-specific suggestions with T-Mobile policies
    if (category === 'billing') {
      const billingPolicies = relevantPolicies.filter(p => 
        p.toLowerCase().includes('payment') || 
        p.toLowerCase().includes('refund') || 
        p.toLowerCase().includes('credit')
      );
      
      newSuggestions.push({
        type: 'billing',
        priority: 'medium',
        text: `Review ${customerName}'s billing history and explain any charges clearly. ${billingPolicies.length > 0 ? `Per T-Mobile policy: ${billingPolicies[0]}` : 'Offer to set up payment plan if needed.'}`,
        reasoning: 'Billing-related concern detected - using T-Mobile billing policies',
        policyReference: billingPolicies[0] || null
      });
    }

    if (category === 'network') {
      const networkPolicies = relevantPolicies.filter(p => 
        p.toLowerCase().includes('coverage') || 
        p.toLowerCase().includes('network') || 
        p.toLowerCase().includes('signal')
      );
      
      newSuggestions.push({
        type: 'technical',
        priority: 'medium',
        text: `Check network coverage in their area and troubleshoot connection issues. ${networkPolicies.length > 0 ? `Per T-Mobile policy: ${networkPolicies[0]}` : 'Offer network optimization tips.'}`,
        reasoning: 'Network/coverage issue mentioned - using T-Mobile network policies',
        policyReference: networkPolicies[0] || null
      });
    }

    if (category === 'cancellation') {
      const retentionPolicies = relevantPolicies.filter(p => 
        p.toLowerCase().includes('retention') || 
        p.toLowerCase().includes('cancellation') || 
        p.toLowerCase().includes('offer')
      );
      
      newSuggestions.push({
        type: 'retention',
        priority: 'high',
        text: `This is a retention opportunity. Acknowledge their concerns, offer solutions, and highlight value: "I'd hate to see you go. Let me see what I can do to make this right for you." ${retentionPolicies.length > 0 ? `Per T-Mobile retention policy: ${retentionPolicies[0]}` : ''}`,
        reasoning: 'Customer considering cancellation - retention critical - using T-Mobile retention protocols',
        policyReference: retentionPolicies[0] || null
      });
    }

    // Add policy-based suggestions
    if (relevantPolicies.length > 0) {
      relevantPolicies.slice(0, 2).forEach((policy, idx) => {
        if (!newSuggestions.some(s => s.policyReference === policy)) {
          newSuggestions.push({
            type: 'policy',
            priority: 'medium',
            text: `T-Mobile Policy: ${policy}`,
            reasoning: 'Relevant T-Mobile policy for this situation',
            policyReference: policy
          });
        }
      });
    }

    // Suggestion 4: Account-specific
    if (accountType === 'premium' || accountType === 'business') {
      newSuggestions.push({
        type: 'account',
        priority: 'medium',
        text: `As a ${accountType} customer, ${customerName} has access to priority support. Leverage this to provide exceptional service.`,
        reasoning: 'Premium account - emphasize value'
      });
    }

    // Suggestion 5: Problem-solving approach
    if (hasIssues && sentimentLabel.includes('negative')) {
      newSuggestions.push({
        type: 'resolution',
        priority: 'high',
        text: `Address their recent issues directly: "I see you've had some challenges recently. Let me work with you to ensure we get everything resolved today."`,
        reasoning: 'Customer has recent issues - proactive resolution needed'
      });
    }

    // Suggestion 6: Positive reinforcement
    if (sentimentLabel.includes('positive') || emotion === 'satisfied' || emotion === 'happy') {
      newSuggestions.push({
        type: 'engagement',
        priority: 'low',
        text: 'Customer is satisfied - maintain positive experience and offer additional value or services.',
        reasoning: 'Positive sentiment - opportunity to upsell or add value'
      });
    }

    // Suggestion 7: General best practice
    if (newSuggestions.length === 0) {
      newSuggestions.push({
        type: 'general',
        priority: 'medium',
        text: `Listen actively to ${customerName}'s needs and provide clear, actionable solutions. Confirm understanding before proceeding.`,
        reasoning: 'General best practice for customer service'
      });
    }

    // Sort by priority (high first)
    newSuggestions.sort((a, b) => {
      const priorityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });

    setSuggestions(newSuggestions.slice(0, 5)); // Show top 5 suggestions
    setLoading(false);
  };

  const getSuggestionIcon = (type) => {
    const icons = {
      'empathy': '💙',
      'urgency': '⚡',
      'billing': '💳',
      'technical': '🔧',
      'retention': '🎯',
      'account': '⭐',
      'resolution': '✅',
      'engagement': '😊',
      'general': '💡'
    };
    return icons[type] || '💡';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'high': '#ef4444',
      'medium': '#f59e0b',
      'low': '#10b981'
    };
    return colors[priority] || '#6b7280';
  };

  return (
    <div className="ai-suggestions">
      <div className="suggestions-content">
        <div className="suggestions-header">💡 AI-Powered Response Suggestions</div>
          {loading ? (
            <div className="suggestions-loading">
              <p>Generating suggestions...</p>
            </div>
          ) : suggestions.length === 0 ? (
            <div className="suggestions-empty">
              <p>No suggestions available at this time.</p>
            </div>
          ) : (
            <div className="suggestions-list">
              {suggestions.map((suggestion, idx) => (
                <div key={idx} className="suggestion-item">
                  <div className="suggestion-header">
                    <span className="suggestion-icon">{getSuggestionIcon(suggestion.type)}</span>
                    <span 
                      className="suggestion-priority"
                      style={{ color: getPriorityColor(suggestion.priority) }}
                    >
                      {suggestion.priority.toUpperCase()}
                    </span>
                  </div>
                  <div className="suggestion-text">{suggestion.text}</div>
                  {suggestion.policyReference && (
                    <div className="suggestion-policy">
                      <small>📋 Policy Reference</small>
                    </div>
                  )}
                  <div className="suggestion-reasoning">
                    <small>💭 {suggestion.reasoning}</small>
                  </div>
                </div>
              ))}
            </div>
          )}
      </div>
    </div>
  );
}

export default AISuggestions;

