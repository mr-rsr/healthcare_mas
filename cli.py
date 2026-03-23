"""
Full Multi-Agent System with Supervisor Routing
Run: python cli.py          (FAQ only, no MCP needed)
Run: python cli.py --full   (all agents, needs Composio MCP)
"""
import asyncio
import sys
import uuid
from langchain_core.messages import AIMessage


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


def run_faq_only():
    """Run FAQ-only mode (no MCP server needed)."""
    from graph.workflow import build_faq_only_workflow

    graph = build_faq_only_workflow()
    thread_id = str(uuid.uuid4())[:8]
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 50)
    print("  HealthFirst Medical Clinic")
    print("  FAQ Agent (multi-turn)")
    print("=" * 50)
    print(f"Thread: {thread_id}")
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        result = graph.invoke({"messages": [("user", user_input)]}, config)
        print(f"\nBot: {_extract_text(result['messages'])}\n")


def run_full_system():
    """Run the full multi-agent system with supervisor routing."""
    from graph.workflow import build_workflow

    print("Connecting to Composio MCP server...")
    try:
        graph, client = asyncio.run(build_workflow())
    except Exception as e:
        print(f"Error: {e}")
        print("Falling back to FAQ-only mode...\n")
        run_faq_only()
        return

    user_id = input("\nEnter user ID (or Enter for 'demo_user'): ").strip() or "demo_user"
    thread_id = str(uuid.uuid4())[:8]

    print("=" * 50)
    print("  HealthFirst Medical Clinic")
    print("  Multi-Agent System")
    print("=" * 50)
    print(f"User: {user_id} | Thread: {thread_id}")
    print("Ask questions, book appointments, or say goodbye.")
    print("The supervisor routes your request automatically!")
    print("Type 'quit' to exit, 'new' for new thread\n")

    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        if user_input.lower() == "new":
            thread_id = str(uuid.uuid4())[:8]
            config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
            print(f"New thread: {thread_id}\n")
            continue

        result = asyncio.run(graph.ainvoke(
            {"messages": [("user", user_input)]}, config
        ))
        print(f"\nBot: {_extract_text(result['messages'])}\n")


def main():
    if "--full" in sys.argv:
        run_full_system()
    else:
        run_faq_only()


if __name__ == "__main__":
    main()
