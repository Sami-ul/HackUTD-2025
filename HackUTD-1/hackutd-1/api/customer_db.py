"""
Mock Customer Database
Stores customer information for the dashboard
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import random


class CustomerDB:
    """Mock customer database"""
    
    def __init__(self):
        self.customers = self._initialize_customers()
    
    def _initialize_customers(self) -> Dict[str, Dict]:
        """Initialize mock customer data"""
        return {
            '5551234567': {
                'phone_number': '5551234567',
                'name': 'John Smith',
                'email': 'john.smith@email.com',
                'account_id': 'ACC001234',
                'plan': 'Magenta Max',
                'monthly_bill': 85.00,
                'account_age_months': 24,
                'previous_calls': 3,
                'last_call_date': (datetime.now() - timedelta(days=15)).isoformat(),
                'previous_sentiment': 'neutral',
                'notes': 'Generally satisfied customer. Had billing question last month.',
                'location': 'Dallas, TX'
            },
            '5559876543': {
                'phone_number': '5559876543',
                'name': 'Maria Garcia',
                'email': 'maria.garcia@email.com',
                'account_id': 'ACC005678',
                'plan': 'Essentials',
                'monthly_bill': 60.00,
                'account_age_months': 6,
                'previous_calls': 1,
                'last_call_date': (datetime.now() - timedelta(days=45)).isoformat(),
                'previous_sentiment': 'positive',
                'notes': 'New customer. Happy with service so far.',
                'location': 'Los Angeles, CA'
            },
            '5555551234': {
                'phone_number': '5555551234',
                'name': 'Robert Johnson',
                'email': 'robert.j@email.com',
                'account_id': 'ACC009876',
                'plan': 'Magenta',
                'monthly_bill': 70.00,
                'account_age_months': 36,
                'previous_calls': 8,
                'last_call_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'previous_sentiment': 'negative',
                'notes': 'Frequent caller. Has network coverage issues in his area. Considered switching last month.',
                'location': 'Rural Montana'
            },
            '5551112222': {
                'phone_number': '5551112222',
                'name': 'Sarah Williams',
                'email': 'sarah.w@email.com',
                'account_id': 'ACC001122',
                'plan': 'Magenta Max',
                'monthly_bill': 90.00,
                'account_age_months': 12,
                'previous_calls': 2,
                'last_call_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'previous_sentiment': 'positive',
                'notes': 'Tech-savvy customer. Usually calls for plan upgrades.',
                'location': 'Seattle, WA'
            },
            '5553334444': {
                'phone_number': '5553334444',
                'name': 'Michael Brown',
                'email': 'mike.brown@email.com',
                'account_id': 'ACC003344',
                'plan': 'Essentials',
                'monthly_bill': 60.00,
                'account_age_months': 18,
                'previous_calls': 5,
                'last_call_date': (datetime.now() - timedelta(days=10)).isoformat(),
                'previous_sentiment': 'very_negative',
                'notes': 'Recent billing dispute. Very upset about overcharge. Needs careful handling.',
                'location': 'Chicago, IL'
            },
            
            '+17206866656': {
                "phone_number": "+17206866656",
                "name": "Aryav Rastogi",
                "email": "aryav.rastogi@hotmail.com",
                "account_id": "ACC001",
                "plan": "Unlimited Premium",
                "monthly_bill": 95.00,
                "account_age_months": 24,
                "previous_calls": 3,
                "last_call_date": "2025-10-25T10:30:00",
                "previous_sentiment": "neutral",
                "notes": "Active customer, no issues.",
                "location": "Dallas, TX"
            }
        }
    
    def get_customer(self, phone_number: str) -> Optional[Dict]:
        """Get customer information by phone number"""
        # Normalize phone number (remove dashes, spaces, etc.)
        normalized = ''.join(filter(str.isdigit, phone_number))
        
        # Try exact match first (with original format)
        if phone_number in self.customers:
            return self.customers[phone_number]
        
        # Try with +1 prefix if it's a US number (11 digits)
        if len(normalized) == 11 and normalized.startswith('1'):
            with_plus = f"+{normalized}"
            if with_plus in self.customers:
                return self.customers[with_plus]
        
        # Try normalized exact match
        if normalized in self.customers:
            return self.customers[normalized]
        
        # Try with last 10 digits
        if len(normalized) >= 10:
            last_10 = normalized[-10:]
            if last_10 in self.customers:
                return self.customers[last_10]
            # Also try with +1 prefix for 10-digit numbers
            with_plus_10 = f"+1{last_10}"
            if with_plus_10 in self.customers:
                return self.customers[with_plus_10]
        
        # Try matching against all customer keys (normalize each key too)
        for key, customer in self.customers.items():
            key_normalized = ''.join(filter(str.isdigit, key))
            if key_normalized == normalized:
                return customer
            if len(key_normalized) >= 10 and len(normalized) >= 10:
                if key_normalized[-10:] == normalized[-10:]:
                    return customer
        
        # Return None if not found
        return None
    
    def create_customer(self, phone_number: str, **kwargs) -> Dict:
        """Create a new customer record"""
        normalized = ''.join(filter(str.isdigit, phone_number))
        if len(normalized) >= 10:
            normalized = normalized[-10:]
        
        customer = {
            'phone_number': normalized,
            'name': kwargs.get('name', 'Unknown'),
            'email': kwargs.get('email', ''),
            'account_id': kwargs.get('account_id', f'ACC{random.randint(100000, 999999)}'),
            'plan': kwargs.get('plan', 'Unknown'),
            'monthly_bill': kwargs.get('monthly_bill', 0.0),
            'account_age_months': kwargs.get('account_age_months', 0),
            'previous_calls': 0,
            'last_call_date': None,
            'previous_sentiment': 'neutral',
            'notes': kwargs.get('notes', ''),
            'location': kwargs.get('location', 'Unknown')
        }
        
        self.customers[normalized] = customer
        return customer

