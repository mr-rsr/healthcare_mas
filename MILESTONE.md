# Milestone 4: Memory - Checkpointer + Store API

## What You'll Build
Add two layers of memory to the agents:
1. **Short-term (Checkpointer)**: Multi-turn conversation persistence within a thread
2. **Long-term (Store API)**: User preferences and booking history across threads

## What's New (from Milestone 3)
```
NEW  config/memory.py              # Shared checkpointer + store instances
UPD  graph/faq_graph.py            # + checkpointer for multi-turn
UPD  graph/booking_graph.py        # + checkpointer + store
UPD  cli.py                        # thread_id, user_id, memory demo
```

## Architecture
```
                    config/memory.py
                    ┌──────────────────┐
                    │  InMemorySaver   │ <-- short-term (per thread)
                    │  InMemoryStore   │ <-- long-term (per user)
                    └──────────────────┘
                           |
        +------------------+------------------+
        |                                     |
   faq_graph                           booking_graph
   (checkpointer)                 (checkpointer + store)
        |                                     |
   Multi-turn:                        Multi-turn +
   "Which one does                    Saves user prefs:
    cardiology?"                      preferred doctor,
   remembers doctors                  booking history
   from prev turn
```

## Two Memory Layers Explained

### Short-Term: InMemorySaver (Checkpointer)

Persists conversation state within a thread. Each `thread_id` is a separate conversation.

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# Same thread_id = conversation continues with full history
config = {"configurable": {"thread_id": "conv_abc123"}}

# Turn 1
graph.invoke({"messages": [("user", "What doctors do you have?")]}, config)

# Turn 2 - agent remembers the conversation
graph.invoke({"messages": [("user", "Which one does cardiology?")]}, config)
# Answer: "Dr. James Wilson" -- remembered from turn 1!
```

**Key concepts:**
- `thread_id` groups messages into a conversation
- New `thread_id` = fresh conversation
- Same `thread_id` = continues where you left off
- Messages are persisted automatically by the checkpointer

### Long-Term: InMemoryStore (Store API)

Persists user data across different conversations/threads.

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
graph = builder.compile(checkpointer=checkpointer, store=store)

# WRITE: Save user preferences
store.put(
    ("users", "user_123", "preferences"),  # namespace tuple
    "doctor_pref",                          # key
    {"doctor": "Dr. Chen", "time": "morning"}  # value
)

# READ: Retrieve user preferences
prefs = store.search(("users", "user_123", "preferences"))
if prefs:
    print(prefs[0].value)  # {"doctor": "Dr. Chen", "time": "morning"}
```

**Key concepts:**
- Namespace tuples organize data: `("users", user_id, "preferences")`
- `store.put()` writes, `store.search()` reads
- Data persists across threads (different conversations, same user)
- InMemoryStore loses data on restart (use PostgresStore for production)

### How They Work Together

| | Short-Term (Checkpointer) | Long-Term (Store) |
|--|--------------------------|-------------------|
| **What** | Conversation messages | User preferences, history |
| **Scope** | Per `thread_id` | Per `user_id` |
| **Survives** | Multiple turns in same chat | Multiple conversations |
| **Access** | Automatic via state | Explicit: `store.put()`, `store.search()` |

## Step-by-Step Code

### Step 1: Shared Memory Config (`config/memory.py`)

Centralize memory instances so all graphs share the same store:

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

checkpointer = InMemorySaver()
store = InMemoryStore()
```

### Step 2: Update FAQ Graph (`graph/faq_graph.py`)

Just add `checkpointer` to `compile()`:

```python
from config.memory import checkpointer

# ... same StateGraph setup ...

faq_graph = builder.compile(checkpointer=checkpointer)
```

Now the FAQ agent remembers multi-turn conversations when you pass `thread_id`.

### Step 3: Update Booking Graph (`graph/booking_graph.py`)

Add both `checkpointer` and `store`:

```python
from config.memory import checkpointer, store

# ... same StateGraph setup ...

return builder.compile(checkpointer=checkpointer, store=store), client
```

### Step 4: Updated CLI (`cli.py`)

Thread and user management:

```python
# Session setup
user_id = input("Enter your user ID: ") or "demo_user"
thread_id = str(uuid.uuid4())[:8]

# Pass thread_id in config for multi-turn
config = {"configurable": {"thread_id": thread_id}}
faq_graph.invoke({"messages": [("user", question)]}, config)

# New thread = fresh conversation
thread_id = str(uuid.uuid4())[:8]  # press 'n' in menu

# Store demo: view saved preferences
store.search(("users",))
```

## Running It

```bash
python cli.py
```

### Test multi-turn (FAQ):
```
Enter user ID: demo_user
Choose: 1

You: What doctors work here?
Bot: We have Dr. Sarah Chen (General), Dr. James Wilson (Cardiology)...

You: Which one does cardiology?
Bot: Dr. James Wilson specializes in Cardiology...  <-- remembers context!
```

### Test new thread:
```
Choose: n    (new thread)
Choose: 1

You: Which one does cardiology?
Bot: Let me search...  <-- fresh conversation, no prior context
```

### Test memory store:
```
Choose: 3    (view memory)
--- Memory Store Contents ---
  Namespace: ('users', 'demo_user', 'preferences')
  Key: last_booking
  Value: {'doctor': 'Dr. Chen', 'timestamp': 'a3b4c5d6'}
```

## What's Next (Milestone 5)
Wire all agents into a single StateGraph with supervisor routing.
