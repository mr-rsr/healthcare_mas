"""
Supervisor - Routes user requests to the appropriate agent
Uses structured output for deterministic routing
"""
from pydantic import BaseModel, Field
from config.model import llm
from agents.state import AgentState


class RouteDecision(BaseModel):
    """Supervisor routing decision."""
    next_agent: str = Field(
        description="The next agent to handle the request. "
        "Must be one of: 'faq_agent', 'booking_agent', 'FINISH'"
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )


SYSTEM_PROMPT = """You are a supervisor routing requests at HealthFirst Medical Clinic.

Analyze the user's message and route to the appropriate agent:

- **faq_agent**: Questions about clinic hours, location, doctors, policies, services, insurance, what to bring, parking, telehealth, lab work.
- **booking_agent**: Requests to book, schedule, or make an appointment. Also if the user is in the middle of providing booking details (name, email, doctor, date, time, reason).
- **FINISH**: The user is saying goodbye, thanks, or the conversation is complete.

Rules:
- If booking is in progress (booking_complete is False and user seems to be providing details), route to booking_agent.
- If unsure, route to faq_agent.
- Only route to FINISH if the user clearly wants to end the conversation."""

router_llm = llm.with_structured_output(RouteDecision)


def supervisor_node(state: AgentState):
    """Route the user request to the appropriate agent."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]

    # Add context about booking state
    if state.get("booking_complete") is False and state.get("booking_details"):
        messages.append({
            "role": "system",
            "content": "NOTE: A booking is currently in progress. Route to booking_agent unless the user clearly wants something else."
        })

    decision = router_llm.invoke(messages)
    return {"next_agent": decision.next_agent}
