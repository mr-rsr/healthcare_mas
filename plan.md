# Multi-Agent Appointment Booking System (MAS)
# Branch-Based Training Plan (Beginner Friendly)

Each branch is independently runnable with a CLI for testing.
Each branch builds on the previous one.

## Branch Overview

```
main (base setup)
  |
  +-- branch-1-rag          LangGraph agent + RAG tool (FAQ bot)
  |
  +-- branch-2-calendar      + Google Calendar booking via Composio MCP
  |
  +-- branch-3-gmail         + Gmail confirmation via Composio MCP
  |
  +-- branch-4-memory        + Short-term (checkpointer) + Long-term (Store API)
  |
  +-- branch-5-cli           + Polished CLI chat interface for testing
  |
  +-- branch-6-fastapi       + FastAPI serving with endpoints
```

---

## Branch: main (Base Setup)

**What**: Project skeleton, config, data files, dependencies

**Files**:
```
MAS/
├── .env.example
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── model.py            # LLM + embeddings
├── data/
│   ├── faq.pdf
│   ├── policy.pdf
│   └── CLINIC_Info.pdf
└── cli.py                  # Simple "hello" test to verify Bedrock works
```

**cli.py** — test LLM connectivity:
```python
from config.model import llm
response = llm.invoke("Say hello")
print(response.content)
```

**What you learn**: Project setup, AWS Bedrock connectivity

---

## Branch 1: branch-1-rag

**What**: LangGraph agent with RAG tool that answers clinic questions

**New files**:
```
├── rag/
│   ├── __init__.py
│   ├── ingest.py           # PDF -> Chroma
│   └── retriever.py        # Chroma retriever
├── tools/
│   ├── __init__.py
│   └── rag_tools.py        # search_clinic_knowledge @tool
├── agents/
│   └── faq_agent.py        # LangGraph ReAct agent with RAG tool
└── cli.py                  # Chat loop: ask clinic questions
```

**LangGraph pattern used**: `create_react_agent` (single agent + tool)

```python
# agents/faq_agent.py
from langgraph.prebuilt import create_react_agent
from config.model import llm
from tools.rag_tools import search_clinic_knowledge

faq_agent = create_react_agent(
    model=llm,
    tools=[search_clinic_knowledge],
    prompt="You are a helpful receptionist at HealthFirst Medical Clinic..."
)
```

**cli.py** — interactive chat:
```python
from agents.faq_agent import faq_agent

print("HealthFirst Clinic FAQ Bot (type 'quit' to exit)")
while True:
    user_input = input("\nYou: ")
    if user_input.lower() == "quit":
        break
    result = faq_agent.invoke({"messages": [("user", user_input)]})
    print(f"\nBot: {result['messages'][-1].content}")
```

**Demo**: "What are your hours?" / "Do you accept insurance?" / "Where is the clinic?"

**What you learn**: RAG pipeline, LangGraph react agent, tools

---

## Branch 2: branch-2-calendar

**What**: Add Google Calendar booking agent via Composio MCP

**New/changed files**:
```
├── tools/
│   └── mcp_tools.py        # Composio MCP client (calendar tools)
├── agents/
│   ├── faq_agent.py         # (from branch-1)
│   └── booking_agent.py     # LangGraph agent with calendar tool
└── cli.py                   # Choose: FAQ or Booking mode
```

**LangGraph pattern**: `create_react_agent` with MCP calendar tools

```python
# agents/booking_agent.py
from langgraph.prebuilt import create_react_agent
from config.model import llm
from tools.mcp_tools import get_calendar_tools

async def create_booking_agent():
    calendar_tools = await get_calendar_tools()
    return create_react_agent(
        model=llm,
        tools=calendar_tools,
        prompt="""You are a booking assistant at HealthFirst Medical Clinic.
Collect: patient name, email, doctor, date, time, reason.
Then create a Google Calendar event."""
    )
```

**cli.py** — mode selection:
```python
print("1. Ask a question (FAQ)")
print("2. Book an appointment")
choice = input("Choose: ")
# Route to faq_agent or booking_agent
```

**What you learn**: Composio MCP setup, external tool integration, async agents

---

## Branch 3: branch-3-gmail

**What**: Add Gmail confirmation agent via Composio MCP

**New/changed files**:
```
├── tools/
│   └── mcp_tools.py        # + Gmail tools added
├── agents/
│   └── confirmation_agent.py  # LangGraph agent with Gmail tool
└── cli.py                   # Full flow: FAQ / Book -> auto-confirm via email
```

**LangGraph pattern**: `create_react_agent` with Gmail tools

```python
# agents/confirmation_agent.py
from langgraph.prebuilt import create_react_agent
from config.model import llm
from tools.mcp_tools import get_gmail_tools

async def create_confirmation_agent():
    gmail_tools = await get_gmail_tools()
    return create_react_agent(
        model=llm,
        tools=gmail_tools,
        prompt="""You send appointment confirmation emails.
Include: patient name, doctor, date/time, clinic address, cancellation policy."""
    )
```

**cli.py** — booking triggers confirmation:
```python
# After booking completes:
print("\nSending confirmation email...")
result = await confirmation_agent.ainvoke({"messages": [
    ("user", f"Send confirmation to {email} for {doctor} on {date}")
]})
```

**What you learn**: Multi-tool MCP, chaining agents manually

---

## Branch 4: branch-4-memory

**What**: Add short-term memory (conversation persistence) + long-term memory (user preferences)

**New/changed files**:
```
├── agents/
│   ├── faq_agent.py         # + checkpointer for multi-turn
│   └── booking_agent.py     # + checkpointer + store for user prefs
└── cli.py                   # Multi-turn conversations, remembers user
```

**Short-term** (conversation within a session):
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
faq_agent = create_react_agent(
    model=llm,
    tools=[search_clinic_knowledge],
    checkpointer=checkpointer,
)

# Same thread_id = remembers conversation
config = {"configurable": {"thread_id": "user_session_1"}}
faq_agent.invoke({"messages": [("user", "What doctors do you have?")]}, config)
faq_agent.invoke({"messages": [("user", "Which one does cardiology?")]}, config)  # remembers context
```

**Long-term** (across sessions):
```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Save user preferences
store.put(("user_123", "preferences"), "doctor", {"name": "Dr. Chen"})

# Retrieve in next session
prefs = store.search(("user_123", "preferences"))
```

**cli.py** — shows memory in action:
```python
print("Returning user? Enter user_id (or 'new'):")
user_id = input("> ")
# Load previous preferences if they exist
# Conversation persists across turns with thread_id
```

**What you learn**: LangGraph checkpointer, Store API, thread_id, namespaces

---

## Branch 5: branch-5-cli

**What**: Polished CLI with all agents working together via LangGraph StateGraph

**New/changed files**:
```
├── agents/
│   ├── state.py             # AgentState TypedDict
│   └── supervisor.py        # Supervisor routing agent
├── graph/
│   ├── __init__.py
│   └── workflow.py          # StateGraph wiring all agents
└── cli.py                   # Full multi-agent CLI
```

**LangGraph pattern**: `StateGraph` with supervisor routing

```python
# graph/workflow.py
from langgraph.graph import StateGraph, START, END
from agents.state import AgentState

builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("faq_agent", faq_node)
builder.add_node("booking_agent", booking_node)
builder.add_node("confirmation_agent", confirmation_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_decision, {...})
builder.add_conditional_edges("booking_agent", after_booking, {...})
builder.add_edge("faq_agent", "supervisor")
builder.add_edge("confirmation_agent", "supervisor")

graph = builder.compile(checkpointer=checkpointer, store=store)
```

**cli.py** — full multi-agent chat:
```python
print("Welcome to HealthFirst Medical Clinic!")
print("You can ask questions, book appointments, or say goodbye.\n")

thread_id = str(uuid.uuid4())
while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "bye", "exit"]:
        break
    result = graph.invoke(
        {"messages": [("user", user_input)]},
        {"configurable": {"thread_id": thread_id, "user_id": "demo_user"}}
    )
    print(f"Bot: {result['messages'][-1].content}\n")
```

**What you learn**: StateGraph, supervisor routing, conditional edges, full multi-agent orchestration

---

## Branch 6: branch-6-fastapi

**What**: Serve the agent via FastAPI with REST endpoints

**New/changed files**:
```
├── main.py                  # FastAPI app
└── cli.py                   # kept for local testing
```

**Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message, get response |
| POST | `/chat/stream` | SSE streaming |
| GET | `/health` | Health check |
| POST | `/ingest` | Trigger RAG ingestion |

```python
# main.py
from fastapi import FastAPI
from graph.workflow import build_graph

app = FastAPI(title="HealthFirst Clinic Agent")
graph = build_graph()

@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {
        "thread_id": request.thread_id or str(uuid.uuid4()),
        "user_id": request.user_id
    }}
    result = await graph.ainvoke(
        {"messages": [("user", request.message)]}, config
    )
    return {"response": result["messages"][-1].content, ...}
```

**Test**: `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "What are your hours?", "user_id": "demo"}'`

**What you learn**: FastAPI serving, async LangGraph, production deployment

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | AWS Bedrock `ChatBedrockConverse` |
| Embeddings | AWS Bedrock `BedrockEmbeddings` (Titan v2) |
| Agent Framework | LangGraph (`create_react_agent` + `StateGraph`) |
| Short-term Memory | LangGraph `InMemorySaver` checkpointer |
| Long-term Memory | LangGraph `InMemoryStore` (Store API) |
| Vector Store | Chroma (persistent, local) |
| Gmail + Calendar | Composio MCP Server + `langchain-mcp-adapters` |
| Observability | LangSmith (env vars, auto-tracing) |
| API | FastAPI + uvicorn |

## Environment Variables (`.env.example`)

```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
COMPOSIO_API_KEY=
COMPOSIO_MCP_URL=http://localhost:3000/mcp
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=mas-clinic-booking
```

## Dependencies (`requirements.txt`)

```
langchain>=0.3.0
langchain-aws>=0.2.0
langchain-community>=0.3.0
langchain-mcp-adapters>=0.1.0
langgraph>=0.2.0
langsmith>=0.1.0
langchain-chroma>=0.1.0
composio-core>=0.6.0
mcp>=1.0.0
fastapi>=0.115.0
uvicorn>=0.30.0
python-dotenv>=1.0.0
boto3>=1.35.0
pydantic>=2.0.0
pypdf>=4.0.0
```
