"""
Demo: Checkpointer (short-term) and Store (long-term) in action.
No MCP server needed - just AWS Bedrock credentials.

Run: python demo_memory.py
"""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# ── PART 1: Store (Long-Term Memory) ────────────────────────────
print("=" * 55)
print("  PART 1: InMemoryStore (Long-Term Memory)")
print("=" * 55)

store = InMemoryStore()

# Write some user preferences
store.put(("users", "alice", "preferences"), "doctor_pref", {"doctor": "Dr. Chen", "time": "morning"})
store.put(("users", "alice", "preferences"), "insurance", {"provider": "BlueCross", "id": "BC-12345"})
store.put(("users", "bob", "preferences"), "doctor_pref", {"doctor": "Dr. Wilson", "time": "evening"})

print("\n1. Saved preferences for Alice and Bob")

# Search all users
print("\n2. store.search(('users',)) -- everything:")
for item in store.search(("users",)):
    print(f"   {item.namespace} | {item.key} -> {item.value}")

# Search just Alice
print("\n3. store.search(('users', 'alice', 'preferences')) -- just Alice:")
for item in store.search(("users", "alice", "preferences")):
    print(f"   {item.key} -> {item.value}")

# Get one specific item
print("\n4. store.get(('users', 'bob', 'preferences'), 'doctor_pref') -- Bob's doctor:")
item = store.get(("users", "bob", "preferences"), "doctor_pref")
print(f"   {item.value}")

# Overwrite
store.put(("users", "alice", "preferences"), "doctor_pref", {"doctor": "Dr. Wilson", "time": "afternoon"})
print("\n5. After overwrite -- Alice now prefers Dr. Wilson:")
item = store.get(("users", "alice", "preferences"), "doctor_pref")
print(f"   {item.value}")

# ── PART 2: Checkpointer (Short-Term Memory) ────────────────────
print("\n")
print("=" * 55)
print("  PART 2: InMemorySaver (Short-Term / Checkpointer)")
print("=" * 55)
print("\nThis uses the actual FAQ graph with your Bedrock LLM.")
print("Watch how same thread_id remembers context, new thread_id forgets.\n")

try:
    from graph.faq_graph import faq_graph

    thread_a = "thread-AAA"
    thread_b = "thread-BBB"
    config_a = {"configurable": {"thread_id": thread_a}}
    config_b = {"configurable": {"thread_id": thread_b}}

    # Turn 1 on thread A - ask about doctors
    print(f"--- Thread A ({thread_a}) - Turn 1 ---")
    q1 = "What doctors work at the clinic?"
    print(f"You: {q1}")
    r1 = faq_graph.invoke({"messages": [("user", q1)]}, config_a)
    print(f"Bot: {r1['messages'][-1].content}\n")

    # Turn 2 on thread A - vague follow-up that NEEDS context
    print(f"--- Thread A ({thread_a}) - Turn 2 (vague follow-up) ---")
    q2 = "What about the second one? What days is he available?"
    print(f"You: {q2}")
    r2 = faq_graph.invoke({"messages": [("user", q2)]}, config_a)
    print(f"Bot: {r2['messages'][-1].content}\n")

    # Same vague question on thread B - NO context, should be confused
    print(f"--- Thread B ({thread_b}) - Turn 1 (same question, NO context) ---")
    print(f"You: {q2}")
    r3 = faq_graph.invoke({"messages": [("user", q2)]}, config_b)
    print(f"Bot: {r3['messages'][-1].content}\n")

    # Show message counts to prove accumulation
    print("--- Message counts ---")
    print(f"Thread A after 2 turns: {len(r2['messages'])} messages (accumulated)")
    print(f"Thread B after 1 turn:  {len(r3['messages'])} messages (fresh)")

except Exception as e:
    print(f"Error (need AWS Bedrock credentials): {e}")
    print("Skipping Part 2. Part 1 above still demonstrates the Store.")
