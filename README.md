# HealthFirst Medical Clinic - Multi-Agent System

A multi-agent appointment booking system built with **LangGraph**, **AWS Bedrock**, **Composio MCP** (Gmail + Google Calendar), **RAG** (Chroma), and **LangSmith** observability.

## Quick Start

### 1. Setup
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # Fill in AWS credentials
```

### 2. Ingest documents
```bash
python -m rag.ingest
```

### 3. Run (choose one)

**Streamlit UI** (recommended):
```bash
streamlit run app.py
```

**CLI**:
```bash
python cli.py              # FAQ only
python cli.py --full       # All agents (needs Composio MCP)
```

**FastAPI**:
```bash
uvicorn main:app --reload
# Open http://localhost:8000/docs
```

## Architecture

```
Streamlit (app.py)           FastAPI (main.py)            CLI (cli.py)
     |                            |                           |
     +------------- graph/workflow.py ------------------------+
                         |
         [supervisor] --> routes to:
              |
    +---------+---------+
    |         |         |
 faq_agent  booking   confirmation
  (RAG)    (Calendar)   (Gmail)
    |         |           |
  Chroma   Composio    Composio
            MCP         MCP
```

## Training Milestones (Branches)

Each branch is a working milestone. Check out any branch and read its `MILESTONE.md`.

| Branch | What's Added |
|--------|-------------|
| `branch-1-rag` | LangGraph StateGraph + RAG tool (FAQ agent) |
| `branch-2-calendar` | + Google Calendar booking via Composio MCP |
| `branch-3-gmail` | + Gmail confirmation via Composio MCP |
| `branch-4-memory` | + Checkpointer (multi-turn) + Store API (user prefs) |
| `branch-5-multi-agent` | Full StateGraph with supervisor routing |
| `branch-6-fastapi` | + FastAPI REST endpoints |
| `main` | + Streamlit UI (this branch) |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | AWS Bedrock - Claude Haiku 4.5 |
| Embeddings | AWS Bedrock - Amazon Titan v2 |
| Agent Framework | LangGraph StateGraph |
| Memory | InMemorySaver + InMemoryStore |
| Vector Store | Chroma (local) |
| Gmail + Calendar | Composio MCP + langchain-mcp-adapters |
| Observability | LangSmith |
| API | FastAPI |
| UI | Streamlit |

## Composio Setup (for booking + email)

```bash
pip install composio-core
composio login
composio add gmail
composio add googlecalendar
composio mcp start
```

## Project Structure

```
MAS/
├── app.py                  # Streamlit UI
├── main.py                 # FastAPI server
├── cli.py                  # CLI testing
├── config/
│   ├── model.py            # LLM + Embeddings
│   └── memory.py           # Checkpointer + Store
├── agents/
│   ├── state.py            # AgentState
│   ├── supervisor.py       # Router
│   ├── faq_agent.py        # FAQ (RAG)
│   ├── booking_agent.py    # Booking (Calendar)
│   └── confirmation_agent.py  # Email (Gmail)
├── graph/
│   ├── faq_graph.py        # FAQ-only graph
│   ├── booking_graph.py    # Booking graph
│   ├── confirmation_graph.py  # Confirmation graph
│   └── workflow.py         # Full multi-agent graph
├── tools/
│   ├── rag_tools.py        # RAG search tool
│   └── mcp_tools.py        # Composio MCP client
├── rag/
│   ├── ingest.py           # PDF ingestion
│   └── retriever.py        # Chroma retriever
└── data/
    ├── faq.pdf
    ├── policy.pdf
    └── CLINIC_Info.pdf
```
