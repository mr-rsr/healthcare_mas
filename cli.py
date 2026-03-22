"""
Branch 4: FAQ + Booking + Email + Memory
Run: python cli.py
"""
import asyncio
import uuid
from graph.faq_graph import faq_graph
from config.memory import store


def run_faq(thread_id: str):
    """Interactive FAQ chat loop with multi-turn memory."""
    config = {"configurable": {"thread_id": thread_id}}

    print("\n--- FAQ Mode ---")
    print(f"Thread: {thread_id}")
    print("Ask about clinic hours, doctors, policies, etc.")
    print("Multi-turn: the bot remembers your conversation!")
    print("Type 'back' to return to menu\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break
        result = faq_graph.invoke({"messages": [("user", user_input)]}, config)
        print(f"\nBot: {result['messages'][-1].content}\n")


async def run_booking(thread_id: str, user_id: str):
    """Interactive booking flow with memory."""
    from graph.booking_graph import build_booking_graph
    from graph.confirmation_graph import build_confirmation_graph

    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    print("\nConnecting to Composio MCP server...")
    try:
        booking_graph, booking_client = await build_booking_graph()
        confirmation_graph, confirmation_client = await build_confirmation_graph()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running: composio mcp start")
        return

    # Check if user has saved preferences
    prefs = store.search(("users", user_id, "preferences"))
    if prefs:
        pref_data = prefs[0].value
        print(f"\nWelcome back! I remember you prefer {pref_data.get('doctor', 'no preference')}.")

    print("\n--- Booking Mode ---")
    print(f"Thread: {thread_id} | User: {user_id}")
    print("I'll help you book an appointment. Multi-turn enabled!")
    print("Type 'back' to return to menu\n")

    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["back", "menu", "b"]:
                break

            result = await booking_graph.ainvoke(
                {"messages": [("user", user_input)]}, config
            )
            response = result["messages"][-1]
            print(f"\nBot: {response.content}\n")

            # Check if booking was completed
            if any(
                hasattr(m, "type") and m.type == "tool"
                and "calendar" in getattr(m, "name", "").lower()
                for m in result["messages"]
            ):
                # Save user preference for next time
                store.put(
                    ("users", user_id, "preferences"),
                    "last_booking",
                    {"doctor": "from conversation", "timestamp": str(uuid.uuid4())[:8]},
                )

                print("Sending confirmation email...")
                summary = f"Send a confirmation email based on this booking: {response.content}"
                confirm_result = await confirmation_graph.ainvoke(
                    {"messages": [("user", summary)]}
                )
                print(f"\nBot: {confirm_result['messages'][-1].content}\n")
    finally:
        await booking_client.close()
        await confirmation_client.close()


def show_memory_demo():
    """Show what's in the store (for demo purposes)."""
    print("\n--- Memory Store Contents ---")
    all_items = store.search(("users",))
    if not all_items:
        print("Store is empty. Book an appointment to save preferences!")
    else:
        for item in all_items:
            print(f"  Namespace: {item.namespace}")
            print(f"  Key: {item.key}")
            print(f"  Value: {item.value}")
            print()
    print("---\n")


def main():
    print("=" * 50)
    print("  HealthFirst Medical Clinic")
    print("  FAQ + Booking + Memory")
    print("=" * 50)

    # Session setup
    user_id = input("\nEnter your user ID (or press Enter for 'demo_user'): ").strip()
    if not user_id:
        user_id = "demo_user"

    thread_id = str(uuid.uuid4())[:8]
    print(f"User: {user_id} | New thread: {thread_id}")

    while True:
        print("\nWhat would you like to do?")
        print("  1. Ask a question (FAQ) - multi-turn")
        print("  2. Book an appointment (+ auto email)")
        print("  3. View memory store")
        print("  n. New conversation thread")
        print("  q. Quit")
        choice = input("\nChoose: ").strip()

        if choice == "1":
            run_faq(thread_id)
        elif choice == "2":
            asyncio.run(run_booking(thread_id, user_id))
        elif choice == "3":
            show_memory_demo()
        elif choice.lower() == "n":
            thread_id = str(uuid.uuid4())[:8]
            print(f"New thread: {thread_id}")
        elif choice.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
