# Milestone 6: FastAPI REST API

## What You'll Build
Serve the multi-agent system via FastAPI with REST endpoints for chat, streaming, health check, and document ingestion.

## What's New (from Milestone 5)
```
NEW  main.py                       # FastAPI application
UPD  cli.py                        # Kept for local testing
```

## Architecture
```
Client (curl / frontend / Streamlit)
    |
    v
FastAPI (main.py)
    |
    +-- POST /chat          --> graph.ainvoke() --> JSON response
    +-- POST /chat/stream   --> graph.astream_events() --> SSE
    +-- POST /ingest        --> RAG pipeline
    +-- GET  /health        --> status check
    |
    v
graph/workflow.py (same graph as CLI)
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message, get JSON response |
| POST | `/chat/stream` | Server-Sent Events streaming |
| POST | `/ingest` | Trigger RAG document ingestion |
| GET | `/health` | Health check (mode + MCP status) |

## Key Concepts

### 1. Lifespan (Startup/Shutdown)

FastAPI lifespan manages MCP client connection:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph, mcp_client

    # Startup: build graph, connect to MCP
    try:
        graph, mcp_client = await build_workflow()
    except:
        graph = build_faq_only_workflow()  # fallback

    yield

    # Shutdown: close MCP client
    if mcp_client:
        await mcp_client.close()
```

**Key concepts:**
- Lifespan runs once at startup and shutdown
- MCP client is shared across all requests
- Graceful fallback to FAQ-only if MCP is unavailable

### 2. Chat Endpoint

```python
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    thread_id: str | None = None    # auto-generated if not provided

@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {
        "thread_id": thread_id,
        "user_id": request.user_id,
    }}
    result = await graph.ainvoke(
        {"messages": [("user", request.message)]}, config
    )
    return {"response": result["messages"][-1].content, ...}
```

**Key concepts:**
- `thread_id` enables multi-turn conversations (same thread = same conversation)
- `user_id` enables long-term memory (Store API)
- Auto-generates thread_id if not provided

### 3. Streaming Endpoint (SSE)

```python
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_stream():
        async for event in graph.astream_events(input, config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {chunk.content}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**Key concepts:**
- `astream_events` streams LangGraph events in real-time
- Filter for `on_chat_model_stream` to get LLM output tokens
- SSE format: `data: <content>\n\n`
- Thread ID sent at end: `data: [THREAD:abc123]\n\n`

## Running It

### Start the server:
```bash
# FAQ-only mode (no MCP needed):
uvicorn main:app --reload

# Full mode (start Composio MCP first):
composio mcp start   # Terminal 1
uvicorn main:app --reload   # Terminal 2
```

### Test with curl:

#### Health check:
```bash
curl http://localhost:8000/health
# {"status":"healthy","mode":"faq_only","mcp_connected":false}
```

#### Chat:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your hours?", "user_id": "demo"}'
# {"response":"Our hours are Mon-Fri 9-5...","thread_id":"a1b2c3d4","user_id":"demo"}
```

#### Multi-turn (same thread):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Which one does cardiology?", "user_id": "demo", "thread_id": "a1b2c3d4"}'
```

#### Streaming:
```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What services do you offer?", "user_id": "demo"}'
# data: We offer
# data:  a range
# data:  of services...
# data: [DONE]
```

#### Ingest documents:
```bash
curl -X POST http://localhost:8000/ingest
# {"status":"success","chunks":140,"files":3}
```

### Interactive docs:
Open http://localhost:8000/docs for Swagger UI.

## What's Next (Main Branch)
Add Streamlit UI that imports the graph directly (no API calls).
