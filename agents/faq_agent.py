"""
FAQ Agent - LangGraph ReAct agent with RAG tool
Answers clinic questions using the knowledge base
"""
from langgraph.prebuilt import create_react_agent
from config.model import llm
from tools.rag_tools import search_clinic_knowledge

SYSTEM_PROMPT = """You are a helpful receptionist at HealthFirst Medical Clinic.

Use the search_clinic_knowledge tool to find answers to patient questions about:
- Clinic hours, location, parking, public transit
- Doctor names and specialties
- Insurance, payment, cancellation policies
- Services offered, lab work, telehealth
- How to book appointments, what to bring

Always search the knowledge base before answering. If the information is not found,
suggest the patient call the clinic at (555) 123-4567.
Be friendly, concise, and professional."""

faq_agent = create_react_agent(
    model=llm,
    tools=[search_clinic_knowledge],
    prompt=SYSTEM_PROMPT,
)
