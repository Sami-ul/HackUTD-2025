"""
CSR (Customer Service Representative) Router
Routes calls to appropriate CSRs based on sentiment, urgency, and issue type
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CSR:
    """Customer Service Representative"""
    id: str
    name: str
    personality: str
    specialties: List[str]  # e.g., ['de-escalation', 'technical', 'billing']
    experience_years: int
    success_rate: float  # 0.0 to 1.0
    current_calls: int
    max_calls: int
    description: str


class CSRRouter:
    """Routes calls to appropriate CSRs based on analysis"""
    
    def __init__(self):
        self.csrs = self._initialize_csrs()
    
    def _initialize_csrs(self) -> List[CSR]:
        """Initialize mock CSRs with different personalities and specialties"""
        return [
            CSR(
                id='csr_001',
                name='Sarah Chen',
                personality='De-escalation Expert',
                specialties=['de-escalation', 'angry_customers', 'complaints'],
                experience_years=8,
                success_rate=0.95,
                current_calls=0,
                max_calls=3,
                description='Expert at calming frustrated customers and turning negative experiences into positive ones. Specializes in handling angry and upset customers.'
            ),
            CSR(
                id='csr_002',
                name='Michael Rodriguez',
                personality='Technical Specialist',
                specialties=['technical', 'network_coverage', 'device_issues'],
                experience_years=6,
                success_rate=0.92,
                current_calls=0,
                max_calls=4,
                description='Technical expert who excels at solving complex network and device issues. Great with customers who need technical explanations.'
            ),
            CSR(
                id='csr_003',
                name='Emily Johnson',
                personality='Billing & Plans Expert',
                specialties=['billing', 'plan_questions', 'refunds'],
                experience_years=5,
                success_rate=0.90,
                current_calls=0,
                max_calls=5,
                description='Specializes in billing issues, plan questions, and refunds. Patient and detail-oriented with financial matters.'
            ),
            CSR(
                id='csr_004',
                name='David Kim',
                personality='High-Urgency Handler',
                specialties=['urgent', 'escalations', 'cancellations'],
                experience_years=7,
                success_rate=0.93,
                current_calls=0,
                max_calls=2,
                description='Handles high-urgency situations and prevents cancellations. Quick problem-solver who can think on his feet.'
            ),
            CSR(
                id='csr_005',
                name='Jessica Martinez',
                personality='Empathetic Listener',
                specialties=['emotional_support', 'confused_customers', 'anxious'],
                experience_years=4,
                success_rate=0.88,
                current_calls=0,
                max_calls=4,
                description='Very empathetic and patient. Great with confused, anxious, or worried customers who need extra support.'
            ),
            CSR(
                id='csr_006',
                name='Robert Thompson',
                personality='Generalist',
                specialties=['general', 'standard_issues', 'first_contact'],
                experience_years=3,
                success_rate=0.85,
                current_calls=0,
                max_calls=6,
                description='Well-rounded CSR who handles general inquiries and standard issues. Good for first-time contacts.'
            )
        ]
    
    def get_all_csrs(self) -> List[Dict]:
        """Get all CSRs as dictionaries"""
        return [
            {
                'id': csr.id,
                'name': csr.name,
                'personality': csr.personality,
                'specialties': csr.specialties,
                'experience_years': csr.experience_years,
                'success_rate': csr.success_rate,
                'current_calls': csr.current_calls,
                'max_calls': csr.max_calls,
                'description': csr.description,
                'available': csr.current_calls < csr.max_calls
            }
            for csr in self.csrs
        ]
    
    def route_call(self, sentiment_score: float, urgency_score: float, 
                   emotion: str, issue_category: str, 
                   customer_info: Optional[Dict] = None) -> Dict:
        """
        Route a call to the most appropriate CSR
        
        Args:
            sentiment_score: Sentiment score (-1 to 1)
            urgency_score: Urgency score (0 to 1)
            emotion: Detected emotion
            issue_category: Issue category
            customer_info: Optional customer information
        
        Returns:
            Dictionary with CSR information
        """
        # Filter available CSRs
        available_csrs = [csr for csr in self.csrs if csr.current_calls < csr.max_calls]
        
        if not available_csrs:
            # All CSRs busy - return first CSR anyway
            available_csrs = [self.csrs[0]]
        
        # Score each CSR based on match
        scored_csrs = []
        
        for csr in available_csrs:
            score = 0.0
            
            # Match based on sentiment (negative = de-escalation expert)
            if sentiment_score < -0.5:
                if 'de-escalation' in csr.specialties or 'angry_customers' in csr.specialties:
                    score += 30
                if 'complaints' in csr.specialties:
                    score += 20
            
            # Match based on urgency
            if urgency_score > 0.7:
                if 'urgent' in csr.specialties or 'escalations' in csr.specialties:
                    score += 25
                if 'cancellations' in csr.specialties:
                    score += 20
            
            # Match based on emotion
            if emotion in ['angry', 'frustrated']:
                if 'de-escalation' in csr.specialties or 'angry_customers' in csr.specialties:
                    score += 25
            elif emotion in ['confused', 'anxious']:
                if 'emotional_support' in csr.specialties or 'confused_customers' in csr.specialties:
                    score += 25
                if 'anxious' in csr.specialties:
                    score += 20
            
            # Match based on issue category
            if issue_category == 'network_coverage' or issue_category == 'technical':
                if 'technical' in csr.specialties or 'network_coverage' in csr.specialties:
                    score += 20
                if 'device_issues' in csr.specialties and issue_category == 'device_issues':
                    score += 20
            elif issue_category == 'billing':
                if 'billing' in csr.specialties:
                    score += 25
            elif issue_category == 'plan_questions':
                if 'plan_questions' in csr.specialties:
                    score += 20
            
            # Bonus for success rate
            score += csr.success_rate * 10
            
            # Bonus for experience
            score += csr.experience_years * 2
            
            # Penalty for current load
            load_ratio = csr.current_calls / csr.max_calls if csr.max_calls > 0 else 0
            score -= load_ratio * 10
            
            scored_csrs.append((csr, score))
        
        # Sort by score (highest first)
        scored_csrs.sort(key=lambda x: x[1], reverse=True)
        
        # Get best match
        best_csr = scored_csrs[0][0]
        
        # Increment current calls
        best_csr.current_calls += 1
        
        return {
            'id': best_csr.id,
            'name': best_csr.name,
            'personality': best_csr.personality,
            'specialties': best_csr.specialties,
            'experience_years': best_csr.experience_years,
            'success_rate': best_csr.success_rate,
            'description': best_csr.description,
            'match_score': scored_csrs[0][1],
            'reason': self._get_routing_reason(best_csr, sentiment_score, urgency_score, emotion, issue_category)
        }
    
    def _get_routing_reason(self, csr: CSR, sentiment_score: float, 
                           urgency_score: float, emotion: str, issue_category: str) -> str:
        """Generate explanation for why this CSR was chosen"""
        reasons = []
        
        if sentiment_score < -0.5 and 'de-escalation' in csr.specialties:
            reasons.append("Expert at handling negative sentiment")
        
        if urgency_score > 0.7 and 'urgent' in csr.specialties:
            reasons.append("Specializes in high-urgency situations")
        
        if emotion in ['angry', 'frustrated'] and 'angry_customers' in csr.specialties:
            reasons.append(f"Best match for {emotion} customers")
        
        if issue_category in csr.specialties:
            reasons.append(f"Specializes in {issue_category} issues")
        
        if not reasons:
            reasons.append("Available and experienced CSR")
        
        return "; ".join(reasons)
    
    def release_call(self, csr_id: str):
        """Release a call from a CSR (decrement current_calls)"""
        for csr in self.csrs:
            if csr.id == csr_id and csr.current_calls > 0:
                csr.current_calls -= 1
                break

