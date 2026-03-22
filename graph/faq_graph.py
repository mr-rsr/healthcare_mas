"""
FAQ Graph - Wires the FAQ agent node into a LangGraph StateGraph
"""
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from config.memory import checkpointer
from agents.faq_agent import faq_node, tools

# Build the graph
builder = StateGraph(MessagesState)
builder.add_node("faq_agent", faq_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "faq_agent")
builder.add_conditional_edges("faq_agent", tools_condition)
builder.add_edge("tools", "faq_agent")

faq_graph = builder.compile(checkpointer=checkpointer)
