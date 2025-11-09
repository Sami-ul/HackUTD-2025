"""
Customer Database Helper Module
Provides functions to access customer data from JSON file
"""

import json
import os

DATABASE_FILE = 'customer_database.json'

def load_customer_database():
    """Load customer database from JSON file"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), DATABASE_FILE)
        with open(db_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Customer database not found: {DATABASE_FILE}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in customer database")
        return []

def get_customer_by_phone(phone_number):
    """
    Get customer information by phone number
    
    Args:
        phone_number (str): Phone number to search for
        
    Returns:
        dict: Customer information or None if not found
    """
    customers = load_customer_database()
    
    # Normalize phone number (remove spaces, dashes, etc.)
    normalized_search = phone_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    for customer in customers:
        normalized_customer = customer['phone_number'].replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if normalized_customer == normalized_search:
            return customer
    
    return None

def get_customer_context(phone_number):
    """
    Get formatted customer context string for LLM
    
    Args:
        phone_number (str): Phone number to search for
        
    Returns:
        str: Formatted customer context or default message
    """
    customer = get_customer_by_phone(phone_number)
    
    if customer:
        context = f"""
Customer Information:
- Name: {customer['name']}
- Account ID: {customer['account_id']}
- Plan: {customer['plan']}
- Monthly Bill: ${customer['monthly_bill']}
- Account Age: {customer['account_age_months']} months
- Location: {customer['location']}
- Previous Calls: {customer['previous_calls']}
- Last Sentiment: {customer['previous_sentiment']}
- Notes: {customer['notes']}
"""
        return context
    else:
        return "Customer information not found in database. Treat as new customer."

if __name__ == "__main__":
    # Test the module
    print("Testing customer database...")
    
    test_numbers = ['+17206866656', '+17202990300', '+15551234567']
    
    for number in test_numbers:
        customer = get_customer_by_phone(number)
        if customer:
            print(f"\n✅ Found: {customer['name']} ({number})")
            print(f"   Plan: {customer['plan']}, Bill: ${customer['monthly_bill']}")
        else:
            print(f"\n❌ Not found: {number}")

