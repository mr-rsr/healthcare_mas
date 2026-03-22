# Milestone 3: Gmail Confirmation via Composio MCP

## What You'll Build
Add a confirmation agent that sends appointment confirmation emails via Gmail after booking. The booking flow now chains: collect details -> create calendar event -> send email.

## What's New (from Milestone 2)
```
NEW  agents/confirmation_agent.py   # Confirmation node (Gmail MCP tools)
NEW  graph/confirmation_graph.py    # Confirmation StateGraph (async)
UPD  cli.py                         # 3 modes: FAQ / Booking+Email / Email test
```

## Architecture
```
CLI Menu
  |
  +-- [1] FAQ Mode -----------> faq_graph
  |
  +-- [2] Booking Mode -------> booking_graph
  |                                  |
  |                          (calendar event created?)
  |                                  |
  |                               YES: auto-trigger
  |                                  |
  |                          confirmation_graph
  |                                  |
  |                          (sends Gmail via MCP)
  |
  +-- [3] Email Test Mode ----> confirmation_graph (standalone)
```

## Prerequisites: Add Gmail to Composio

If you already set up Google Calendar in Milestone 2:

```bash
composio add gmail
```
This opens a browser for Google OAuth. Grant Gmail send permissions.

Then restart the MCP server:
```bash
composio mcp start
```

## Step-by-Step Code

### Step 1: Confirmation Agent Node (`agents/confirmation_agent.py`)

Same factory pattern as booking agent, but with Gmail tools:

```python
def create_confirmation_node(gmail_tools):
    llm_with_tools = llm.bind_tools(gmail_tools)

    def confirmation_node(state: MessagesState):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    return confirmation_node, gmail_tools
```

**Key concepts:**
- Same pattern as booking_agent — factory that accepts MCP tools
- System prompt includes email template details (clinic address, cancellation policy)
- LLM decides how to format the email and which Gmail tool to call

### Step 2: Confirmation Graph (`graph/confirmation_graph.py`)

Same async builder pattern:

```python
async def build_confirmation_graph():
    client = get_mcp_client()
    gmail_tools = await get_gmail_tools(client)
    confirmation_node, tools = create_confirmation_node(gmail_tools)

    builder = StateGraph(MessagesState)
    builder.add_node("confirmation_agent", confirmation_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "confirmation_agent")
    builder.add_conditional_edges("confirmation_agent", tools_condition)
    builder.add_edge("tools", "confirmation_agent")

    return builder.compile(), client
```

### Step 3: Chaining Booking -> Confirmation (`cli.py`)

After booking creates a calendar event, automatically trigger the confirmation email:

```python
# In the booking loop, after detecting a calendar tool was used:
if calendar_tool_was_used:
    print("Sending confirmation email...")
    summary = f"Send confirmation email based on: {response.content}"
    confirm_result = await confirmation_graph.ainvoke(
        {"messages": [("user", summary)]}
    )
```

**Key concepts:**
- Two separate graphs chained in the CLI (not yet a single multi-agent graph)
- The booking result is passed as context to the confirmation agent
- In Milestone 5, these will be wired together in one StateGraph with a supervisor

### Step 4: MCP Client Reuse (`tools/mcp_tools.py`)

Both agents use `get_mcp_client()` which connects to the same Composio server.
Calendar and Gmail tools are filtered by name:

```python
async def get_calendar_tools(client):
    tools = await client.get_tools()
    return [t for t in tools if "calendar" in t.name.lower()]

async def get_gmail_tools(client):
    tools = await client.get_tools()
    return [t for t in tools if "gmail" in t.name.lower()]
```

## Running It

### Terminal 1: Start Composio MCP server
```bash
composio mcp start
```

### Terminal 2: Run the CLI
```bash
python cli.py
```

### Test booking + email flow:
```
Choose: 2
You: Book an appointment for John Smith, john@email.com, with Dr. Chen, Monday 10am, annual checkup
Bot: I've created a calendar event...

Sending confirmation email...
Bot: I've sent a confirmation email to john@email.com with the appointment details.
```

### Test email standalone:
```
Choose: 3
You: Send a confirmation to test@email.com for Dr. Patel appointment on March 25 at 2pm
Bot: I've sent the confirmation email...
```

## What's Next (Milestone 4)
Add memory: conversation persistence (checkpointer) and user preferences (Store API).
