"""
Branch 2: FAQ Agent + Booking Agent
Run: python cli.py
"""
import asyncio
from graph.faq_graph import faq_graph
from langchain_core.messages import HumanMessage


def run_faq():
    """Interactive FAQ chat loop."""
    print("\n--- FAQ Mode ---")
    print("Ask about clinic hours, doctors, policies, etc.")
    print("Type 'back' to return to menu\n")
    messages = []
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break
        messages.append(HumanMessage(content=user_input))
        result = faq_graph.invoke({"messages": messages})
        print(f"\nBot: {result['messages'][-1].content}\n")


def run_booking():
    """Interactive booking chat loop with MCP calendar tools."""
    from graph.booking_graph import build_booking_graph
    messages = []
    print("\nConnecting to Composio MCP server...")
    try:
        
        booking_graph, client = asyncio.run(build_booking_graph())
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Composio MCP server is running.")
        return

    print("\n--- Booking Mode ---")
    print("I'll help you book an appointment.")
    print("Type 'back' to return to menu\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["back", "menu", "b"]:
            break
        messages.append(HumanMessage(content=user_input))
        result = asyncio.run(booking_graph.ainvoke({"messages": messages}))
        print(f"\nBot: {result['messages'][-1].content}\n")


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
            run_booking()
        elif choice.lower() in ["q", "quit", "exit"]:
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try 1, 2, or q.")


if __name__ == "__main__":
    main()
