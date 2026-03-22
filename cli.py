"""
Branch 5: Full Multi-Agent System with Supervisor Routing
Run: python cli.py          (FAQ only, no MCP needed)
Run: python cli.py --full   (all agents, needs Composio MCP server)
"""
import sys
import asyncio
import uuid


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
        print(f"\nBot: {result['messages'][-1].content}\n")


async def run_full_system():
    """Run the full multi-agent system with supervisor routing."""
    from graph.workflow import build_workflow

    print("Connecting to Composio MCP server...")
    try:
        graph, client = await build_workflow()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running: composio mcp start")
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

    try:
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

            result = await graph.ainvoke(
                {"messages": [("user", user_input)]}, config
            )
            response = result["messages"][-1]
            print(f"\nBot: {response.content}\n")
    finally:
        await client.close()


def main():
    if "--full" in sys.argv:
        asyncio.run(run_full_system())
    else:
        run_faq_only()


if __name__ == "__main__":
    main()
