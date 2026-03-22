"""
MCP Tools - Connect to Composio MCP Server for Gmail and Google Calendar
Uses langchain-mcp-adapters to convert MCP tools to LangChain tools
"""
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

COMPOSIO_MCP_URL = os.getenv(
    "COMPOSIO_MCP_URL",
    "https://backend.composio.dev/v3/mcp/9136c46c-19e6-4e0e-bd3e-471d3e36207a/mcp?user_id=pg-test-5ec3bf32-c31d-49ed-b75f-a03c3a2dc300",
)
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")


def get_mcp_client():
    """Create and return a MultiServerMCPClient connected to Composio."""
    client = MultiServerMCPClient(
        {
            "composio": {
                "url": COMPOSIO_MCP_URL,
                "transport": "http",
                "headers": {
                    "x-api-key": COMPOSIO_API_KEY,
                },
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
