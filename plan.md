# Multi-Agent Appointment Booking System (MAS)
# Branch-Based Training Plan

Each branch is a working milestone with CLI, MILESTONE.md, and builds on the previous.
**main** = final result with Streamlit UI + FastAPI.

## Branch Flow

```
branch-1-rag          FAQ agent + RAG (CLI)
    |
branch-2-calendar     + Google Calendar booking via Composio MCP (CLI)
    |
branch-3-gmail        + Gmail confirmation via Composio MCP (CLI)
    |
branch-4-memory       + Checkpointer + Store API (CLI)
    |
branch-5-multi-agent  Full StateGraph with supervisor routing (CLI)
    |
branch-6-fastapi      + FastAPI REST endpoints
    |
main                  + Streamlit UI (final result)
```

## Architecture (Final)

```
                    Streamlit UI (app.py)          FastAPI (main.py)
                         |                              |
                         +--------- graph/ -------------+
                                      |
            StateGraph (graph/workflow.py)
                         |
         +---------------+---------------+
         |               |               |
    supervisor      faq_agent      booking_agent --> confirmation_agent
         |               |               |                  |
         |          RAG tools       Calendar MCP        Gmail MCP
         |          (Chroma)        (Composio)          (Composio)
         |
    Memory: InMemorySaver (short-term) + InMemoryStore (long-term)
```

**Key**: Streamlit imports graph directly (deployable to Streamlit Cloud).
FastAPI is separate (for API consumers). Both use the same graph.

## Code Structure (Final on main)

```
MAS/
├── app.py                  # Streamlit UI (imports graph directly)
├── main.py                 # FastAPI endpoints (separate)
├── cli.py                  # CLI for testing
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── model.py            # Shared LLM + Embeddings
├── agents/
│   ├── __init__.py
│   ├── state.py            # AgentState TypedDict
│   ├── supervisor.py       # Supervisor routing node
│   ├── faq_agent.py        # FAQ node (RAG)
│   ├── booking_agent.py    # Booking node (Calendar MCP)
│   └── confirmation_agent.py  # Confirmation node (Gmail MCP)
├── graph/
│   ├── __init__.py
│   └── workflow.py         # Full StateGraph with all agents
├── tools/
│   ├── __init__.py
│   ├── rag_tools.py        # RAG search tool
│   └── mcp_tools.py        # Composio MCP client
├── rag/
│   ├── __init__.py
│   ├── ingest.py           # PDF -> Chroma
│   └── retriever.py        # Chroma retriever
└── data/
    ├── faq.pdf
    ├── policy.pdf
    └── CLINIC_Info.pdf
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | AWS Bedrock `ChatBedrockConverse` (Claude Haiku 4.5) |
| Embeddings | AWS Bedrock `BedrockEmbeddings` (Titan v2) |
| Agent Framework | LangGraph `StateGraph` |
| Short-term Memory | LangGraph `InMemorySaver` checkpointer |
| Long-term Memory | LangGraph `InMemoryStore` (Store API) |
| Vector Store | Chroma (persistent, local) |
| Gmail + Calendar | Composio MCP Server + `langchain-mcp-adapters` |
| Observability | LangSmith (auto-tracing) |
| API | FastAPI + uvicorn |
| UI | Streamlit (imports graph directly) |
