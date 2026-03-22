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


def build_workflow():
    """Build the full multi-agent StateGraph."""
    client = get_mcp_client()

    # Load MCP tools
    calendar_tools = get_calendar_tools(client)
    gmail_tools = get_gmail_tools(client)

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

    # Edges: START -> supervisor
    builder.add_edge(START, "supervisor")

    # Supervisor routes to the right agent or END
    builder.add_conditional_edges("supervisor", route_supervisor, {
        "faq_agent": "faq_agent",
        "booking_agent": "booking_agent",
        END: END,
    })

    # FAQ: tools_condition routes to "faq_tools" if tool calls, else back to "supervisor"
    builder.add_conditional_edges("faq_agent", tools_condition, {
        "tools": "faq_tools",
        END: "supervisor",
    })
    builder.add_edge("faq_tools", "faq_agent")

    # Booking: tools_condition routes to "booking_tools" if tool calls, else to "confirmation_agent"
    builder.add_conditional_edges("booking_agent", tools_condition, {
        "tools": "booking_tools",
        END: "confirmation_agent",
    })
    builder.add_edge("booking_tools", "booking_agent")

    # Confirmation: tools_condition routes to "confirmation_tools" if tool calls, else back to "supervisor"
    builder.add_conditional_edges("confirmation_agent", tools_condition, {
        "tools": "confirmation_tools",
        END: "supervisor",
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
