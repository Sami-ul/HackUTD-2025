"""
Real-time Sentiment Analysis for Voice Calls
Analyzes customer emotion and sentiment during live conversations
"""

import logging
from typing import Dict, List, Tuple
import re

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        """
        Initialize sentiment analyzer
        Uses multiple approaches for robust sentiment detection
        """
        self.sentiment_history = {}
        
        # Emotion/sentiment keywords
        self.positive_words = {
            'thank', 'thanks', 'great', 'good', 'excellent', 'perfect', 'happy',
            'appreciate', 'wonderful', 'awesome', 'love', 'helpful', 'pleased',
            'satisfied', 'amazing', 'fantastic'
        }
        
        self.negative_words = {
            'frustrated', 'angry', 'upset', 'disappointed', 'horrible', 'terrible',
            'awful', 'hate', 'worst', 'useless', 'annoyed', 'irritated', 'mad',
            'furious', 'disappointed', 'unacceptable', 'ridiculous', 'stupid'
        }
        
        self.urgency_words = {
            'urgent', 'immediately', 'asap', 'now', 'emergency', 'critical',
            'serious', 'important', 'must', 'need', 'quickly', 'hurry'
        }
        
        self.confusion_words = {
            'confused', 'understand', 'explain', 'what', 'how', 'why', 'clarify',
            'unclear', "don't get", 'lost', 'complicated'
        }
        
        logger.info("✓ Sentiment Analyzer initialized")
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment from transcribed text
        
        Returns:
            dict with sentiment scores and analysis
        """
        if not text:
            return self._empty_sentiment()
        
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # Count sentiment indicators
        positive_count = len(words.intersection(self.positive_words))
        negative_count = len(words.intersection(self.negative_words))
        urgency_count = len(words.intersection(self.urgency_words))
        confusion_count = len(words.intersection(self.confusion_words))
        
        # Calculate overall sentiment score (-1 to 1)
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
        else:
            sentiment_score = 0.0
        
        # Determine primary sentiment
        if sentiment_score > 0.3:
            primary_sentiment = "positive"
            sentiment_label = "😊 Positive"
        elif sentiment_score < -0.3:
            primary_sentiment = "negative"
            sentiment_label = "😠 Negative"
        else:
            primary_sentiment = "neutral"
            sentiment_label = "😐 Neutral"
        
        # Detect secondary emotions
        emotions = []
        if urgency_count > 0:
            emotions.append("urgent")
        if confusion_count > 0:
            emotions.append("confused")
        if negative_count > 2:
            emotions.append("frustrated")
        if positive_count > 2:
            emotions.append("satisfied")
        
        # Calculate confidence
        confidence = min(1.0, (total_sentiment_words / 5.0))
        
        # Escalation recommendation
        should_escalate = (
            (primary_sentiment == "negative" and negative_count >= 3) or
            (urgency_count >= 2) or
            ("frustrated" in emotions and urgency_count >= 1)
        )
        
        result = {
            "sentiment_score": round(sentiment_score, 3),
            "primary_sentiment": primary_sentiment,
            "sentiment_label": sentiment_label,
            "emotions": emotions,
            "confidence": round(confidence, 3),
            "should_escalate": should_escalate,
            "indicators": {
                "positive_words": positive_count,
                "negative_words": negative_count,
                "urgency_words": urgency_count,
                "confusion_words": confusion_count
            },
            "text_analyzed": text
        }
        
        logger.info(f"Sentiment: {sentiment_label} (score: {sentiment_score:.2f}) | Emotions: {emotions}")
        
        return result
    
    def analyze_call_progression(self, call_sid: str, sentiment_result: Dict) -> Dict:
        """
        Track sentiment over the duration of a call
        Detects sentiment trends and changes
        """
        if call_sid not in self.sentiment_history:
            self.sentiment_history[call_sid] = {
                'sentiments': [],
                'start_time': None,
                'escalation_count': 0
            }
        
        # Add to history
        history = self.sentiment_history[call_sid]
        history['sentiments'].append(sentiment_result)
        
        if sentiment_result.get('should_escalate'):
            history['escalation_count'] += 1
        
        # Calculate trends
        recent_sentiments = history['sentiments'][-5:]  # Last 5 interactions
        
        if len(recent_sentiments) >= 2:
            scores = [s['sentiment_score'] for s in recent_sentiments]
            
            # Trend detection
            if len(scores) >= 3:
                if all(scores[i] < scores[i-1] for i in range(1, len(scores))):
                    trend = "declining"
                    trend_emoji = "📉"
                elif all(scores[i] > scores[i-1] for i in range(1, len(scores))):
                    trend = "improving"
                    trend_emoji = "📈"
                else:
                    trend = "stable"
                    trend_emoji = "➡️"
            else:
                trend = "insufficient_data"
                trend_emoji = "..."
            
            avg_recent = sum(scores) / len(scores)
        else:
            trend = "initial"
            trend_emoji = "🆕"
            avg_recent = sentiment_result['sentiment_score']
        
        # Overall call sentiment
        all_scores = [s['sentiment_score'] for s in history['sentiments']]
        avg_overall = sum(all_scores) / len(all_scores)
        
        progression = {
            "call_sid": call_sid,
            "interaction_count": len(history['sentiments']),
            "current_sentiment": sentiment_result['primary_sentiment'],
            "trend": trend,
            "trend_emoji": trend_emoji,
            "average_recent_score": round(avg_recent, 3),
            "average_overall_score": round(avg_overall, 3),
            "escalation_triggers": history['escalation_count'],
            "needs_immediate_attention": history['escalation_count'] >= 2
        }
        
        logger.info(f"Call progression: {trend_emoji} {trend} | Avg: {avg_overall:.2f}")
        
        return progression
    
    def get_call_summary(self, call_sid: str) -> Dict:
        """
        Generate comprehensive sentiment summary for a call
        """
        if call_sid not in self.sentiment_history:
            return {"error": "Call not found"}
        
        history = self.sentiment_history[call_sid]
        sentiments = history['sentiments']
        
        if not sentiments:
            return {"error": "No sentiment data"}
        
        # Calculate statistics
        scores = [s['sentiment_score'] for s in sentiments]
        primary_sentiments = [s['primary_sentiment'] for s in sentiments]
        
        # Count sentiment types
        sentiment_counts = {
            'positive': primary_sentiments.count('positive'),
            'neutral': primary_sentiments.count('neutral'),
            'negative': primary_sentiments.count('negative')
        }
        
        # All emotions detected
        all_emotions = []
        for s in sentiments:
            all_emotions.extend(s.get('emotions', []))
        
        unique_emotions = list(set(all_emotions))
        
        # Overall assessment
        avg_score = sum(scores) / len(scores)
        if avg_score > 0.3:
            overall_sentiment = "positive"
            overall_emoji = "😊"
        elif avg_score < -0.3:
            overall_sentiment = "negative"
            overall_emoji = "😠"
        else:
            overall_sentiment = "neutral"
            overall_emoji = "😐"
        
        # Quality indicators
        started_negative = sentiments[0]['primary_sentiment'] == 'negative'
        ended_positive = sentiments[-1]['primary_sentiment'] == 'positive'
        improved = started_negative and ended_positive
        
        summary = {
            "call_sid": call_sid,
            "total_interactions": len(sentiments),
            "overall_sentiment": overall_sentiment,
            "overall_emoji": overall_emoji,
            "average_score": round(avg_score, 3),
            "sentiment_breakdown": sentiment_counts,
            "emotions_detected": unique_emotions,
            "escalation_count": history['escalation_count'],
            "call_quality": {
                "started_negative": started_negative,
                "ended_positive": ended_positive,
                "improved_during_call": improved,
                "consistent_positive": sentiment_counts['positive'] > sentiment_counts['negative'] * 2,
                "needs_followup": avg_score < -0.2 or history['escalation_count'] > 0
            },
            "score_range": {
                "min": round(min(scores), 3),
                "max": round(max(scores), 3),
                "variance": round(max(scores) - min(scores), 3)
            }
        }
        
        return summary
    
    def _empty_sentiment(self) -> Dict:
        """Return empty sentiment result"""
        return {
            "sentiment_score": 0.0,
            "primary_sentiment": "neutral",
            "sentiment_label": "😐 Neutral",
            "emotions": [],
            "confidence": 0.0,
            "should_escalate": False,
            "indicators": {
                "positive_words": 0,
                "negative_words": 0,
                "urgency_words": 0,
                "confusion_words": 0
            },
            "text_analyzed": ""
        }
    
    def clear_call_history(self, call_sid: str):
        """Clear sentiment history for a call"""
        if call_sid in self.sentiment_history:
            del self.sentiment_history[call_sid]
            logger.info(f"Cleared sentiment history for call {call_sid}")


# Create global instance
sentiment_analyzer = SentimentAnalyzer()

