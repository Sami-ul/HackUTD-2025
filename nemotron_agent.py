from openai import OpenAI
import json
import logging
import os
from tools import CUSTOMER_CARE_TOOLS
from mock_database import db

logger = logging.getLogger(__name__)

class NemotronCustomerCareAgent:
    def __init__(self, model_name="nvidia/nemotron-nano-9b-v2:free"):
        self.model_name = model_name
        
        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.tools = CUSTOMER_CARE_TOOLS
        logger.info(f"Initialized Nemotron Agent with: {model_name}")
    
    def process_customer_inquiry(self, account_id, intent, slots, transcription):
        context = f"""
You are a customer service agent. Help this customer:
- Account ID: {account_id}
- Their intent: {intent}
- They said: "{transcription}"

Use tools when needed. Be helpful and concise.
"""
        
        messages = [{"role": "user", "content": context}]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                max_tokens=512,
                temperature=0.7
            )
            
            assistant_message = response.choices.message
            
            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    logger.info(f"Executing tool: {tool_name}")
                    self._execute_tool(tool_name, tool_args)
            
            return {
                "success": True,
                "response": assistant_message.content
            }
        
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return {"success": False, "error": str(e)}
    
    def _execute_tool(self, tool_name, tool_args):
        if tool_name == "get_bill_info":
            return db.get_bill_info(tool_args.get("account_id"))
        elif tool_name == "make_payment":
            return db.make_payment(tool_args.get("account_id"), tool_args.get("amount"))
        elif tool_name == "write_dashboard_report":
            return db.write_dashboard_report(
                tool_args.get("account_id"),
                tool_args.get("report_type"),
                tool_args.get("content")
            )
        elif tool_name == "escalate_to_human":
            return db.escalate_to_human(tool_args.get("account_id"), tool_args.get("reason"))
