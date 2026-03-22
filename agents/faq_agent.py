"""
FAQ Agent - LangGraph StateGraph with RAG tool
Answers clinic questions using the knowledge base
"""
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
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

tools = [search_clinic_knowledge]
llm_with_tools = llm.bind_tools(tools)


def call_model(state: MessagesState):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "call_model")
builder.add_conditional_edges("call_model", tools_condition)
builder.add_edge("tools", "call_model")

faq_agent = builder.compile()
