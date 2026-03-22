"""
Shared agent state for the multi-agent system
"""
from typing import Optional
from typing_extensions import TypedDict, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class BookingDetails(TypedDict, total=False):
    patient_name: str
    patient_email: str
    doctor_name: str
    appointment_date: str
    appointment_time: str
    reason: str


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str
    booking_details: Optional[BookingDetails]
    booking_complete: bool
    confirmation_sent: bool
