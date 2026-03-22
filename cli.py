"""
Branch 2: FAQ Agent + Booking Agent
Run: python cli.py
"""
import asyncio
from graph.faq_graph import faq_graph


def run_faq():
    """Interactive FAQ chat loop."""
    print("\n--- FAQ Mode ---")
    print("Ask about clinic hours, doctors, policies, etc.")
    print("Type 'back' to return to menu\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break
        result = faq_graph.invoke({"messages": [("user", user_input)]})
        print(f"\nBot: {result['messages'][-1].content}\n")


async def run_booking():
    """Interactive booking chat loop with MCP calendar tools."""
    from graph.booking_graph import build_booking_graph

    print("\nConnecting to Composio MCP server...")
    try:
        booking_graph, client = await build_booking_graph()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running: composio mcp start")
        return

    print("\n--- Booking Mode ---")
    print("I'll help you book an appointment.")
    print("Type 'back' to return to menu\n")

    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["back", "menu", "b"]:
                break
            result = await booking_graph.ainvoke({"messages": [("user", user_input)]})
            print(f"\nBot: {result['messages'][-1].content}\n")
    finally:
        await client.close()


def main():
    print("=" * 50)
    print("  HealthFirst Medical Clinic")
    print("  FAQ + Appointment Booking")
    print("=" * 50)

    while True:
        print("\nWhat would you like to do?")
        print("  1. Ask a question (FAQ)")
        print("  2. Book an appointment")
        print("  q. Quit")
        choice = input("\nChoose (1/2/q): ").strip()

        if choice == "1":
            run_faq()
        elif choice == "2":
            asyncio.run(run_booking())
        elif choice.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try 1, 2, or q.")


if __name__ == "__main__":
    main()
