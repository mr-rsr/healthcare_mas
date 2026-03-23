"""
FastAPI server for HealthFirst Medical Clinic Multi-Agent System
Run: uvicorn main:app --reload
"""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage
from pydantic import BaseModel
from graph.workflow import build_workflow, build_faq_only_workflow


def _extract_text(messages) -> str:
    """Extract text from the last AI message, handling Bedrock's list content format."""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue
        content = msg.content
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            parts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
            if parts:
                return "\n".join(parts)
    return "I'm sorry, I couldn't generate a response. Please try again."


# Global graph and MCP client (set during lifespan)
graph = None
mcp_client = None
faq_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to MCP server and build graph. Shutdown: close client."""
    global graph, mcp_client, faq_graph

    # Always build FAQ-only graph (no MCP needed)
    faq_graph = build_faq_only_workflow()

    # Try to build full multi-agent graph
    try:
        graph, mcp_client = await build_workflow()
        print("Full multi-agent system ready (MCP connected)")
    except Exception as e:
        print(f"Warning: Could not connect to MCP server: {e}")
        print("Running in FAQ-only mode. Start Composio MCP server for full features.")
        graph = faq_graph

    yield

    # Cleanup
    if mcp_client:
        await mcp_client.close()


app = FastAPI(
    title="HealthFirst Medical Clinic API",
    description="Multi-agent appointment booking system",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    thread_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    user_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the multi-agent system."""
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": request.user_id,
        }
    }

    try:
        result = await graph.ainvoke(
            {"messages": [("user", request.message)]}, config
        )
        return ChatResponse(
            response=_extract_text(result["messages"]),
            thread_id=thread_id,
            user_id=request.user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream responses from the multi-agent system via SSE."""
    thread_id = request.thread_id or str(uuid.uuid4())[:8]
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": request.user_id,
        }
    }

    async def event_stream():
        try:
            async for event in graph.astream_events(
                {"messages": [("user", request.message)]},
                config,
                version="v2",
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {chunk.content}\n\n"
            yield f"data: [THREAD:{thread_id}]\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR:{str(e)}]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/ingest")
async def ingest():
    """Trigger RAG document ingestion."""
    try:
        from rag.ingest import load_pdf, split_text, create_vector_store
        import glob

        file_paths = glob.glob("data/*.pdf")
        all_docs = []
        for file_path in file_paths:
            documents = load_pdf(file_path)
            docs = split_text(documents)
            all_docs.extend(docs)

        create_vector_store(all_docs)
        return {"status": "success", "chunks": len(all_docs), "files": len(file_paths)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    has_mcp = mcp_client is not None
    return {
        "status": "healthy",
        "mode": "full" if has_mcp else "faq_only",
        "mcp_connected": has_mcp,
    }
