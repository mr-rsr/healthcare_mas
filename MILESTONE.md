# Milestone 5: Full Multi-Agent System with Supervisor

## What You'll Build
Wire all agents into a single LangGraph StateGraph with a supervisor that automatically routes user requests to the right agent.

## What's New (from Milestone 4)
```
NEW  agents/state.py               # Shared AgentState TypedDict
NEW  agents/supervisor.py          # Supervisor routing with structured output
NEW  graph/workflow.py             # Full StateGraph with all agents + routing
UPD  agents/faq_agent.py           # Uses AgentState instead of MessagesState
UPD  agents/booking_agent.py       # Uses AgentState
UPD  agents/confirmation_agent.py  # Uses AgentState
UPD  cli.py                        # --full flag for multi-agent mode
```

## Architecture
```
User Message
    |
    v
[supervisor] -- structured output --> RouteDecision
    |                                    |
    +-- "faq_agent" -----> [faq_agent] --+--> [faq_tools] (RAG)
    |                          |              |
    |                          +<-------------+
    |                          |
    |                          +--> back to [supervisor]
    |
    +-- "booking_agent" -> [booking_agent] --+--> [booking_tools] (Calendar MCP)
    |                          |                   |
    |                          +<------------------+
    |                          |
    |                    (booking_complete?)
    |                     YES: [confirmation_agent] --+--> [confirmation_tools] (Gmail MCP)
    |                          |                           |
    |                          +<--------------------------+
    |                          |
    |                          +--> back to [supervisor]
    |
    +-- "FINISH" -------> END
```

## Key Concepts

### 1. Custom State (`agents/state.py`)

Shared state across all agents — more than just messages:

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str              # supervisor's routing decision
    booking_details: Optional[BookingDetails]
    booking_complete: bool
    confirmation_sent: bool
```

**Why custom state?**
- `MessagesState` only has `messages`
- We need `next_agent` for routing, `booking_complete` for flow control
- `add_messages` reducer appends new messages (doesn't replace)

### 2. Supervisor with Structured Output (`agents/supervisor.py`)

Deterministic routing using Pydantic model:

```python
class RouteDecision(BaseModel):
    next_agent: str   # "faq_agent", "booking_agent", or "FINISH"
    reasoning: str

router_llm = llm.with_structured_output(RouteDecision)

def supervisor_node(state: AgentState):
    decision = router_llm.invoke(messages)
    return {"next_agent": decision.next_agent}
```

**Key concepts:**
- `with_structured_output()` forces LLM to return valid JSON matching the Pydantic schema
- No string parsing — guaranteed to get one of the valid agent names
- `reasoning` field helps with debugging (why did it route there?)

### 3. Conditional Edges (`graph/workflow.py`)

The graph uses conditional edges for routing:

```python
# Supervisor routes to the right agent
builder.add_conditional_edges("supervisor", route_supervisor, {
    "faq_agent": "faq_agent",
    "booking_agent": "booking_agent",
    END: END,
})

# Each agent checks: need tools? or back to supervisor?
builder.add_conditional_edges("faq_agent", route_after_faq, {
    "faq_tools": "faq_tools",
    "supervisor": "supervisor",
})
```

**Key concepts:**
- `add_conditional_edges(node, function, mapping)` — function returns a key, mapping resolves to next node
- Each agent has its own tool node (faq_tools, booking_tools, confirmation_tools)
- After tool execution, control returns to the agent for another LLM call
- After the agent responds (no tool calls), control goes back to supervisor

### 4. Separate Tool Nodes

Each agent gets its own ToolNode to avoid tool name conflicts:

```python
builder.add_node("faq_tools", ToolNode(faq_tools))           # RAG
builder.add_node("booking_tools", ToolNode(booking_tools))    # Calendar MCP
builder.add_node("confirmation_tools", ToolNode(gmail_tools)) # Gmail MCP
```

### 5. Booking -> Confirmation Chain

After booking completes, automatically triggers confirmation:

```python
def route_after_booking(state):
    if state["messages"][-1].tool_calls:
        return "booking_tools"
    if state.get("booking_complete"):
        return "confirmation_agent"    # auto-trigger email
    return "supervisor"
```

## Running It

### FAQ-only mode (no MCP needed):
```bash
python cli.py
```

### Full multi-agent mode (needs Composio MCP):
```bash
# Terminal 1: Start MCP server
composio mcp start

# Terminal 2: Run CLI
python cli.py --full
```

### Test supervisor routing:
```
You: What are your hours?
Bot: [supervisor -> faq_agent] Our hours are Mon-Fri 9-5, Thu until 7...

You: I want to book an appointment
Bot: [supervisor -> booking_agent] I'd be happy to help! What's your name?

You: John Smith
Bot: [supervisor -> booking_agent] And your email?
(booking_agent continues collecting details)

You: Thanks, bye!
Bot: [supervisor -> FINISH] Goodbye!
```

## What's Next (Milestone 6)
Add FastAPI endpoints to serve the agent via REST API.
