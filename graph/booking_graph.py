"""
Booking Graph - Wires the booking agent node into a LangGraph StateGraph
"""
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from agents.booking_agent import create_booking_node
from tools.mcp_tools import get_mcp_client, get_calendar_tools


async def build_booking_graph():
    """Build and return the booking graph with MCP calendar tools."""
    client = get_mcp_client()
    calendar_tools = await get_calendar_tools(client)

    if not calendar_tools:
        raise RuntimeError("No calendar tools found. Is Composio MCP server running?")

    booking_node, tools = create_booking_node(calendar_tools)

    builder = StateGraph(MessagesState)
    builder.add_node("booking_agent", booking_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "booking_agent")
    builder.add_conditional_edges("booking_agent", tools_condition)
    builder.add_edge("tools", "booking_agent")

    return builder.compile(), client
