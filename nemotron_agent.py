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
        
        # System prompt for conversational agent with LLM reasoning
        self.system_prompt = """You are an intelligent customer service AI assistant having a natural phone conversation.

Your capabilities:
- Understand customer needs through natural conversation
- Proactively call tools when needed (don't wait to be asked)
- Maintain conversation context and reference previous information
- Be concise and natural (1-3 sentences per response)
- Think about what the customer wants and act accordingly

Available tools:
- get_bill_info: Get billing information for an account
- make_payment: Process a payment
- write_dashboard_report: Create reports for follow-up
- escalate_to_human: Escalate complex issues to human agents

Guidelines:
- If customer mentions billing/payment/balance/amount, proactively check their bill using get_bill_info
- If they want to pay or mention payment, use make_payment
- If they seem frustrated or have complex issues, escalate to human
- Be conversational - respond like a helpful human would
- Don't ask permission to use tools - just use them when appropriate
- Reference previous conversation naturally (e.g., "As I mentioned..." or "Your bill of $125...")
- Keep responses brief and natural for phone conversation
- If you already have information from tools, don't call them again unnecessarily
"""
        
        logger.info(f"✓ Conversational Agent initialized: {model_name}")
    
    def process_conversation_turn(self, conversation_history, account_id):
        """
        Process one turn of conversation with full LLM reasoning
        
        Args:
            conversation_history: List of {"role": "user/assistant", "content": "..."}
            account_id: Customer account ID
        
        Returns:
            str: AI's response to speak to the user
        """
        
        # Build messages with system prompt + conversation
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add context about the account
        messages.append({
            "role": "system",
            "content": f"Current customer account ID: {account_id}"
        })
        
        try:
            # FIRST LLM CALL: Let AI reason and decide actions
            logger.info(f"🧠 Sending {len(conversation_history)} messages to LLM for reasoning")
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",  # LLM decides if tools needed
                max_tokens=512,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # If LLM wants to use tools
            if assistant_message.tool_calls:
                logger.info(f"🧠 LLM decided to call {len(assistant_message.tool_calls)} tool(s)")
                
                # Add assistant's tool call to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute each tool the LLM requested
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🔧 Executing: {tool_name}({tool_args})")
                    
                    # Execute tool
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    logger.info(f"✓ Tool result: {tool_result}")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # SECOND LLM CALL: Generate natural response with tool results
                final_response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=512,
                    temperature=0.7
                )
                
                response_text = final_response.choices[0].message.content
                
                logger.info(f"🤖 Final response: {response_text}")
                
                return response_text or "I've looked that up for you."
            
            # No tools needed - direct response
            response_text = assistant_message.content or "I'm here to help!"
            
            logger.info(f"🤖 Direct response: {response_text}")
            
            return response_text
        
        except Exception as e:
            logger.error(f"❌ Agent error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "I'm sorry, I'm having trouble processing that. Could you try again?"
    
    def process_customer_inquiry(self, account_id, intent, slots, transcription):
        """Legacy method for backward compatibility"""
        # Convert to conversation format
        conversation_history = [
            {"role": "user", "content": transcription}
        ]
        return {
            "success": True,
            "response": self.process_conversation_turn(conversation_history, account_id)
        }
    
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
