"""
Memory configuration - shared checkpointer and store instances
"""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# Short-term: conversation persistence within a thread
checkpointer = InMemorySaver()

# Long-term: user preferences and booking history across threads
store = InMemoryStore()
