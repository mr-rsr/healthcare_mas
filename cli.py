"""
Branch 3: FAQ + Booking + Email Confirmation
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


def run_booking():
    """Interactive booking flow: collect details -> create event -> send confirmation."""
    from graph.booking_graph import build_booking_graph
    from graph.confirmation_graph import build_confirmation_graph

    print("\nConnecting to Composio MCP server...")
    try:
        booking_graph, booking_client = asyncio.run(build_booking_graph())
        confirmation_graph, confirmation_client = asyncio.run(build_confirmation_graph())
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running.")
        return

    print("\n--- Booking Mode ---")
    print("I'll help you book an appointment.")
    print("Type 'back' to return to menu\n")

    booking_messages = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break

        booking_messages.append(("user", user_input))
        result = booking_graph.invoke({"messages": booking_messages})
        response = result["messages"][-1]
        booking_messages = result["messages"]
        print(f"\nBot: {response.content}\n")

        # Check if booking was completed (calendar event created)
        if any(
            hasattr(m, "type") and m.type == "tool"
            and "calendar" in getattr(m, "name", "").lower()
            for m in result["messages"]
        ):
            print("Sending confirmation email...")
            summary = f"Send a confirmation email based on this booking: {response.content}"
            confirm_result = confirmation_graph.invoke(
                {"messages": [("user", summary)]}
            )
            print(f"\nBot: {confirm_result['messages'][-1].content}\n")


def run_confirmation():
    """Standalone email sending for testing."""
    from graph.confirmation_graph import build_confirmation_graph

    print("\nConnecting to Composio MCP server...")
    try:
        confirmation_graph, client = asyncio.run(build_confirmation_graph())
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running.")
        return

    print("\n--- Email Confirmation Mode ---")
    print("Test sending confirmation emails.")
    print("Type 'back' to return to menu\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break
        result = confirmation_graph.invoke({"messages": [("user", user_input)]})
        print(f"\nBot: {result['messages'][-1].content}\n")


def main():
    print("=" * 50)
    print("  HealthFirst Medical Clinic")
    print("  FAQ + Booking + Email Confirmation")
    print("=" * 50)

    while True:
        print("\nWhat would you like to do?")
        print("  1. Ask a question (FAQ)")
        print("  2. Book an appointment (+ auto email)")
        print("  3. Send confirmation email (test)")
        print("  q. Quit")
        choice = input("\nChoose (1/2/3/q): ").strip()

        if choice == "1":
            run_faq()
        elif choice == "2":
            run_booking()
        elif choice == "3":
            run_confirmation()
        elif choice.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try 1, 2, 3, or q.")


if __name__ == "__main__":
    main()
