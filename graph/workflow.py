"""
Multi-Agent Workflow - Full StateGraph with supervisor routing
Wires: supervisor -> faq_agent / booking_agent -> confirmation_agent
"""
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from config.memory import checkpointer, store
from agents.state import AgentState
from agents.supervisor import supervisor_node
from agents.faq_agent import faq_node, tools as faq_tools
from agents.booking_agent import create_booking_node
from agents.confirmation_agent import create_confirmation_node
from tools.mcp_tools import get_mcp_client, get_calendar_tools, get_gmail_tools


def route_supervisor(state: AgentState):
    """Route based on supervisor's decision."""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return END
    return next_agent


def route_after_faq(state: AgentState):
    """After FAQ responds, check if it needs tools or go back to supervisor."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "faq_tools"
    return "supervisor"


def route_after_booking(state: AgentState):
    """After booking responds, check if it needs tools or go back to supervisor."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "booking_tools"
    # If booking just completed (tool result came back), trigger confirmation
    if state.get("booking_complete"):
        return "confirmation_agent"
    return "supervisor"


def route_after_confirmation(state: AgentState):
    """After confirmation responds, check if it needs tools or go back to supervisor."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "confirmation_tools"
    return "supervisor"


async def build_workflow():
    """Build the full multi-agent StateGraph. Async because MCP tools are loaded at runtime."""
    client = get_mcp_client()

    # Load MCP tools
    calendar_tools = await get_calendar_tools(client)
    gmail_tools = await get_gmail_tools(client)

    if not calendar_tools:
        raise RuntimeError("No calendar tools found. Is Composio MCP server running?")
    if not gmail_tools:
        raise RuntimeError("No Gmail tools found. Is Composio MCP server running?")

    booking_node, booking_tools_list = create_booking_node(calendar_tools)
    confirmation_node, confirmation_tools_list = create_confirmation_node(gmail_tools)

    # Build the graph
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("faq_agent", faq_node)
    builder.add_node("faq_tools", ToolNode(faq_tools))
    builder.add_node("booking_agent", booking_node)
    builder.add_node("booking_tools", ToolNode(booking_tools_list))
    builder.add_node("confirmation_agent", confirmation_node)
    builder.add_node("confirmation_tools", ToolNode(confirmation_tools_list))

    # Edges
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", route_supervisor, {
        "faq_agent": "faq_agent",
        "booking_agent": "booking_agent",
        END: END,
    })

    # FAQ: call tools if needed, then back to supervisor
    builder.add_conditional_edges("faq_agent", route_after_faq, {
        "faq_tools": "faq_tools",
        "supervisor": "supervisor",
    })
    builder.add_edge("faq_tools", "faq_agent")

    # Booking: call tools if needed, then confirmation or supervisor
    builder.add_conditional_edges("booking_agent", route_after_booking, {
        "booking_tools": "booking_tools",
        "confirmation_agent": "confirmation_agent",
        "supervisor": "supervisor",
    })
    builder.add_edge("booking_tools", "booking_agent")

    # Confirmation: call tools if needed, then back to supervisor
    builder.add_conditional_edges("confirmation_agent", route_after_confirmation, {
        "confirmation_tools": "confirmation_tools",
        "supervisor": "supervisor",
    })
    builder.add_edge("confirmation_tools", "confirmation_agent")

    graph = builder.compile(checkpointer=checkpointer, store=store)
    return graph, client


def build_faq_only_workflow():
    """Build a FAQ-only graph (no MCP needed). Useful for testing without Composio."""
    from langgraph.graph import MessagesState

    builder = StateGraph(MessagesState)
    builder.add_node("faq_agent", faq_node)
    builder.add_node("tools", ToolNode(faq_tools))

    builder.add_edge(START, "faq_agent")
    builder.add_conditional_edges("faq_agent", tools_condition)
    builder.add_edge("tools", "faq_agent")

    return builder.compile(checkpointer=checkpointer)
