"""
Real-time call transcript sentiment analyzer
Processes transcripts as they come in and updates sentiment scores
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
# Also add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from src.call_transcript_analyzer import CallTranscriptSentimentAnalyzer, CallTranscript, SentimentPrediction

# Import parse functions - handle both relative and absolute imports
try:
    from scripts.parse_live_transcript import parse_transcript_with_speakers, parse_realtime_chunk, parse_transcript_by_lines
except ImportError:
    try:
        # Try relative import
        from parse_live_transcript import parse_transcript_with_speakers, parse_realtime_chunk, parse_transcript_by_lines
    except ImportError:
        # Last resort - import directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("parse_live_transcript", scripts_dir / "parse_live_transcript.py")
        parse_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(parse_module)
        parse_transcript_with_speakers = parse_module.parse_transcript_with_speakers
        parse_realtime_chunk = parse_module.parse_realtime_chunk
        parse_transcript_by_lines = parse_module.parse_transcript_by_lines


class RealTimeSentimentAnalyzer:
    """Real-time sentiment analyzer for live call transcripts"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize real-time analyzer
        
        Args:
            model_path: Path to trained sklearn model (.pkl file)
                       If None, uses rule-based
        """
        print("Initializing real-time sentiment analyzer...", flush=True)
        
        if model_path and Path(model_path).exists():
            # Load trained sklearn model
            self.analyzer = CallTranscriptSentimentAnalyzer(
                model_type='sklearn',
                model_path=model_path
            )
            print(f"✓ Loaded trained sklearn model from {model_path}", flush=True)
        else:
            # Use VADER by default (pre-trained, no training needed)
            self.analyzer = CallTranscriptSentimentAnalyzer(model_type='vader')
            print("✓ Using VADER sentiment analyzer (pre-trained, no training needed)", flush=True)
        
        self.processed_count = 0
        self.sentiment_history = []  # Store recent predictions
    
    def analyze_transcript(self, transcript_data: Dict) -> Dict:
        """
        Analyze a single transcript in real-time
        
        Args:
            transcript_data: Dictionary with transcript info:
                {
                    'transcript_id': str,
                    'customer_text': str (optional - will be extracted if not provided),
                    'agent_text': str (optional),
                    'full_transcript': str (optional - will parse if has Customer:/Agent: labels),
                    'transcript': str (optional - raw transcript with speaker labels),
                    'timestamp': str (optional)
                }
        
        Returns:
            Dictionary with analysis results
        """
        # Extract customer and agent text
        customer_text = transcript_data.get('customer_text', '')
        agent_text = transcript_data.get('agent_text', '')
        full_transcript = transcript_data.get('full_transcript', '') or transcript_data.get('transcript', '')
        
        # If full_transcript has speaker labels but customer_text is empty, parse it
        if not customer_text and full_transcript:
            # Check for speaker labels (customer/agent or Customer:/Agent:)
            transcript_lower = full_transcript.lower()
            has_labels = (
                'customer' in transcript_lower[:20] or 
                'agent' in transcript_lower[:20] or
                'Customer:' in full_transcript[:50] or 
                'Agent:' in full_transcript[:50]
            )
            
            if has_labels:
                parsed = parse_transcript_with_speakers(full_transcript)
                customer_text = parsed['customer_text']
                agent_text = parsed['agent_text']
            else:
                # No labels - assume entire transcript is customer text
                customer_text = full_transcript
        
        # Create CallTranscript object - ONLY use customer text for sentiment
        transcript = CallTranscript(
            transcript_id=transcript_data.get('transcript_id', f"call_{int(time.time())}"),
            customer_text=customer_text,  # Only customer text for sentiment analysis
            agent_text=agent_text,  # Stored but not used for sentiment
            full_transcript=full_transcript,
            timestamp=transcript_data.get('timestamp', datetime.now().isoformat())
        )
        
        # Analyze sentiment
        start_time = time.time()
        prediction = self.analyzer.predict_sentiment(transcript)
        processing_time = time.time() - start_time
        
        self.processed_count += 1
        
        # Store in history (keep last 100)
        result = {
            'transcript_id': prediction.transcript_id,
            'timestamp': datetime.now().isoformat(),
            'customer_text': customer_text[:200],  # Store customer text for reference
            'agent_text': agent_text[:200] if agent_text else None,  # Store agent text
            'sentiment': {
                'label': prediction.sentiment_label,
                'score': prediction.sentiment_score,
                'confidence': prediction.confidence
            },
            'emotion': prediction.emotion,
            'urgency': {
                'score': prediction.urgency_score,
                'level': 'HIGH' if prediction.urgency_score > 0.7 else 'MEDIUM' if prediction.urgency_score > 0.4 else 'LOW'
            },
            'issue_category': prediction.predicted_issue_category,
            'routing': prediction.routing_recommendation,
            'keywords': prediction.keywords,
            'processing_time_ms': round(processing_time * 1000, 2)
        }
        
        self.sentiment_history.append(result)
        if len(self.sentiment_history) > 100:
            self.sentiment_history.pop(0)
        
        return result
    
    def analyze_stream(self, transcript_stream: List[Dict]) -> List[Dict]:
        """Analyze multiple transcripts in a stream"""
        results = []
        for transcript_data in transcript_stream:
            result = self.analyze_transcript(transcript_data)
            results.append(result)
        return results
    
    def get_statistics(self) -> Dict:
        """Get statistics about processed transcripts"""
        if not self.sentiment_history:
            return {'total_processed': 0}
        
        sentiment_counts = {}
        urgency_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        routing_counts = {}
        
        for item in self.sentiment_history:
            # Count sentiments
            sent_label = item['sentiment']['label']
            sentiment_counts[sent_label] = sentiment_counts.get(sent_label, 0) + 1
            
            # Count urgency levels
            urgency_level = item['urgency']['level']
            urgency_counts[urgency_level] = urgency_counts.get(urgency_level, 0) + 1
            
            # Count routing
            routing = item['routing']
            routing_counts[routing] = routing_counts.get(routing, 0) + 1
        
        avg_processing_time = sum(item['processing_time_ms'] for item in self.sentiment_history) / len(self.sentiment_history)
        
        return {
            'total_processed': self.processed_count,
            'recent_count': len(self.sentiment_history),
            'sentiment_distribution': sentiment_counts,
            'urgency_distribution': urgency_counts,
            'routing_distribution': routing_counts,
            'avg_processing_time_ms': round(avg_processing_time, 2)
        }


def process_live_transcript(analyzer: RealTimeSentimentAnalyzer, transcript_text: str, 
                           transcript_id: Optional[str] = None) -> Dict:
    """
    Process a single live transcript
    
    Supports two formats:
    1. Plain text (assumed to be customer text only)
    2. Text with speaker labels: "Customer: ... Agent: ..."
    
    Args:
        analyzer: RealTimeSentimentAnalyzer instance
        transcript_text: The transcript text to analyze (with or without speaker labels)
        transcript_id: Optional ID for the transcript
    
    Returns:
        Analysis results dictionary
    """
    # Check if transcript has speaker labels (customer/agent or Customer:/Agent:)
    transcript_lower = transcript_text.lower()
    has_labels = (
        'customer' in transcript_lower[:20] or 
        'agent' in transcript_lower[:20] or
        'Customer:' in transcript_text[:50] or 
        'Agent:' in transcript_text[:50]
    )
    
    if has_labels:
        # Has labels - parse it to separate customer and agent
        parsed = parse_transcript_with_speakers(transcript_text)
        transcript_data = {
            'transcript_id': transcript_id or f"live_{int(time.time())}",
            'transcript': transcript_text,  # Store full transcript
            'customer_text': parsed['customer_text'],  # Extract customer text ONLY
            'agent_text': parsed['agent_text'],  # Extract agent text (stored but not used for sentiment)
            'timestamp': datetime.now().isoformat()
        }
        print(f"📞 Parsed transcript - Customer: {len(parsed['customer_text'])} chars, Agent: {len(parsed['agent_text'])} chars")
    else:
        # Plain text - assume it's customer text only
        transcript_data = {
            'transcript_id': transcript_id or f"live_{int(time.time())}",
            'customer_text': transcript_text,  # Customer text only
            'timestamp': datetime.now().isoformat()
        }
    
    result = analyzer.analyze_transcript(transcript_data)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"📝 Customer Text: {result.get('customer_text', transcript_data.get('customer_text', 'N/A'))[:150]}...")
    print(f"🎯 Sentiment: {result['sentiment']['label']} (score: {result['sentiment']['score']:.3f})")
    print(f"😊 Emotion: {result['emotion']}")
    print(f"⚡ Urgency: {result['urgency']['level']} (score: {result['urgency']['score']:.3f})")
    print(f"🔄 Routing: {result['routing']}")
    if result.get('keywords'):
        print(f"🔑 Keywords: {', '.join(result['keywords'][:5])}")
    print(f"⏱️  Processing time: {result['processing_time_ms']}ms")
    print(f"{'='*60}")
    
    return result


def main():
    """Example usage of real-time analyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time call transcript sentiment analyzer')
    parser.add_argument('--model', type=str, default=None,
                       help='Path to trained model file')
    parser.add_argument('--transcript', type=str, default=None,
                       help='Single transcript text to analyze')
    parser.add_argument('--file', type=str, default=None,
                       help='JSON file with transcripts to analyze')
    parser.add_argument('--txt-file', type=str, default=None,
                       help='TXT file with full conversation transcript (customer/agent labeled)')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode - enter transcripts one by one')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = RealTimeSentimentAnalyzer(model_path=args.model)
    
    if args.transcript:
        # Analyze single transcript
        result = process_live_transcript(analyzer, args.transcript)
        # Don't print JSON again - process_live_transcript already prints formatted output
    
    elif args.txt_file:
        # Process TXT file with full conversation transcript
        print(f"\n📄 Processing TXT file: {args.txt_file}\n")
        
        with open(args.txt_file, 'r', encoding='utf-8') as f:
            full_transcript = f.read()
        
        # Parse transcript by lines to get individual customer statements
        customer_lines = parse_transcript_by_lines(full_transcript)
        
        print(f"📊 Found {len(customer_lines)} customer statements\n")
        print(f"{'='*80}")
        print(f"{'LINE':<6} {'SENTIMENT':<15} {'EMOTION':<12} {'URGENCY':<10} {'ROUTING':<20} {'TEXT'[:40]}")
        print(f"{'='*80}")
        
        all_results = []
        
        # Analyze each customer line separately
        for line_data in customer_lines:
            line_num = line_data['line_number']
            customer_text = line_data['customer_text']
            
            # Analyze this line
            result = analyzer.analyze_transcript({
                'transcript_id': f"{Path(args.txt_file).stem}_line_{line_num}",
                'customer_text': customer_text,
                'agent_text': line_data.get('agent_text', ''),
                'timestamp': datetime.now().isoformat()
            })
            
            all_results.append({
                'line_number': line_num,
                'customer_text': customer_text,
                'agent_text': line_data.get('agent_text', ''),
                'analysis': result
            })
            
            # Print line-by-line stats
            sentiment_label = result['sentiment']['label']
            emotion = result['emotion']
            urgency_level = result['urgency']['level']
            urgency_score = result['urgency']['score']
            routing = result['routing']
            text_preview = customer_text[:40] + "..." if len(customer_text) > 40 else customer_text
            
            print(f"{line_num:<6} {sentiment_label:<15} {emotion:<12} {urgency_level} ({urgency_score:.2f}){'':<3} {routing:<20} {text_preview}")
        
        print(f"{'='*80}\n")
        
        # Calculate overall statistics
        sentiment_counts = {}
        urgency_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        total_urgency = 0.0
        total_sentiment = 0.0
        
        for item in all_results:
            result = item['analysis']
            sent_label = result['sentiment']['label']
            sentiment_counts[sent_label] = sentiment_counts.get(sent_label, 0) + 1
            total_sentiment += result['sentiment']['score']
            
            urgency_level = result['urgency']['level']
            urgency_counts[urgency_level] = urgency_counts.get(urgency_level, 0) + 1
            total_urgency += result['urgency']['score']
        
        avg_sentiment = total_sentiment / len(all_results) if all_results else 0.0
        avg_urgency = total_urgency / len(all_results) if all_results else 0.0
        
        # Determine overall sentiment label
        if avg_sentiment >= 0.5:
            overall_sentiment = 'very_positive'
        elif avg_sentiment >= 0.05:
            overall_sentiment = 'positive'
        elif avg_sentiment <= -0.5:
            overall_sentiment = 'very_negative'
        elif avg_sentiment <= -0.05:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Print overall summary
        print(f"{'='*80}")
        print(f"📊 OVERALL SUMMARY")
        print(f"{'='*80}")
        print(f"🎯 Overall Sentiment: {overall_sentiment} (avg score: {avg_sentiment:.3f})")
        print(f"⚡ Average Urgency: {avg_urgency:.3f}")
        print(f"\n📈 Sentiment Distribution:")
        for label, count in sorted(sentiment_counts.items()):
            percentage = (count / len(all_results)) * 100
            print(f"   {label}: {count} ({percentage:.1f}%)")
        print(f"\n⚡ Urgency Distribution:")
        for level, count in sorted(urgency_counts.items()):
            if count > 0:
                percentage = (count / len(all_results)) * 100
                print(f"   {level}: {count} ({percentage:.1f}%)")
        print(f"{'='*80}\n")
        
        # Save detailed results
        output_file = args.txt_file.replace('.txt', '_analyzed.json')
        with open(output_file, 'w') as f:
            json.dump({
                'file': args.txt_file,
                'total_customer_lines': len(all_results),
                'overall_sentiment': overall_sentiment,
                'average_sentiment_score': avg_sentiment,
                'average_urgency_score': avg_urgency,
                'sentiment_distribution': sentiment_counts,
                'urgency_distribution': urgency_counts,
                'line_by_line_analysis': all_results
            }, f, indent=2)
        print(f"✓ Detailed results saved to {output_file}")
        
    elif args.file:
        # Analyze from JSON file
        with open(args.file, 'r') as f:
            transcripts = json.load(f)
        
        print(f"\nProcessing {len(transcripts)} transcripts...\n")
        results = analyzer.analyze_stream(transcripts)
        
        # Save results
        output_file = args.file.replace('.json', '_analyzed.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Processed {len(results)} transcripts")
        print(f"✓ Results saved to {output_file}")
        
        # Show statistics
        stats = analyzer.get_statistics()
        print(f"\nStatistics:")
        print(f"  Total processed: {stats['total_processed']}")
        print(f"  Sentiment distribution: {stats['sentiment_distribution']}")
        print(f"  Urgency distribution: {stats['urgency_distribution']}")
        print(f"  Avg processing time: {stats['avg_processing_time_ms']}ms")
    
    elif args.interactive:
        # Interactive mode
        print("\n" + "=" * 60)
        print("Interactive Real-Time Sentiment Analyzer")
        print("=" * 60)
        print("Enter call transcripts (type 'quit' to exit, 'stats' for statistics)\n")
        
        while True:
            try:
                transcript_text = input("Enter transcript: ").strip()
                
                if transcript_text.lower() == 'quit':
                    break
                elif transcript_text.lower() == 'stats':
                    stats = analyzer.get_statistics()
                    print(f"\n{json.dumps(stats, indent=2)}\n")
                    continue
                elif not transcript_text:
                    continue
                
                result = process_live_transcript(analyzer, transcript_text)
                # Results already printed by process_live_transcript
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
        
        # Final statistics
        stats = analyzer.get_statistics()
        print(f"\n\nFinal Statistics:")
        print(f"  Total transcripts processed: {stats['total_processed']}")
        print(f"  Sentiment distribution: {stats['sentiment_distribution']}")
        print(f"  Urgency distribution: {stats['urgency_distribution']}")
    
    else:
        print("No input specified. Use --transcript, --file, or --interactive")
        print("\nExamples:")
        print("  python scripts/realtime_analyzer.py --transcript \"I'm frustrated with the service!\"")
        print("  python scripts/realtime_analyzer.py --file data/transcripts.json")
        print("  python scripts/realtime_analyzer.py --interactive")
        print("  python scripts/realtime_analyzer.py --model models/sentiment_model.pkl --interactive")


if __name__ == "__main__":
    main()

