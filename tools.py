"""
Tool Functions for Nemotron Agent
These functions can be called by the AI based on customer requests
"""

import json
from datetime import datetime, timedelta
from customer_db import get_customer_by_phone

def check_bill(phone_number):
    """
    Get customer's monthly bill amount and due date
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Bill information including amount and due date
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {
            "error": "Customer not found",
            "monthly_bill": 0,
            "due_date": None
        }
    
    # Calculate next due date (15th of next month)
    today = datetime.now()
    if today.day < 15:
        due_date = today.replace(day=15)
    else:
        next_month = today.replace(day=1) + timedelta(days=32)
        due_date = next_month.replace(day=15)
    
    return {
        "monthly_bill": customer['monthly_bill'],
        "due_date": due_date.strftime("%Y-%m-%d"),
        "account_id": customer['account_id'],
        "payment_status": "current"
    }

def get_account_info(phone_number):
    """
    Get complete account information for customer
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Complete account information
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    return {
        "name": customer['name'],
        "account_id": customer['account_id'],
        "plan": customer['plan'],
        "monthly_bill": customer['monthly_bill'],
        "account_age_months": customer['account_age_months'],
        "location": customer['location'],
        "email": customer['email'],
        "status": "active"
    }

def check_plan(phone_number):
    """
    Get customer's current plan details
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Plan information including features and pricing
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    # Plan features based on plan type
    plan_features = {
        "Unlimited Premium": ["Unlimited talk, text, data", "100GB premium data", "HD streaming", "International calling"],
        "Unlimited Plus": ["Unlimited talk, text, data", "50GB premium data", "SD streaming", "Mobile hotspot"],
        "Magenta Max": ["Unlimited talk, text, data", "Unlimited premium data", "4K streaming", "International data"],
        "Magenta": ["Unlimited talk, text, data", "100GB premium data", "HD streaming"],
        "Essentials": ["Unlimited talk, text, data", "Basic features only"],
        "Go5G Plus": ["Unlimited talk, text, data", "100GB premium data", "Netflix included", "Apple TV+"],
        "Go5G": ["Unlimited talk, text, data", "50GB premium data", "HD streaming"]
    }
    
    return {
        "plan_name": customer['plan'],
        "monthly_cost": customer['monthly_bill'],
        "features": plan_features.get(customer['plan'], ["Standard features"]),
        "data_included": "Unlimited",
        "contract_type": "No contract"
    }

def get_call_history(phone_number):
    """
    Get customer's previous call history and interactions
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Call history including sentiment and notes
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    return {
        "total_calls": customer['previous_calls'],
        "last_call_date": customer['last_call_date'],
        "last_sentiment": customer['previous_sentiment'],
        "notes": customer['notes'],
        "account_age_months": customer['account_age_months']
    }

def check_data_usage(phone_number):
    """
    Get customer's current data usage statistics
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Data usage information
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    # Simulate data usage based on plan
    usage_percentages = {
        "Unlimited Premium": 65,
        "Unlimited Plus": 72,
        "Magenta Max": 58,
        "Magenta": 80,
        "Essentials": 45,
        "Go5G Plus": 68,
        "Go5G": 75
    }
    
    usage_pct = usage_percentages.get(customer['plan'], 50)
    
    return {
        "plan": customer['plan'],
        "data_used_gb": round(usage_pct * 0.5, 1),
        "data_limit": "Unlimited",
        "usage_percentage": usage_pct,
        "billing_cycle_end": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),
        "overage_charges": 0
    }

def get_payment_history(phone_number):
    """
    Get customer's payment history
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Payment history and status
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    return {
        "payment_status": "current",
        "last_payment_date": (datetime.now() - timedelta(days=18)).strftime("%Y-%m-%d"),
        "last_payment_amount": customer['monthly_bill'],
        "payment_method": "Auto-pay (Credit Card)",
        "outstanding_balance": 0,
        "account_age_months": customer['account_age_months']
    }

def check_network_status(phone_number):
    """
    Check network status and coverage for customer's location
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Network status information
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    return {
        "location": customer['location'],
        "network_status": "Operational",
        "signal_strength": "Excellent",
        "5g_available": True,
        "network_type": "5G",
        "outages": [],
        "coverage_quality": "Excellent"
    }

def get_upgrade_eligibility(phone_number):
    """
    Check if customer is eligible for device upgrade
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Upgrade eligibility information
    """
    customer = get_customer_by_phone(phone_number)
    
    if not customer:
        return {"error": "Customer not found"}
    
    # Eligible if account is older than 12 months
    eligible = customer['account_age_months'] >= 12
    
    return {
        "eligible": eligible,
        "account_age_months": customer['account_age_months'],
        "months_until_eligible": max(0, 12 - customer['account_age_months']),
        "available_upgrades": ["iPhone 15 Pro", "Samsung Galaxy S24", "Google Pixel 8"] if eligible else [],
        "upgrade_credit": 200 if eligible and customer['account_age_months'] >= 24 else 0,
        "trade_in_available": eligible
    }

def get_available_plans(phone_number):
    """
    Get list of available plans for customer
    
    Args:
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Available plans and pricing
    """
    customer = get_customer_by_phone(phone_number)
    
    current_plan = customer['plan'] if customer else None
    
    plans = [
        {"name": "Essentials", "price": 55, "data": "Unlimited", "features": "Basic"},
        {"name": "Magenta", "price": 70, "data": "Unlimited", "features": "HD Streaming"},
        {"name": "Unlimited Plus", "price": 85, "data": "Unlimited", "features": "50GB Premium + Hotspot"},
        {"name": "Magenta Max", "price": 90, "data": "Unlimited", "features": "Unlimited Premium + 4K"},
        {"name": "Unlimited Premium", "price": 95, "data": "Unlimited", "features": "100GB Premium + International"},
        {"name": "Go5G Plus", "price": 100, "data": "Unlimited", "features": "Premium + Netflix + Apple TV+"}
    ]
    
    return {
        "current_plan": current_plan,
        "available_plans": plans,
        "can_upgrade": True,
        "can_downgrade": True
    }

# Tool registry for easy lookup
AVAILABLE_TOOLS = {
    'check_bill': check_bill,
    'get_account_info': get_account_info,
    'check_plan': check_plan,
    'get_call_history': get_call_history,
    'check_data_usage': check_data_usage,
    'get_payment_history': get_payment_history,
    'check_network_status': check_network_status,
    'get_upgrade_eligibility': get_upgrade_eligibility,
    'get_available_plans': get_available_plans
}

def call_tool(tool_name, phone_number):
    """
    Call a tool by name with the customer's phone number
    
    Args:
        tool_name (str): Name of the tool to call
        phone_number (str): Customer's phone number
        
    Returns:
        dict: Result from the tool function
    """
    if tool_name in AVAILABLE_TOOLS:
        return AVAILABLE_TOOLS[tool_name](phone_number)
    else:
        return {"error": f"Tool '{tool_name}' not found"}

if __name__ == "__main__":
    # Test all tools
    test_phone = '+17206866656'
    
    print(f"Testing tools for {test_phone}...\n")
    
    for tool_name in AVAILABLE_TOOLS.keys():
        print(f"\n{'='*50}")
        print(f"Testing: {tool_name}")
        print('='*50)
        result = call_tool(tool_name, test_phone)
        print(json.dumps(result, indent=2))
    
    print("\n✅ All tools tested successfully")

