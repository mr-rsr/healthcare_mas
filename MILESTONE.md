# Milestone 2: Google Calendar Booking via Composio MCP

## What You'll Build
Add an appointment booking agent that creates Google Calendar events using the Composio MCP Server. The CLI now has two modes: FAQ and Booking.

## What's New (from Milestone 1)
```
NEW  tools/mcp_tools.py          # Composio MCP client (calendar + gmail tools)
NEW  agents/booking_agent.py     # Booking node function (calendar tools)
NEW  graph/booking_graph.py      # Booking StateGraph (async, MCP tools)
UPD  cli.py                      # Mode selection: FAQ or Booking
```

## Architecture
```
CLI Menu
  |
  +-- [1] FAQ Mode ---------> faq_graph (from milestone 1)
  |
  +-- [2] Booking Mode -----> booking_graph
                                   |
                          booking_agent node
                                   |
                          tools_condition?
                           /           \
                         YES            NO
                          |              |
                    ToolNode            END
                    (Calendar MCP)
                          |
                    back to booking_agent
```

## How Composio MCP Works

```
Composio MCP Server (localhost:3000)
    |-- Exposes Gmail + Calendar as MCP tools
    |-- Handles OAuth with Google
    v
langchain-mcp-adapters (MultiServerMCPClient)
    |-- Connects via streamable_http transport
    |-- Converts MCP tools --> LangChain tools
    v
LangGraph agent (bind_tools + ToolNode)
    |-- LLM decides when to call calendar tools
    |-- ToolNode executes the MCP tool calls
```

## Prerequisites: Composio Setup (One-Time)

### 1. Install Composio CLI
```bash
pip install composio-core
```

### 2. Login to Composio
```bash
composio login
```

### 3. Add Google Calendar integration
```bash
composio add googlecalendar
```
This opens a browser for Google OAuth. Grant calendar permissions.

### 4. Start the MCP server
```bash
composio mcp start
```
This starts the MCP server on `http://localhost:3000/mcp`.

### 5. Verify it's running
```bash
curl http://localhost:3000/mcp
```

## Step-by-Step Code

### Step 1: MCP Client (`tools/mcp_tools.py`)

Connects to the Composio MCP server and loads tools:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

COMPOSIO_MCP_URL = os.getenv("COMPOSIO_MCP_URL", "http://localhost:3000/mcp")

async def get_mcp_client():
    client = MultiServerMCPClient(
        {
            "composio": {
                "url": COMPOSIO_MCP_URL,
                "transport": "streamable_http",
            }
        }
    )
    return client

async def get_calendar_tools(client):
    tools = await client.get_tools()
    return [t for t in tools if "calendar" in t.name.lower()]
```

**Key concepts:**
- `MultiServerMCPClient` - Connects to one or more MCP servers
- `streamable_http` - Transport protocol for HTTP-based MCP servers
- Tools are loaded async at runtime (not at import time)
- Filter by name to get only calendar-related tools

### Step 2: Booking Agent Node (`agents/booking_agent.py`)

Factory pattern — tools are injected at runtime since MCP tools are async:

```python
def create_booking_node(calendar_tools):
    llm_with_tools = llm.bind_tools(calendar_tools)

    def booking_node(state: MessagesState):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return booking_node, calendar_tools
```

**Key concepts:**
- Factory pattern: MCP tools aren't available at import time (they're async)
- `create_booking_node()` is called after tools are loaded
- Returns both the node function and tools (needed for ToolNode)

### Step 3: Booking Graph (`graph/booking_graph.py`)

Async graph builder — connects to MCP, loads tools, wires the graph:

```python
async def build_booking_graph():
    client = get_mcp_client()
    calendar_tools = await get_calendar_tools(client)

    booking_node, tools = create_booking_node(calendar_tools)

    builder = StateGraph(MessagesState)
    builder.add_node("booking_agent", booking_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "booking_agent")
    builder.add_conditional_edges("booking_agent", tools_condition)
    builder.add_edge("tools", "booking_agent")

    return builder.compile(), client
```

**Key concepts:**
- Graph is built async because MCP tools are loaded at runtime
- Returns both the compiled graph AND the client (for cleanup)
- Same StateGraph pattern as FAQ, but with MCP tools instead of RAG

### Step 4: Updated CLI (`cli.py`)

Mode selection — FAQ (sync) or Booking (async):

```python
def main():
    while True:
        print("1. Ask a question (FAQ)")
        print("2. Book an appointment")
        print("q. Quit")
        choice = input("Choose: ")

        if choice == "1":
            run_faq()          # sync - uses faq_graph directly
        elif choice == "2":
            asyncio.run(run_booking())  # async - needs MCP connection
```

**Key concepts:**
- FAQ mode is sync (RAG tools are local)
- Booking mode is async (MCP tools require network connection)
- `asyncio.run()` bridges sync CLI with async MCP operations
- MCP client is cleaned up with `await client.close()` in finally block

## Running It

### Terminal 1: Start Composio MCP server
```bash
composio mcp start
```

### Terminal 2: Run the CLI
```bash
python cli.py
```

### Test the booking flow:
```
Choose: 2
You: I want to book an appointment
Bot: I'd be happy to help! Let me collect some details...
You: John Smith, john@email.com, Dr. Chen, next Monday at 10am, annual checkup
Bot: I've created a calendar event for your appointment...
```

## What's Next (Milestone 3)
Add Gmail confirmation — after booking, automatically send a confirmation email.
