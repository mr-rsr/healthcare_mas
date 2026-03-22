"""
MCP Tools - Connect to Composio MCP Server for Gmail and Google Calendar
Uses langchain-mcp-adapters to convert MCP tools to LangChain tools
"""
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

COMPOSIO_MCP_URL = os.getenv("COMPOSIO_MCP_URL", "http://localhost:3000/mcp")


async def get_mcp_client():
    """Create and return a MultiServerMCPClient connected to Composio."""
    client = MultiServerMCPClient(
        {
            "composio": {
                "url": COMPOSIO_MCP_URL,
                "transport": "streamable_http",
            }
        }
    )
    return client


async def get_all_tools(client: MultiServerMCPClient):
    """Load all MCP tools from the Composio server."""
    return await client.get_tools()


async def get_calendar_tools(client: MultiServerMCPClient):
    """Filter and return only Google Calendar tools."""
    tools = await client.get_tools()
    return [t for t in tools if "calendar" in t.name.lower()]


async def get_gmail_tools(client: MultiServerMCPClient):
    """Filter and return only Gmail tools."""
    tools = await client.get_tools()
    return [t for t in tools if "gmail" in t.name.lower()]
