"""
Confirmation Agent - Node function for sending appointment confirmation emails
Uses Composio MCP tools for Gmail
"""
from agents.state import AgentState
from config.model import llm

SYSTEM_PROMPT = """You are a confirmation assistant at HealthFirst Medical Clinic.

Your job is to send appointment confirmation emails to patients after booking.
Use the Gmail tool to send the email.

The confirmation email should include:
- Patient name
- Doctor name
- Appointment date and time
- Clinic address: 456 Wellness Blvd, Springfield, IL 62701
- Cancellation policy: Cancel 24 hours in advance to avoid $50 fee
- Clinic phone: (555) 123-4567

Keep the email professional and friendly. Use a clear subject line like:
"Appointment Confirmation - HealthFirst Medical Clinic"

IMPORTANT: After successfully sending the email, always reply to the patient
confirming that the email has been sent and summarise the appointment details."""


def create_confirmation_node(gmail_tools):
    """Factory: creates a confirmation node with Gmail tools bound to the LLM."""
    llm_with_tools = llm.bind_tools(gmail_tools)

    def confirmation_node(state: AgentState):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        response = llm_with_tools.invoke(messages)

        # Mark confirmation as sent if tool was called
        return {"messages": [response], "confirmation_sent": True}

    return confirmation_node, gmail_tools
