"""
Branch 1: FAQ Agent with RAG
Run: python cli.py
"""
from graph.faq_graph import faq_graph

print("=" * 50)
print("  HealthFirst Medical Clinic")
print("  FAQ Assistant (RAG-powered)")
print("=" * 50)
print("Ask about clinic hours, doctors, policies, etc.")
print("Type 'quit' to exit\n")

while True:
    user_input = input("You: ").strip()
    if not user_input or user_input.lower() in ("quit", "exit","q"):
        print("Goodbye!")
        break

    result = faq_graph.invoke({"messages": [("user", user_input)]})
    print(f"\nBot: {result['messages'][-1].content}\n")
