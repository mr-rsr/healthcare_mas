"""
Booking Agent - Node function for appointment booking via Google Calendar
Uses Composio MCP tools for calendar event creation
"""
from agents.state import AgentState
from config.model import llm

SYSTEM_PROMPT = """You are a booking assistant at HealthFirst Medical Clinic.

Your job is to help patients book appointments. Collect the following information:
- Patient name
- Patient email
- Doctor name (available: Dr. Sarah Chen, Dr. James Wilson, Dr. Priya Patel, Dr. Michael Rodriguez, Dr. Emily Thompson)
- Preferred date
- Preferred time (clinic hours: Mon-Fri 9AM-5PM, Thu until 7PM)
- Reason for visit

Once you have all details, use the Google Calendar tool to create the appointment.
Confirm the booking details with the patient before creating the event.
Be friendly and professional."""


def create_booking_node(calendar_tools):
    """Factory: creates a booking node with calendar tools bound to the LLM."""
    llm_with_tools = llm.bind_tools(calendar_tools)

    def booking_node(state: AgentState):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return booking_node, calendar_tools
