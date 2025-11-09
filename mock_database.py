class MockCustomerDatabase:
    def __init__(self):
        self.customers = {
            "12345": {
                "name": "John Smith",
                "bill_amount": 125.50,
                "due_date": "2025-11-15"
            },
            "67890": {
                "name": "Jane Doe",
                "bill_amount": 85.00,
                "due_date": "2025-11-10"
            }
        }
        self.reports = []
    
    def get_bill_info(self, account_id):
        if account_id in self.customers:
            customer = self.customers[account_id]
            return {
                "success": True,
                "bill_amount": customer["bill_amount"],
                "due_date": customer["due_date"]
            }
        return {"success": False, "error": "Account not found"}
    
    def make_payment(self, account_id, amount):
        if account_id in self.customers:
            self.customers[account_id]["bill_amount"] = max(0, 
                self.customers[account_id]["bill_amount"] - amount)
            return {"success": True, "new_balance": self.customers[account_id]["bill_amount"]}
        return {"success": False, "error": "Account not found"}
    
    def write_dashboard_report(self, account_id, report_type, content):
        self.reports.append({
            "account_id": account_id,
            "type": report_type,
            "content": content
        })
        return {"success": True}
    
    def escalate_to_human(self, account_id, reason):
        return {"success": True, "message": "Escalated to human agent"}

db = MockCustomerDatabase()
