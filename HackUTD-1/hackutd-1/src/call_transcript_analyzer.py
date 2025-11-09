"""
Call Transcript Sentiment Analyzer for T-Mobile Network Health Dashboard
Includes training capabilities for custom sentiment models
"""

import os
import json
import pickle
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd

# # Load the parquet file
# df = pd.read_parquet("calls.parquet")

# # Option 1: Save to one-line-per-record JSON (newline-delimited)
# df.to_json("calls.json", orient="records", lines=True)

# Lazy imports - only import when needed to avoid slow startup
SKLEARN_AVAILABLE = None
TRANSFORMERS_AVAILABLE = None
VADER_AVAILABLE = None

def _check_vader():
    """Lazy check for VADER availability"""
    global VADER_AVAILABLE
    if VADER_AVAILABLE is None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            VADER_AVAILABLE = True
        except ImportError:
            VADER_AVAILABLE = False
    return VADER_AVAILABLE

def _check_sklearn():
    """Lazy check for sklearn availability"""
    global SKLEARN_AVAILABLE
    if SKLEARN_AVAILABLE is None:
        try:
            import sklearn
            SKLEARN_AVAILABLE = True
        except ImportError:
            SKLEARN_AVAILABLE = False
    return SKLEARN_AVAILABLE

def _check_transformers():
    """Lazy check for transformers availability"""
    global TRANSFORMERS_AVAILABLE
    if TRANSFORMERS_AVAILABLE is None:
        try:
            import transformers
            TRANSFORMERS_AVAILABLE = True
        except ImportError:
            TRANSFORMERS_AVAILABLE = False
    return TRANSFORMERS_AVAILABLE


@dataclass
class CallTranscript:
    """Represents a call transcript"""
    transcript_id: str
    customer_text: str
    agent_text: str
    full_transcript: str
    duration: Optional[float] = None
    timestamp: Optional[str] = None
    issue_category: Optional[str] = None
    resolution_status: Optional[str] = None
    customer_sentiment: Optional[str] = None  # Ground truth label
    urgency_level: Optional[str] = None


@dataclass
class SentimentPrediction:
    """Sentiment prediction result"""
    transcript_id: str
    sentiment_label: str  
    sentiment_score: float  
    emotion: str  
    urgency_score: float  
    confidence: float
    keywords: List[str]
    predicted_issue_category: Optional[str] = None
    routing_recommendation: Optional[str] = None


class CallTranscriptSentimentAnalyzer:
    """
    Sentiment analyzer specifically trained for call transcripts
    Supports both pre-trained models and custom training
    """
    
    def __init__(self, model_type: str = 'vader', model_path: Optional[str] = None):
        """
        Initialize call transcript analyzer
        
        Args:
            model_type: 'vader' (recommended - pre-trained, no training needed), 'sklearn', or 'transformers'
            model_path: Path to saved sklearn model (.pkl file) - only used if model_type='sklearn'
        """
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.tokenizer = None
        self.transformer_model = None
        self.sentiment_pipeline = None
        self.vader_analyzer = None
        self.label_encoder = None
        
        if model_type == 'vader':
            # Use VADER (pre-trained, no training needed)
            if _check_vader():
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
                self.model_type = 'vader'
            else:
                print("Warning: vaderSentiment not available. Install with: pip install vaderSentiment")
                print("Falling back to rule-based model")
                self.model_type = 'sklearn'
        elif model_path and os.path.exists(model_path):
            # Check if it's a directory (fine-tuned transformer) or file (sklearn pickle)
            if os.path.isdir(model_path):
                # Fine-tuned transformer model
                if _check_transformers():
                    self._load_finetuned_transformer(model_path)
                else:
                    raise ImportError("transformers library required for fine-tuned models")
            else:
                # Sklearn pickle file
                self.load_model(model_path)
        elif model_type == 'transformers' and _check_transformers():
            # Use pre-trained transformer model
            self._load_pretrained_transformer()
    
    def _load_pretrained_transformer(self):
        """Load pre-trained transformer model for sentiment analysis"""
        if not _check_transformers():
            return
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            # Using a sentiment analysis model fine-tuned on customer service data
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.transformer_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=self.tokenizer
            )
            self.model_type = 'transformers'
        except Exception as e:
            print(f"Error loading transformer model: {e}")
            print("Falling back to sklearn model")
            self.model_type = 'sklearn'
    
    def _load_finetuned_transformer(self, model_dir: str):
        """Load fine-tuned transformer model"""
        if not _check_transformers():
            return
        try:
            from transformers import pipeline
            import json
            
            # Load fine-tuned model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_dir,
                tokenizer=model_dir
            )
            
            # Load label mapping if available
            label_map_path = os.path.join(model_dir, 'label_mapping.json')
            if os.path.exists(label_map_path):
                with open(label_map_path, 'r') as f:
                    self.label_mapping = json.load(f)
            else:
                # Default mapping for 3-label system
                self.label_mapping = {'positive': 0, 'neutral': 1, 'negative': 2}
            
            self.model_type = 'transformers'
            print(f"✓ Loaded fine-tuned model from {model_dir}")
        except Exception as e:
            print(f"Error loading fine-tuned model: {e}")
            print("Falling back to rule-based model")
            self.model_type = 'sklearn'
    
    def train_sklearn_model(self, transcripts: List[CallTranscript], 
                           test_size: float = 0.2) -> Dict:
        """
        Train a sklearn-based sentiment classifier
        
        Args:
            transcripts: List of CallTranscript objects with customer_sentiment labels
            test_size: Proportion of data for testing
            
        Returns:
            Training metrics dictionary
        """
        if not _check_sklearn():
            raise ImportError("scikit-learn is required for training")
        
        # Lazy import sklearn modules
        from sklearn.model_selection import train_test_split
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report, accuracy_score
        
        # Prepare data
        texts = []
        labels = []
        
        for transcript in transcripts:
            # Use customer text for sentiment (agent text is usually neutral)
            text = transcript.customer_text or transcript.full_transcript
            label = transcript.customer_sentiment
            
            if text and label:
                texts.append(text)
                labels.append(label)
        
        if not texts:
            raise ValueError("No labeled transcripts provided")
        
        # Check if we can stratify (need at least 2 samples per class)
        from collections import Counter
        label_counts = Counter(labels)
        min_class_count = min(label_counts.values())
        can_stratify = min_class_count >= 2
        
        # Split data
        if can_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=test_size, random_state=42, stratify=labels
            )
        else:
            print(f"Warning: Cannot stratify (some classes have < 2 examples). Using random split.")
            print(f"Label distribution: {dict(label_counts)}")
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=test_size, random_state=42
            )
        
        # Create pipeline with improved parameters for better accuracy
        self.vectorizer = TfidfVectorizer(
            max_features=10000,  # Increased features
            ngram_range=(1, 3),  # Include trigrams for better context
            stop_words='english',
            min_df=1,  # Lower min_df to catch more patterns
            max_df=0.95,  # Filter very common words
            sublinear_tf=True  # Use sublinear TF scaling
        )
        
        # Use LogisticRegression with better parameters
        self.model = LogisticRegression(
            max_iter=2000,  # More iterations for convergence
            random_state=42,
            class_weight='balanced',  # Handle imbalanced classes
            C=1.0,  # Regularization strength
            solver='lbfgs'  # Good solver for small datasets
        )
        
        # Train
        print("Training sentiment model...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        X_test_vec = self.vectorizer.transform(X_test)
        y_pred = self.model.predict(X_test_vec)
        
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        metrics = {
            'accuracy': accuracy,
            'classification_report': report,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'model_type': 'sklearn'
        }
        
        print(f"Model trained! Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        return metrics
    
    def train_transformer_model(self, transcripts: List[CallTranscript],
                               output_dir: str = './models/sentiment_model',
                               num_epochs: int = 3) -> Dict:
        """
        Fine-tune a transformer model on call transcripts
        
        Args:
            transcripts: List of CallTranscript objects with labels
            output_dir: Directory to save the fine-tuned model
            num_epochs: Number of training epochs
            
        Returns:
            Training metrics
        """
        if not _check_transformers():
            raise ImportError("transformers library is required")
        
        # This is a simplified version - full implementation would use Trainer API
        print("Transformer fine-tuning requires more setup.")
        print("For now, using pre-trained model with zero-shot classification.")
        
        return {'status': 'using_pretrained', 'model_type': 'transformers'}
    
    def predict_sentiment(self, transcript: CallTranscript) -> SentimentPrediction:
        """
        Predict sentiment for a call transcript
        
        Args:
            transcript: CallTranscript object
            
        Returns:
            SentimentPrediction object
        """
        # ONLY use customer text for sentiment analysis
        # If full_transcript exists but customer_text doesn't, try to extract it
        text = transcript.customer_text
        
        # If no customer_text, try to extract from full_transcript
        if not text and transcript.full_transcript:
            # Check if full_transcript has speaker labels
            if 'Customer:' in transcript.full_transcript or 'customer:' in transcript.full_transcript.lower():
                # Try to extract customer text
                lines = transcript.full_transcript.split('\n')
                customer_lines = []
                for line in lines:
                    if line.strip().lower().startswith('customer:'):
                        customer_lines.append(line[9:].strip())
                    elif line.strip() and not line.strip().lower().startswith('agent:'):
                        # Continuation line - only add if we're in customer section
                        if customer_lines:
                            customer_lines.append(line.strip())
                text = ' '.join(customer_lines).strip()
            else:
                # No labels - use full transcript as customer text
                text = transcript.full_transcript
        
        if not text:
            return SentimentPrediction(
                transcript_id=transcript.transcript_id,
                sentiment_label='neutral',
                sentiment_score=0.0,
                emotion='neutral',
                urgency_score=0.0,
                confidence=0.0,
                keywords=[]
            )
        
        if self.model_type == 'vader' and self.vader_analyzer:
            return self._predict_with_vader(transcript, text)
        elif self.model_type == 'transformers' and self.sentiment_pipeline:
            return self._predict_with_transformer(transcript, text)
        elif self.model_type == 'sklearn' and self.model:
            return self._predict_with_sklearn(transcript, text)
        else:
            # Fallback to rule-based
            return self._predict_rule_based(transcript, text)
    
    def _predict_with_transformer(self, transcript: CallTranscript, text: str) -> SentimentPrediction:
        """Predict using transformer model"""
        try:
            result = self.sentiment_pipeline(text[:512])  # Limit length
            
            # Map transformer labels to our labels
            label_mapping = {
                'POSITIVE': 'positive',
                'NEGATIVE': 'negative',
                'NEUTRAL': 'neutral',
                'LABEL_0': 'negative',
                'LABEL_1': 'neutral',
                'LABEL_2': 'positive'
            }
            
            label = result[0]['label']
            score = result[0]['score']
            
            sentiment_label = label_mapping.get(label, 'neutral')
            
            # Convert to -1 to 1 scale
            if sentiment_label == 'positive':
                sentiment_score = score
            elif sentiment_label == 'negative':
                sentiment_score = -score
            else:
                sentiment_score = 0.0
            
            # Detect emotion and urgency
            emotion = self._detect_emotion(text, sentiment_score)
            urgency_score = self._calculate_urgency(text, sentiment_score)
            keywords = self._extract_keywords(text)
            issue_category = self._predict_issue_category(text)
            routing = self._recommend_routing(sentiment_score, urgency_score, issue_category)
            
            return SentimentPrediction(
                transcript_id=transcript.transcript_id,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                emotion=emotion,
                urgency_score=urgency_score,
                confidence=score,
                keywords=keywords,
                predicted_issue_category=issue_category,
                routing_recommendation=routing
            )
        except Exception as e:
            print(f"Error in transformer prediction: {e}")
            return self._predict_rule_based(transcript, text)
    
    def _predict_with_vader(self, transcript: CallTranscript, text: str) -> SentimentPrediction:
        """
        Predict using VADER sentiment analyzer (pre-trained, no training needed)
        VADER is specifically designed for social media and customer service text
        """
        if not self.vader_analyzer:
            return self._predict_rule_based(transcript, text)
        
        # Get VADER scores
        scores = self.vader_analyzer.polarity_scores(text)
        compound = scores['compound']  # Range: -1 (very negative) to +1 (very positive)
        text_lower = text.lower()
        
        # Post-process VADER results with domain-specific rules for customer service
        # Check for strong negative indicators that VADER might miss
        strong_negative_phrases = [
            'done with', 'fed up', 'had enough', 'sick of', 'tired of',
            'want to cancel', 'switching', 'leaving', 'cancel service',
            'worst service', 'terrible service', 'unacceptable', 'ridiculous',
            'never again', 'worst company', 'hate this', 'absolutely done'
        ]
        
        # Check for strong positive indicators
        strong_positive_phrases = [
            'love it', 'amazing service', 'best service', 'very happy',
            'so grateful', 'thank you so much', 'excellent service', 'perfect'
        ]
        
        # Adjust sentiment based on strong phrases
        negative_phrase_count = sum(1 for phrase in strong_negative_phrases if phrase in text_lower)
        positive_phrase_count = sum(1 for phrase in strong_positive_phrases if phrase in text_lower)
        
        # If we find strong negative phrases, make sentiment more negative
        if negative_phrase_count > 0:
            # Adjust compound score to be more negative
            compound = min(compound, -0.3 - (negative_phrase_count * 0.2))
        
        # If we find strong positive phrases, make sentiment more positive
        if positive_phrase_count > 0:
            compound = max(compound, 0.3 + (positive_phrase_count * 0.2))
        
        # Map compound score to our 5-label system
        # Adjusted thresholds for better customer service context
        if compound >= 0.5:
            sentiment_label = 'very_positive'
            sentiment_score = compound
        elif compound >= 0.1:  # Lowered from 0.05 for better positive detection
            sentiment_label = 'positive'
            sentiment_score = compound
        elif compound <= -0.5:
            sentiment_label = 'very_negative'
            sentiment_score = compound
        elif compound <= -0.1:  # Lowered from -0.05 for better negative detection
            sentiment_label = 'negative'
            sentiment_score = compound
        else:
            # Neutral zone - but check if there are any indicators
            if negative_phrase_count > 0:
                sentiment_label = 'negative'
                sentiment_score = -0.3
            elif positive_phrase_count > 0:
                sentiment_label = 'positive'
                sentiment_score = 0.3
            else:
                sentiment_label = 'neutral'
                sentiment_score = compound
        
        # Use compound score as confidence (absolute value)
        confidence = abs(compound)
        
        # Detect emotion and urgency
        emotion = self._detect_emotion(text, sentiment_score)
        urgency_score = self._calculate_urgency(text, sentiment_score)
        keywords = self._extract_keywords(text)
        issue_category = self._predict_issue_category(text)
        routing = self._recommend_routing(sentiment_score, urgency_score, issue_category)
        
        return SentimentPrediction(
            transcript_id=transcript.transcript_id,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            emotion=emotion,
            urgency_score=urgency_score,
            confidence=confidence,
            keywords=keywords,
            predicted_issue_category=issue_category,
            routing_recommendation=routing
        )
    
    def _predict_with_sklearn(self, transcript: CallTranscript, text: str) -> SentimentPrediction:
        """Predict using sklearn model"""
        if not self.model or not self.vectorizer:
            return self._predict_rule_based(transcript, text)
        
        # Vectorize text
        text_vec = self.vectorizer.transform([text])
        
        # Predict
        prediction = self.model.predict(text_vec)[0]
        probabilities = self.model.predict_proba(text_vec)[0]
        confidence = max(probabilities)
        
        # Map prediction to sentiment score
        label_to_score = {
            'very_positive': 0.8,
            'positive': 0.4,
            'neutral': 0.0,
            'negative': -0.4,
            'very_negative': -0.8
        }
        
        sentiment_score = label_to_score.get(prediction, 0.0)
        
        emotion = self._detect_emotion(text, sentiment_score)
        urgency_score = self._calculate_urgency(text, sentiment_score)
        keywords = self._extract_keywords(text)
        issue_category = self._predict_issue_category(text)
        routing = self._recommend_routing(sentiment_score, urgency_score, issue_category)
        
        return SentimentPrediction(
            transcript_id=transcript.transcript_id,
            sentiment_label=prediction,
            sentiment_score=sentiment_score,
            emotion=emotion,
            urgency_score=urgency_score,
            confidence=confidence,
            keywords=keywords,
            predicted_issue_category=issue_category,
            routing_recommendation=routing
        )
    
    def _predict_rule_based(self, transcript: CallTranscript, text: str) -> SentimentPrediction:
        """Fallback rule-based sentiment prediction"""
        text_lower = text.lower()
        
        # Simple keyword-based sentiment
        positive_words = ['great', 'excellent', 'good', 'love', 'amazing', 'thank', 'appreciate', 'satisfied']
        negative_words = ['terrible', 'awful', 'horrible', 'bad', 'hate', 'worst', 'disappointed', 'frustrated', 'angry']
        urgent_words = ['urgent', 'immediately', 'asap', 'critical', 'emergency', 'now', 'escalate']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        urgent_count = sum(1 for word in urgent_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words > 0:
            sentiment_score = (positive_count - negative_count) / max(total_words, 1) * 5
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
        else:
            sentiment_score = 0.0
        
        # Determine label
        if sentiment_score >= 0.6:
            sentiment_label = 'very_positive'
        elif sentiment_score >= 0.2:
            sentiment_label = 'positive'
        elif sentiment_score <= -0.6:
            sentiment_label = 'very_negative'
        elif sentiment_score <= -0.2:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        emotion = self._detect_emotion(text, sentiment_score)
        urgency_score = min(1.0, urgent_count * 0.3 + abs(min(0, sentiment_score)) * 0.6)
        keywords = self._extract_keywords(text)
        issue_category = self._predict_issue_category(text)
        routing = self._recommend_routing(sentiment_score, urgency_score, issue_category)
        
        return SentimentPrediction(
            transcript_id=transcript.transcript_id,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            emotion=emotion,
            urgency_score=urgency_score,
            confidence=0.6,
            keywords=keywords,
            predicted_issue_category=issue_category,
            routing_recommendation=routing
        )
    
    def _detect_emotion(self, text: str, sentiment_score: float) -> str:
        """Detect emotion from text with improved accuracy"""
        text_lower = text.lower()
        
        emotion_keywords = {
            'angry': [
                'angry', 'mad', 'furious', 'rage', 'livid', 'outraged', 'enraged',
                'pissed', 'pissed off', 'infuriated', 'irate', 'fuming'
            ],
            'frustrated': [
                'frustrated', 'annoyed', 'irritated', 'fed up', 'sick of', 'tired of',
                'done with', 'had enough', 'exasperated', 'aggravated'
            ],
            'disappointed': [
                'disappointed', 'let down', 'dissatisfied', 'unhappy', 'upset',
                'disheartened', 'discouraged', 'disillusioned'
            ],
            'confused': [
                'confused', 'unclear', "don't understand", 'puzzled', 'bewildered',
                'perplexed', 'lost', "don't get it"
            ],
            'anxious': [
                'worried', 'anxious', 'concerned', 'nervous', 'stressed', 'panicked',
                'uneasy', 'apprehensive'
            ],
            'satisfied': [
                'satisfied', 'pleased', 'content', 'good enough', 'okay', 'fine',
                'acceptable', 'decent'
            ],
            'happy': [
                'happy', 'excited', 'thrilled', 'delighted', 'joyful', 'ecstatic',
                'overjoyed', 'pleased', 'glad'
            ]
        }
        
        # Calculate emotion scores with phrase matching
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    # Longer phrases get higher weight
                    score += len(kw.split()) * 2
            if score > 0:
                emotion_scores[emotion] = score
        
        # Special handling for "done with" type phrases - these indicate frustration/anger
        if any(phrase in text_lower for phrase in ['done with', 'fed up', 'had enough', 'sick of']):
            emotion_scores['frustrated'] = emotion_scores.get('frustrated', 0) + 5
        
        # Special handling for cancellation intent - indicates frustration or anger
        if any(phrase in text_lower for phrase in ['cancel', 'switching', 'leaving', 'done']):
            if sentiment_score < -0.3:
                emotion_scores['frustrated'] = emotion_scores.get('frustrated', 0) + 3
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        # Fallback based on sentiment with better thresholds
        if sentiment_score <= -0.7:
            return 'angry'
        elif sentiment_score <= -0.4:
            return 'frustrated'
        elif sentiment_score <= -0.1:
            return 'disappointed'
        elif sentiment_score >= 0.7:
            return 'happy'
        elif sentiment_score >= 0.3:
            return 'satisfied'
        else:
            return 'neutral'
    
    def _calculate_urgency(self, text: str, sentiment_score: float) -> float:
        """
        Calculate urgency score (0.0 to 1.0)
        Higher score = more urgent
        """
        text_lower = text.lower()
        
        # High urgency indicators (strong signals) - expanded list
        high_urgency_indicators = [
            'urgent', 'immediately', 'asap', 'critical', 'emergency', 'now',
            'right away', "can't wait", 'need help now', 'escalate', 'manager',
            'supervisor', 'complaint', 'filing complaint', 'cancel', 'switching',
            'third time', 'multiple times', 'again', 'still', 'yet again',
            'fed up', 'had enough', 'done with', 'want to cancel', 'lawyer',
            'sue', 'terrible service', 'worst service', 'unacceptable',
            'absolutely done', 'never again', 'worst company', 'hate this',
            'leaving', 'switching to', 'cancel service', 'terminate', 'quit'
        ]
        
        # Medium urgency indicators - expanded list
        medium_urgency_indicators = [
            'frustrated', 'disappointed', 'upset', 'angry', 'annoyed',
            'problem', 'issue', 'broken', 'not working', "doesn't work",
            'slow', 'bad', 'poor', 'wrong', 'error', 'failed',
            'concerned', 'worried', 'unhappy', 'dissatisfied', 'trouble',
            'sick of', 'tired of', 'unacceptable', 'ridiculous', 'outrageous'
        ]
        
        # Count urgency indicators with phrase matching
        high_urgency_count = 0
        for indicator in high_urgency_indicators:
            if indicator in text_lower:
                # Longer phrases get higher weight
                high_urgency_count += len(indicator.split())
        
        medium_urgency_count = sum(1 for indicator in medium_urgency_indicators if indicator in text_lower)
        
        # Special handling for "done with" - this is HIGH urgency
        if any(phrase in text_lower for phrase in ['done with', 'fed up', 'had enough', 'sick of']):
            high_urgency_count += 3
        
        # Calculate urgency from sentiment (negative sentiment = higher urgency)
        # Adjusted thresholds for better urgency detection
        urgency_from_sentiment = 0.0
        if sentiment_score <= -0.7:
            urgency_from_sentiment = 0.8  # Very negative = very high urgency
        elif sentiment_score <= -0.4:
            urgency_from_sentiment = 0.6  # Negative = high urgency
        elif sentiment_score <= -0.2:
            urgency_from_sentiment = 0.4  # Slightly negative = medium urgency
        elif sentiment_score < 0:
            urgency_from_sentiment = 0.2  # Any negative = some urgency
        
        # Calculate final urgency score with improved weighting
        urgency_score = (
            (high_urgency_count * 0.15) +  # Each high urgency indicator adds 0.15 (reduced from 0.25 to allow stacking)
            (medium_urgency_count * 0.08) +  # Each medium urgency indicator adds 0.08
            urgency_from_sentiment  # Sentiment-based urgency
        )
        
        # Boost urgency if multiple high indicators present
        if high_urgency_count >= 3:
            urgency_score += 0.2
        
        # Cap at 1.0 and ensure minimum based on sentiment
        urgency_score = min(1.0, max(urgency_score, urgency_from_sentiment))
        
        return urgency_score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords"""
        tmobile_keywords = [
            'tmobile', 't-mobile', 'network', 'coverage', 'signal', 'dropped call',
            'billing', 'bill', 'charge', 'plan', 'data', 'speed', '5g', 'lte',
            'customer service', 'support', 'agent', 'issue', 'problem', 'fix'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in tmobile_keywords if kw in text_lower]
        
        return list(set(found_keywords))[:10]
    
    def _predict_issue_category(self, text: str) -> str:
        """Predict issue category from text"""
        text_lower = text.lower()
        
        categories = {
            'network_coverage': ['coverage', 'signal', 'dropped', 'no service', 'dead zone', 'slow', '5g', 'lte'],
            'billing': ['bill', 'charge', 'overcharge', 'fee', 'price', 'cost', 'refund'],
            'customer_service': ['support', 'rep', 'customer service', 'rude', 'unhelpful', 'wait time'],
            'technical': ['app', 'website', 'login', 'error', 'bug', 'sim', 'activation'],
            'device_issues': ['phone', 'device', 'not working', 'broken', 'defective'],
            'plan_questions': ['plan', 'unlimited', 'data', 'upgrade', 'downgrade', 'switch']
        }
        
        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category
        
        return 'general'
    
    def _recommend_routing(self, sentiment_score: float, urgency_score: float, 
                          issue_category: str) -> str:
        """Recommend routing based on sentiment, urgency, and issue"""
        # Simple routing logic
        if urgency_score > 0.7 or sentiment_score < -0.5:
            return 'human_escalation'
        elif issue_category in ['billing', 'plan_questions'] and sentiment_score > -0.3:
            return 'agent_qa'
        elif issue_category == 'network_coverage' and urgency_score < 0.5:
            return 'network_health_dashboard'
        else:
            return 'standard_agent'
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model_type': self.model_type,
            'model': self.model,
            'vectorizer': self.vectorizer,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model_type = model_data['model_type']
        self.model = model_data['model']
        self.vectorizer = model_data['vectorizer']
        
        print(f"Model loaded from {filepath}")
    
    def batch_predict(self, transcripts: List[CallTranscript]) -> List[SentimentPrediction]:
        """Predict sentiment for multiple transcripts"""
        return [self.predict_sentiment(transcript) for transcript in transcripts]

