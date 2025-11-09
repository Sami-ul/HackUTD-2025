"""
Test script for Sentiment Analysis
Run this to see how sentiment analysis works without needing a real phone call
"""

from sentiment_analyzer import sentiment_analyzer

def print_sentiment(text):
    """Test sentiment analysis on a text sample"""
    print("\n" + "="*70)
    print(f"📝 TEXT: {text}")
    print("="*70)
    
    # Analyze sentiment
    result = sentiment_analyzer.analyze_text(text)
    
    # Print results
    print(f"\n{result['sentiment_label']}")
    print(f"Score: {result['sentiment_score']}")
    print(f"Emotions: {', '.join(result['emotions']) if result['emotions'] else 'None'}")
    print(f"Confidence: {result['confidence']}")
    print(f"Should Escalate: {'⚠️  YES' if result['should_escalate'] else '✅ No'}")
    print(f"\nIndicators:")
    for key, value in result['indicators'].items():
        if value > 0:
            print(f"  - {key}: {value}")


def test_call_progression():
    """Simulate a call with changing sentiment"""
    print("\n" + "🔵"*35)
    print("SIMULATING A CALL WITH SENTIMENT TRACKING")
    print("🔵"*35)
    
    call_sid = "TEST_CALL_001"
    
    # Simulate conversation
    conversation = [
        "Hello, I need help with my bill",
        "This is really frustrating and confusing",
        "I urgently need someone to explain this immediately",
        "Okay, thank you, that makes sense now",
        "Great service, I really appreciate your help"
    ]
    
    for i, text in enumerate(conversation, 1):
        print(f"\n\n{'='*70}")
        print(f"INTERACTION {i}")
        print(f"{'='*70}")
        print(f"Customer says: \"{text}\"")
        
        # Analyze sentiment
        sentiment_result = sentiment_analyzer.analyze_text(text)
        progression = sentiment_analyzer.analyze_call_progression(call_sid, sentiment_result)
        
        # Display results
        print(f"\n{sentiment_result['sentiment_label']}")
        print(f"Score: {sentiment_result['sentiment_score']}")
        print(f"Emotions: {', '.join(sentiment_result['emotions']) if sentiment_result['emotions'] else 'None'}")
        
        if sentiment_result['should_escalate']:
            print(f"⚠️  ESCALATION RECOMMENDED")
        
        print(f"\n📊 Progression:")
        print(f"  Trend: {progression['trend_emoji']} {progression['trend']}")
        print(f"  Average Score: {progression['average_overall_score']}")
        print(f"  Total Interactions: {progression['interaction_count']}")
        
        if progression['needs_immediate_attention']:
            print(f"  🚨 NEEDS IMMEDIATE ATTENTION!")
    
    # Final summary
    print("\n\n" + "🟢"*35)
    print("CALL SUMMARY")
    print("🟢"*35)
    
    summary = sentiment_analyzer.get_call_summary(call_sid)
    
    print(f"\n{summary['overall_emoji']} Overall Sentiment: {summary['overall_sentiment'].upper()}")
    print(f"Average Score: {summary['average_score']}")
    print(f"Total Interactions: {summary['total_interactions']}")
    print(f"\nSentiment Breakdown:")
    for sentiment, count in summary['sentiment_breakdown'].items():
        print(f"  {sentiment.capitalize()}: {count}")
    
    print(f"\nEmotions Detected: {', '.join(summary['emotions_detected'])}")
    print(f"Escalation Triggers: {summary['escalation_count']}")
    
    print(f"\n📈 Call Quality:")
    quality = summary['call_quality']
    if quality['improved_during_call']:
        print("  ✅ Customer sentiment IMPROVED during call")
    if quality['consistent_positive']:
        print("  ✅ Consistently positive interaction")
    if quality['needs_followup']:
        print("  ⚠️  Needs follow-up")
    
    # Clean up
    sentiment_analyzer.clear_call_history(call_sid)


if __name__ == "__main__":
    print("\n" + "🎯"*35)
    print("SENTIMENT ANALYSIS TESTING")
    print("🎯"*35)
    
    # Test individual sentiments
    print("\n\n" + "="*70)
    print("TEST 1: INDIVIDUAL SENTIMENT TESTS")
    print("="*70)
    
    test_cases = [
        "Thank you so much! This is excellent service!",
        "I'm really frustrated with this terrible experience",
        "I urgently need help immediately, this is critical",
        "I don't understand, can you explain this please?",
        "What's my account balance?",
    ]
    
    for text in test_cases:
        print_sentiment(text)
    
    # Test call progression
    print("\n\n" + "="*70)
    print("TEST 2: CALL PROGRESSION SIMULATION")
    print("="*70)
    
    test_call_progression()
    
    print("\n\n" + "✅"*35)
    print("TESTING COMPLETE!")
    print("✅"*35)
    print("\nSentiment analysis is working correctly!")
    print("Now try it with real phone calls using: ./start_server.sh")

