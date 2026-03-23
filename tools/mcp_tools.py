"""
MCP Tools - Connect to Composio MCP Server for Google Calendar
Uses langchain-mcp-adapters to convert MCP tools to LangChain tools
"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_mcp_adapters.client import MultiServerMCPClient

COMPOSIO_MCP_URL = os.getenv("COMPOSIO_MCP_URL", "")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")


def get_mcp_client():
    """Create and return a MultiServerMCPClient connected to Composio."""
    client = MultiServerMCPClient(
        {
            "composio": {
                "url": COMPOSIO_MCP_URL,
                "transport": "streamable_http",
                "headers": {
                    "x-api-key": COMPOSIO_API_KEY,
                },
            }
        }
    )
    return client


async def get_calendar_tools(client: MultiServerMCPClient):
    """Filter and return only Google Calendar tools."""
    tools = await client.get_tools()
    return [t for t in tools if "calendar" in t.name.lower()]
