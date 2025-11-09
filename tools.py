CUSTOMER_CARE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_bill_info",
            "description": "Get current bill amount and due date",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Customer account ID"}
                },
                "required": ["account_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "make_payment",
            "description": "Record a payment from customer",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Customer account ID"},
                    "amount": {"type": "number", "description": "Payment amount"}
                },
                "required": ["account_id", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_dashboard_report",
            "description": "Write customer interaction report to dashboard",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string", "description": "Customer account ID"},
                    "report_type": {"type": "string", "description": "billing/technical/complaint"},
                    "content": {"type": "string", "description": "Report content"}
                },
                "required": ["account_id", "report_type", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate to human agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["account_id", "reason"]
            }
        }
    }
]
